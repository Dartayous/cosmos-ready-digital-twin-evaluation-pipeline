from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List
from urllib import request, error

from schemas import validate_cosmos_response


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_config(config_path: Path) -> Dict[str, Any]:
    return load_json(config_path)


def collect_image_paths(request_payload: Dict[str, Any], max_images: int) -> List[str]:
    image_sequence = request_payload.get("inputs", {}).get("image_sequence", [])
    return image_sequence[:max_images]

def summarize_telemetry_from_request(request_payload: Dict[str, Any]) -> Dict[str, Any]:
    telemetry_rel = request_payload.get("inputs", {}).get("telemetry_file", "")
    run_dir = Path("runs") / request_payload["run_id"]
    telemetry_path = run_dir / telemetry_rel

    telemetry = load_json(telemetry_path)
    frames = telemetry.get("frames", [])

    frame_count = len(frames)
    camera_ids = []
    obstacle_flags = []
    hit_counts = []
    min_distances = []

    for frame in frames:
        camera_id = frame.get("camera_id")
        if camera_id and camera_id not in camera_ids:
            camera_ids.append(camera_id)

        lidar = frame.get("lidar_summary", {})
        if "obstacle_detected" in lidar:
            obstacle_flags.append(bool(lidar["obstacle_detected"]))
        if "beam_hit_count" in lidar:
            hit_counts.append(lidar["beam_hit_count"])
        if "min_distance_m" in lidar:
            min_distances.append(lidar["min_distance_m"])

    summary = {
        "frame_count": frame_count,
        "camera_ids": camera_ids,
        "obstacle_detected_all_frames": all(obstacle_flags) if obstacle_flags else None,
        "average_beam_hit_count": round(sum(hit_counts) / len(hit_counts), 2) if hit_counts else None,
        "average_min_distance_m": round(sum(min_distances) / len(min_distances), 3) if min_distances else None,
    }

    return summary


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def compute_telemetry_adjustment_from_request(request_payload: Dict[str, Any]) -> tuple[float, list[str], str]:
    telemetry_rel = request_payload["inputs"]["telemetry_file"]
    run_dir = Path("runs") / request_payload["run_id"]
    telemetry_path = run_dir / telemetry_rel

    telemetry = load_json(telemetry_path)
    frames = telemetry.get("frames", [])

    if not frames:
        return -0.20, ["no telemetry frames found"], "high"

    hit_counts = []
    min_distances = []
    obstacle_flags = []

    for frame in frames:
        lidar = frame.get("lidar_summary", {})
        if "beam_hit_count" in lidar:
            hit_counts.append(lidar["beam_hit_count"])
        if "min_distance_m" in lidar:
            min_distances.append(lidar["min_distance_m"])
        if "obstacle_detected" in lidar:
            obstacle_flags.append(bool(lidar["obstacle_detected"]))

    factors = []
    adjustment = 0.0

    if obstacle_flags and not all(obstacle_flags):
        return -0.35, ["obstacle not detected in all frames"], "high"

    if hit_counts:
        avg_hits = sum(hit_counts) / len(hit_counts)
        factors.append(f"average beam_hit_count = {avg_hits:.2f}")

        if avg_hits >= 16:
            adjustment += 0.08
        elif avg_hits >= 10:
            adjustment += 0.00
        elif avg_hits >= 5:
            adjustment -= 0.10
        else:
            adjustment -= 0.20
    else:
        factors.append("beam_hit_count unavailable")
        adjustment -= 0.05

    if min_distances:
        avg_min_dist = sum(min_distances) / len(min_distances)
        factors.append(f"average min_distance_m = {avg_min_dist:.2f}")

        if avg_min_dist < 0.8:
            adjustment -= 0.08
        elif avg_min_dist < 1.5:
            adjustment += 0.03
        else:
            adjustment -= 0.03
    else:
        factors.append("min_distance_m unavailable")
        adjustment -= 0.03

    if obstacle_flags:
        factors.append("obstacle_detected true in all frames")

    risk_hint = "medium"
    if adjustment >= 0.05:
        risk_hint = "low"
    elif adjustment <= -0.15:
        risk_hint = "high"

    return adjustment, factors, risk_hint


