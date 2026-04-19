from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List
from urllib import request, error


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_config(config_path: Path) -> Dict[str, Any]:
    return load_json(config_path)


def collect_image_paths(run_request_payload: Dict[str, Any], max_images: int) -> List[str]:
    image_sequence = run_request_payload.get("inputs", {}).get("image_sequence", [])
    return image_sequence[:max_images]


def build_predict_payload(
    run_request_payload: Dict[str, Any],
    config: Dict[str, Any],
) -> Dict[str, Any]:
    max_images = int(config.get("max_images", 1))
    image_paths = collect_image_paths(run_request_payload, max_images=max_images)

    if not image_paths:
        raise RuntimeError("No image paths available in run request for Cosmos Predict.")

    return {
        "model": config.get("model_name", "cosmos-predict1-5b"),
        "input": {
            "run_id": run_request_payload.get("run_id"),
            "scenario_id": run_request_payload.get("scenario_id"),
            "prompt_text": config.get("prompt_text", ""),
            "seed_image_paths": image_paths,
            "scene_context": run_request_payload.get("inputs", {}).get("scene_context", {}),
            "task_type": "future_world_generation_for_perception_evaluation",
            "expected_output": {
                "type": "video",
                "format": "mp4"
            }
        }
    }


def call_predict_endpoint(
    run_request_payload: Dict[str, Any],
    config: Dict[str, Any],
) -> Dict[str, Any]:
    endpoint_url = config.get("endpoint_url", "").strip()
    if not endpoint_url or "YOUR_COSMOS_PREDICT_ENDPOINT_HERE" in endpoint_url:
        raise RuntimeError(
            "Predict endpoint_url is not configured in configs/cosmos_predict_config.json"
        )

    api_key_env_var = config.get("api_key_env_var", "COSMOS_API_KEY")
    api_key = os.environ.get(api_key_env_var)
    if not api_key:
        raise RuntimeError(
            f"Predict endpoint requires environment variable {api_key_env_var}"
        )

    timeout_seconds = int(config.get("timeout_seconds", 120))
    payload = build_predict_payload(run_request_payload, config)
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
        raise RuntimeError(f"Predict endpoint HTTP error {e.code}: {body}") from e
    except error.URLError as e:
        raise RuntimeError(f"Predict endpoint connection error: {e}") from e


def normalize_predict_output(raw_output: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a hosted Predict response into a stable inspection format.

    We do NOT assume one exact response shape yet.
    We preserve the raw structure but try to extract likely artifact fields.
    """
    artifact_url = None
    artifact_type = None

    # Common possible shapes
    if isinstance(raw_output.get("output"), dict):
        output = raw_output["output"]
        artifact_url = output.get("artifact_url") or output.get("video_url") or output.get("url")
        artifact_type = output.get("artifact_type") or output.get("type") or "video"
    elif isinstance(raw_output.get("result"), dict):
        result = raw_output["result"]
        artifact_url = result.get("artifact_url") or result.get("video_url") or result.get("url")
        artifact_type = result.get("artifact_type") or result.get("type") or "video"
    else:
        artifact_url = raw_output.get("artifact_url") or raw_output.get("video_url") or raw_output.get("url")
        artifact_type = raw_output.get("artifact_type") or raw_output.get("type") or "video"

    return {
        "artifact_found": artifact_url is not None,
        "artifact_type": artifact_type,
        "artifact_url": artifact_url,
        "raw_output": raw_output,
    }