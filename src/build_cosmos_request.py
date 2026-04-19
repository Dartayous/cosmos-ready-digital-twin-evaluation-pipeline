from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from schemas import validate_cosmos_request


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(payload: Dict[str, Any], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def write_text(content: str, path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        f.write(content)


def collect_frame_paths(telemetry: Dict[str, Any]) -> List[str]:
    frames = telemetry.get("frames", [])
    return [frame["image_path"] for frame in frames if "image_path" in frame]

def build_request_payload(
    manifest: Dict[str, Any],
    telemetry: Dict[str, Any],
) -> Dict[str, Any]:
    frame_paths = collect_frame_paths(telemetry)

    return {
        "run_id": manifest["run_id"],
        "scenario_id": manifest["scenario_id"],
        "task_type": "obstacle_visibility_evaluation",
        "inputs": {
            "image_sequence": frame_paths,
            "telemetry_file": str(Path("telemetry") / "telemetry.json"),
            "scene_context": {
                "environment": "warehouse",
                "robot": "nova_carter_drive_to_goal",
                "obstacle_label": "box",
                "sensor_baseline": "lidar_detects_obstacle"
            }
        },
        "questions": [
            "Is the box obstacle visually detectable in this sequence?",
            "How confident are you that the obstacle remains visible enough for perception or training use?",
            "What environmental factors most affect visibility in this run?",
            "Would you retain this run for obstacle avoidance or perception training?"
        ],
        "required_output_schema": "cosmos_response_v01"
    }


def build_prompt_markdown(
    manifest: Dict[str, Any],
    telemetry: Dict[str, Any],
    request_payload: Dict[str, Any],
) -> str:
    frame_paths = collect_frame_paths(telemetry)
    frame_lines = "\n".join(f"- {frame}" for frame in frame_paths)

    return f"""# Cosmos Reasoning Request

## Run Info
- Run ID: {manifest["run_id"]}
- Scenario ID: {manifest["scenario_id"]}
- USD File: {manifest["usd_file"]}
- Capture Mode: {manifest["capture_mode"]}

## Scene Context
- Environment: warehouse
- Robot: nova_carter_drive_to_goal
- Obstacle: box
- Baseline: LiDAR indicates obstacle is present in the scene

## Image Sequence
{frame_lines}

## Evaluation Questions
1. Is the box obstacle visually detectable in this sequence?
2. How confident are you that the obstacle remains visible enough for perception or training use?
3. What environmental factors most affect visibility in this run?
4. Would you retain this run for obstacle avoidance or perception training?

## Required JSON Output
{{
  "run_id": "{manifest["run_id"]}",
  "scenario_id": "{manifest["scenario_id"]}",
  "model_name": "cosmos_reason_or_mock_contract",
  "analysis": {{
    "obstacle_detectable": true,
    "visibility_confidence": 0.0,
    "primary_factors": ["factor_1", "factor_2"],
    "risk_level": "low|medium|high"
  }},
  "recommendation": {{
    "dataset_label": "good_training_example|borderline_example|reject_example",
    "action": "retain_for_training|review_manually|exclude_from_training"
  }}
}}
"""

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a Cosmos-style request package from a run bundle."
    )
    parser.add_argument(
        "--run-dir",
        required=True,
        help="Path to an existing run directory, e.g. runs/run_0001"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_dir = Path(args.run_dir)

    manifest_path = run_dir / "manifests" / "run_manifest.json"
    telemetry_path = run_dir / "telemetry" / "telemetry.json"
    request_dir = run_dir / "requests"
    reports_dir = run_dir / "reports"

    request_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    manifest = load_json(manifest_path)
    telemetry = load_json(telemetry_path)

    request_payload = build_request_payload(manifest, telemetry)
    validate_cosmos_request(request_payload)

    request_json_path = request_dir / "cosmos_request.json"
    prompt_md_path = request_dir / "cosmos_prompt.md"
    report_md_path = reports_dir / "request_summary.md"

    write_json(request_payload, request_json_path)

    prompt_md = build_prompt_markdown(manifest, telemetry, request_payload)
    write_text(prompt_md, prompt_md_path)
    write_text(prompt_md, report_md_path)

    print(f"Built Cosmos request package for: {run_dir}")
    print(f"Request JSON: {request_json_path}")
    print(f"Prompt Markdown: {prompt_md_path}")
    print(f"Report Summary: {report_md_path}")


if __name__ == "__main__":
    main()