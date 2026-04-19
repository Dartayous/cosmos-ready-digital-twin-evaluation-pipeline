from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from cosmos_reason_client import (
    load_json,
    load_config,
    build_real_cosmos_payload,
    call_real_cosmos_endpoint,
    normalize_real_cosmos_output,
)

DEFAULT_CONFIG_PATH = "configs/cosmos_reason_config.json"


def write_json(payload: Dict[str, Any], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Test a real Cosmos Reason endpoint without touching the main pipeline."
    )
    parser.add_argument(
        "--run-dir",
        required=True,
        help="Path to an existing run directory, e.g. runs/run_0004",
    )
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG_PATH,
        help="Path to Cosmos Reason config JSON",
    )
    parser.add_argument(
        "--save-artifacts",
        action="store_true",
        help="Save raw and normalized endpoint responses into the run folder",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_dir = Path(args.run_dir)
    config_path = Path(args.config)

    request_path = run_dir / "requests" / "cosmos_request.json"
    request_payload = load_json(request_path)
    config = load_config(config_path)

    mode = config.get("mode", "mock").strip().lower()
    if mode != "real_cosmos":
        raise RuntimeError(
            f"test_cosmos_endpoint.py requires mode='real_cosmos' in {config_path}, but found mode='{mode}'"
        )

    payload = build_real_cosmos_payload(request_payload, config)

    print("=== REAL COSMOS REQUEST PAYLOAD ===")
    print(json.dumps(payload, indent=2))

    raw_output = call_real_cosmos_endpoint(request_payload, config)

    print("\n=== RAW ENDPOINT RESPONSE ===")
    print(json.dumps(raw_output, indent=2))

    normalized_output = normalize_real_cosmos_output(raw_output, request_payload, config)

    print("\n=== NORMALIZED COSMOS RESPONSE ===")
    print(json.dumps(normalized_output, indent=2))

    if args.save_artifacts:
        debug_dir = run_dir / "responses"
        debug_dir.mkdir(parents=True, exist_ok=True)

        raw_path = debug_dir / "cosmos_raw_response.json"
        normalized_path = debug_dir / "cosmos_normalized_response.json"

        write_json(raw_output, raw_path)
        write_json(normalized_output, normalized_path)

        print(f"\nSaved raw response to: {raw_path}")
        print(f"Saved normalized response to: {normalized_path}")


if __name__ == "__main__":
    main()