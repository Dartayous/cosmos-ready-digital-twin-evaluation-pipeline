from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from cosmos_reason_client import load_json
from cosmos_predict_client import (
    load_config,
    build_predict_payload,
    call_predict_endpoint,
    normalize_predict_output,
)

DEFAULT_CONFIG_PATH = "configs/cosmos_predict_config.json"


def write_json(payload: Dict[str, Any], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Test a real Cosmos Predict endpoint using an existing run request."
    )
    parser.add_argument(
        "--run-dir",
        required=True,
        help="Path to an existing run directory, e.g. runs/run_0004",
    )
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG_PATH,
        help="Path to Cosmos Predict config JSON",
    )
    parser.add_argument(
        "--save-artifacts",
        action="store_true",
        help="Save raw and normalized Predict responses into the run folder",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_dir = Path(args.run_dir)
    config_path = Path(args.config)

    request_path = run_dir / "requests" / "cosmos_request.json"
    run_request_payload = load_json(request_path)
    config = load_config(config_path)

    payload = build_predict_payload(run_request_payload, config)

    print("=== REAL COSMOS PREDICT REQUEST PAYLOAD ===")
    print(json.dumps(payload, indent=2))

    raw_output = call_predict_endpoint(run_request_payload, config)

    print("\n=== RAW PREDICT ENDPOINT RESPONSE ===")
    print(json.dumps(raw_output, indent=2))

    normalized = normalize_predict_output(raw_output)

    print("\n=== NORMALIZED PREDICT RESPONSE ===")
    print(json.dumps(normalized, indent=2))

    if args.save_artifacts:
        predict_dir = run_dir / "predict"
        predict_dir.mkdir(parents=True, exist_ok=True)

        raw_path = predict_dir / "predict_raw_response.json"
        normalized_path = predict_dir / "predict_normalized_response.json"

        write_json(raw_output, raw_path)
        write_json(normalized, normalized_path)

        print(f"\nSaved raw response to: {raw_path}")
        print(f"Saved normalized response to: {normalized_path}")


if __name__ == "__main__":
    main()