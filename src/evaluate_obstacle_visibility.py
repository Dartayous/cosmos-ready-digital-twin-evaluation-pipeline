from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_text(content: str, path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        f.write(content)


def build_evaluation_report(
    manifest: Dict[str, Any],
    telemetry: Dict[str, Any],
    cosmos_response: Dict[str, Any],
    decision: Dict[str, Any],
) -> str:
    frame_count = len(telemetry.get("frames", []))
    analysis = cosmos_response["analysis"]
    recommendation = cosmos_response["recommendation"]

    primary_factors_lines = "\n".join(
        f"- {factor}" for factor in analysis.get("primary_factors", [])
    )

    return f"""# Obstacle Visibility Evaluation Report

## Run Summary
- Run ID: {manifest["run_id"]}
- Scenario ID: {manifest["scenario_id"]}
- USD File: {manifest["usd_file"]}
- Capture Mode: {manifest["capture_mode"]}
- Frame Count: {frame_count}

## Baseline Perception Context
- LiDAR baseline status: obstacle_detected = true
- Purpose: compare structured simulation evidence against Cosmos-style reasoning output

## Cosmos Analysis
- Obstacle Detectable: {analysis["obstacle_detectable"]}
- Visibility Confidence: {analysis["visibility_confidence"]}
- Risk Level: {analysis["risk_level"]}

## Primary Factors
{primary_factors_lines}

## Recommendation
- Dataset Label: {recommendation["dataset_label"]}
- Action: {recommendation["action"]}

## Downstream Decision
- Approved For Training: {decision["approved_for_training"]}
- Reason Code: {decision["reason_code"]}
- Next Step: {decision["next_step"]}

## Interpretation
This run demonstrates a Cosmos-style perception evaluation workflow:
simulation output was captured, structured into a run bundle, converted into a reasoning request,
answered through a mock Cosmos contract, and normalized into a machine-readable training decision.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a human-readable obstacle visibility evaluation report."
    )
    parser.add_argument(
        "--run-dir",
        required=True,
        help="Path to an existing run directory, e.g. runs/run_0002"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_dir = Path(args.run_dir)

    manifest_path = run_dir / "manifests" / "run_manifest.json"
    telemetry_path = run_dir / "telemetry" / "telemetry.json"
    response_path = run_dir / "responses" / "cosmos_response.json"
    decision_path = run_dir / "decisions" / "decision.json"
    reports_dir = run_dir / "reports"

    reports_dir.mkdir(parents=True, exist_ok=True)

    manifest = load_json(manifest_path)
    telemetry = load_json(telemetry_path)
    cosmos_response = load_json(response_path)
    decision = load_json(decision_path)

    report_content = build_evaluation_report(
        manifest=manifest,
        telemetry=telemetry,
        cosmos_response=cosmos_response,
        decision=decision,
    )

    report_path = reports_dir / "evaluation_report.md"
    write_text(report_content, report_path)

    print(f"Evaluation report written to: {report_path}")


if __name__ == "__main__":
    main()