def run_mock_reasoning(request_payload: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    scenario_id = request_payload["scenario_id"]

    if scenario_id == "baseline_clear":
        base_confidence = 0.82
        base_risk = "low"
        dataset_label = "good_training_example"
        action = "retain_for_training"
        factors = [
            "clear baseline scenario",
            "obstacle expected to be visible",
        ]
    elif scenario_id == "dim_lighting":
        base_confidence = 0.60
        base_risk = "medium"
        dataset_label = "borderline_example"
        action = "review_manually"
        factors = [
            "reduced scene brightness",
            "lower visual contrast",
        ]
    elif scenario_id == "partial_occlusion":
        base_confidence = 0.50
        base_risk = "high"
        dataset_label = "borderline_example"
        action = "review_manually"
        factors = [
            "partial obstacle occlusion",
            "reduced visible contour",
        ]
    elif scenario_id == "blur":
        base_confidence = 0.50
        base_risk = "medium"
        dataset_label = "borderline_example"
        action = "review_manually"
        factors = [
            "image blur degrades edge detail",
            "visual certainty reduced",
        ]
    elif scenario_id == "noise":
        base_confidence = 0.50
        base_risk = "medium"
        dataset_label = "borderline_example"
        action = "review_manually"
        factors = [
            "image noise reduces clarity",
            "signal quality degraded",
        ]
    else:
        base_confidence = 0.50
        base_risk = "medium"
        dataset_label = "borderline_example"
        action = "review_manually"
        factors = [
            "unknown scenario",
            "default fallback response",
        ]

    telemetry_adjustment, telemetry_factors, telemetry_risk_hint = compute_telemetry_adjustment_from_request(
        request_payload
    )

    final_confidence = clamp(base_confidence + telemetry_adjustment)

    if final_confidence >= 0.80:
        risk_level = "low"
        dataset_label = "good_training_example"
        action = "retain_for_training"
    elif final_confidence >= 0.45:
        risk_level = telemetry_risk_hint if telemetry_risk_hint != "low" else base_risk
        dataset_label = "borderline_example"
        action = "review_manually"
    else:
        risk_level = "high"
        dataset_label = "reject_example"
        action = "exclude_from_training"

    cosmos_response = {
        "run_id": request_payload["run_id"],
        "scenario_id": scenario_id,
        "model_name": "cosmos_reason_or_mock_contract_v03",
        "analysis": {
            "obstacle_detectable": final_confidence >= 0.30,
            "visibility_confidence": round(final_confidence, 2),
            "primary_factors": factors + telemetry_factors,
            "risk_level": risk_level
        },
        "recommendation": {
            "dataset_label": dataset_label,
            "action": action
        }
    }

    validate_cosmos_response(cosmos_response)
    return cosmos_response


def build_real_cosmos_payload(request_payload: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    max_images = int(config.get("max_images", 3))
    image_paths = collect_image_paths(request_payload, max_images=max_images)
    telemetry_summary = summarize_telemetry_from_request(request_payload)

    return {
        "model": config.get("model_name", "cosmos-reason2"),
        "input": {
            "run_id": request_payload.get("run_id"),
            "scenario_id": request_payload.get("scenario_id"),
            "task_type": request_payload.get("task_type", "obstacle_visibility_evaluation"),
            "scene_context": request_payload.get("inputs", {}).get("scene_context", {}),
            "image_sequence": image_paths,
            "telemetry_summary": telemetry_summary,
            "questions": request_payload.get("questions", []),
            "requested_output_schema": {
                "analysis": {
                    "obstacle_detectable": "bool",
                    "visibility_confidence": "float_0_to_1",
                    "primary_factors": "list[str]",
                    "risk_level": "low|medium|high"
                },
                "recommendation": {
                    "dataset_label": "good_training_example|borderline_example|reject_example",
                    "action": "retain_for_training|review_manually|exclude_from_training"
                }
            }
        }
    }


def call_real_cosmos_endpoint(request_payload: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Real-mode stub:
    - builds an HTTP request
    - attempts endpoint call
    - expects JSON back
    - normalizes response later

    This is intentionally conservative so the pipeline shape is correct even
    before a real endpoint is configured.
    """
    endpoint_url = config.get("endpoint_url", "").strip()
    if not endpoint_url or "YOUR_COSMOS_REASON_ENDPOINT_HERE" in endpoint_url:
        raise RuntimeError(
            "real_cosmos mode selected, but endpoint_url is not configured in configs/cosmos_reason_config.json"
        )

    api_key_env_var = config.get("api_key_env_var", "COSMOS_API_KEY")
    api_key = os.environ.get(api_key_env_var)
    if not api_key:
        raise RuntimeError(
            f"real_cosmos mode selected, but environment variable {api_key_env_var} is not set"
        )

    timeout_seconds = int(config.get("timeout_seconds", 60))
    payload = build_real_cosmos_payload(request_payload, config)
    payload_bytes = json.dumps(payload).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    req = request.Request(
        endpoint_url,
        data=payload_bytes,
        headers=headers,
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=timeout_seconds) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Cosmos endpoint HTTP error {e.code}: {body}") from e
    except error.URLError as e:
        raise RuntimeError(f"Cosmos endpoint connection error: {e}") from e


def normalize_real_cosmos_output(
    raw_output: Dict[str, Any],
    request_payload: Dict[str, Any],
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Normalize a real Cosmos response into the project's stable schema.

    Supported patterns:
    1. raw_output["analysis"] / raw_output["recommendation"]
    2. raw_output["output"]["analysis"] / raw_output["output"]["recommendation"]
    3. raw_output["result"]["analysis"] / raw_output["result"]["recommendation"]
    4. top-level fallback fields such as:
       - obstacle_detectable
       - visibility_confidence
       - primary_factors
       - risk_level
       - dataset_label
       - action
    5. message/content-style fallbacks if the endpoint returns a text response
    """

    analysis = {}
    recommendation = {}

    # Pattern 1: top-level analysis/recommendation
    if isinstance(raw_output.get("analysis"), dict):
        analysis = raw_output.get("analysis", {})
    if isinstance(raw_output.get("recommendation"), dict):
        recommendation = raw_output.get("recommendation", {})

    # Pattern 2: nested output
    if not analysis and isinstance(raw_output.get("output"), dict):
        output_block = raw_output["output"]
        if isinstance(output_block.get("analysis"), dict):
            analysis = output_block.get("analysis", {})
        if isinstance(output_block.get("recommendation"), dict):
            recommendation = output_block.get("recommendation", {})

    # Pattern 3: nested result
    if not analysis and isinstance(raw_output.get("result"), dict):
        result_block = raw_output["result"]
        if isinstance(result_block.get("analysis"), dict):
            analysis = result_block.get("analysis", {})
        if isinstance(result_block.get("recommendation"), dict):
            recommendation = result_block.get("recommendation", {})

    # Pattern 4: top-level fallback scalar fields
    if not analysis:
        analysis = {
            "obstacle_detectable": raw_output.get("obstacle_detectable"),
            "visibility_confidence": raw_output.get("visibility_confidence"),
            "primary_factors": raw_output.get("primary_factors"),
            "risk_level": raw_output.get("risk_level"),
        }

    if not recommendation:
        recommendation = {
            "dataset_label": raw_output.get("dataset_label"),
            "action": raw_output.get("action"),
        }

    # Pattern 5: message/content fallback
    if not analysis.get("primary_factors"):
        message_text = None

        if isinstance(raw_output.get("message"), str):
            message_text = raw_output["message"]
        elif isinstance(raw_output.get("content"), str):
            message_text = raw_output["content"]
        elif isinstance(raw_output.get("output"), dict) and isinstance(raw_output["output"].get("content"), str):
            message_text = raw_output["output"]["content"]

        if message_text:
            analysis["primary_factors"] = [message_text[:300]]

    confidence = analysis.get("visibility_confidence", 0.5)
    if not isinstance(confidence, (int, float)):
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.5

    confidence = clamp(float(confidence))

    obstacle_detectable = analysis.get("obstacle_detectable")
    if not isinstance(obstacle_detectable, bool):
        obstacle_detectable = confidence >= 0.30

    risk_level = analysis.get("risk_level", "medium")
    if risk_level not in {"low", "medium", "high"}:
        risk_level = "medium"

    primary_factors = analysis.get("primary_factors")
    if not isinstance(primary_factors, list) or not primary_factors:
        primary_factors = ["real_cosmos output did not provide structured primary_factors"]

    dataset_label = recommendation.get("dataset_label", "borderline_example")
    if dataset_label not in {
        "good_training_example",
        "borderline_example",
        "reject_example",
    }:
        dataset_label = "borderline_example"

    action = recommendation.get("action", "review_manually")
    if action not in {
        "retain_for_training",
        "review_manually",
        "exclude_from_training",
    }:
        action = "review_manually"

    cosmos_response = {
        "run_id": request_payload["run_id"],
        "scenario_id": request_payload["scenario_id"],
        "model_name": config.get("model_name", "cosmos-reason2"),
        "analysis": {
            "obstacle_detectable": obstacle_detectable,
            "visibility_confidence": round(confidence, 2),
            "primary_factors": primary_factors,
            "risk_level": risk_level,
        },
        "recommendation": {
            "dataset_label": dataset_label,
            "action": action,
        },
    }

    validate_cosmos_response(cosmos_response)
    return cosmos_response


def run_real_reasoning(request_payload: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    raw_output = call_real_cosmos_endpoint(request_payload, config)
    return normalize_real_cosmos_output(raw_output, request_payload, config)
