from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from cosmos_reason_client import load_config, run_mock_reasoning, run_real_reasoning
from schemas import validate_cosmos_response, validate_decision


DEFAULT_CONFIG_PATH = "configs/cosmos_reason_config.json"


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(payload: Dict[str, Any], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def build_decision(cosmos_response: Dict[str, Any]) -> Dict[str, Any]:
    analysis = cosmos_response["analysis"]
    recommendation = cosmos_response["recommendation"]

    confidence = analysis["visibility_confidence"]
    action = recommendation["action"]

    approved_for_training = action == "retain_for_training" and confidence >= 0.80

    if approved_for_training:
        reason_code = "VISIBLE_OBSTACLE_HIGH_CONFIDENCE"
        next_step = "include_in_training_set"
    elif action == "review_manually":
        reason_code = "REQUIRES_MANUAL_REVIEW"
        next_step = "send_to_review_queue"
    else:
        reason_code = "LOW_CONFIDENCE_OR_REJECTED"
        next_step = "exclude_from_training_set"

    return {
        "run_id": cosmos_response["run_id"],
        "decision_type": "dataset_curation",
        "approved_for_training": approved_for_training,
        "reason_code": reason_code,
        "next_step": next_step
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a Cosmos response and downstream decision for a run."
    )
    parser.add_argument(
        "--run-dir",
        required=True,
        help="Path to an existing run directory, e.g. runs/run_0004"
    )
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG_PATH,
        help="Path to Cosmos Reason config JSON"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_dir = Path(args.run_dir)

    request_path = run_dir / "requests" / "cosmos_request.json"
    response_dir = run_dir / "responses"
    decision_dir = run_dir / "decisions"

    response_dir.mkdir(parents=True, exist_ok=True)
    decision_dir.mkdir(parents=True, exist_ok=True)

    request_payload = load_json(request_path)
    config = load_config(Path(args.config))
    mode = config.get("mode", "mock").strip().lower()

    if mode == "mock":
        cosmos_response = run_mock_reasoning(request_payload, config)
    elif mode == "real_cosmos":
        cosmos_response = run_real_reasoning(request_payload, config)
    else:
        raise ValueError(
            f"Unsupported mode in {args.config}: {mode}. Expected 'mock' or 'real_cosmos'."
        )

    validate_cosmos_response(cosmos_response)

    decision_payload = build_decision(cosmos_response)
    validate_decision(decision_payload)

    response_path = response_dir / "cosmos_response.json"
    decision_path = decision_dir / "decision.json"

    write_json(cosmos_response, response_path)
    write_json(decision_payload, decision_path)

    print(f"Mode used: {mode}")
    print(f"Cosmos response written to: {response_path}")
    print(f"Decision written to: {decision_path}")


if __name__ == "__main__":
    main()