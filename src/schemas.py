from __future__ import annotations

from typing import Any, Dict, Iterable


MANIFEST_REQUIRED_KEYS = (
    "run_id",
    "timestamp_utc",
    "project",
    "scenario_id",
    "usd_file",
    "source_project",
    "capture_mode",
    "sensor_outputs",
    "status",
)

COSMOS_REQUEST_REQUIRED_KEYS = (
    "run_id",
    "scenario_id",
    "task_type",
    "inputs",
    "questions",
    "required_output_schema",
)

COSMOS_RESPONSE_REQUIRED_KEYS = (
    "run_id",
    "scenario_id",
    "model_name",
    "analysis",
    "recommendation",
)

DECISION_REQUIRED_KEYS = (
    "run_id",
    "decision_type",
    "approved_for_training",
    "reason_code",
    "next_step",
)


def find_missing_keys(payload: Dict[str, Any], required_keys: Iterable[str]) -> list[str]:
    """Return a list of required keys that are missing from payload."""
    return [key for key in required_keys if key not in payload]


def validate_required_keys(
    payload: Dict[str, Any],
    required_keys: Iterable[str],
    payload_name: str,
) -> None:
    """Raise ValueError if any required key is missing."""
    missing = find_missing_keys(payload, required_keys)
    if missing:
        raise ValueError(
            f"{payload_name} is missing required keys: {', '.join(missing)}"
        )


def validate_manifest(payload: Dict[str, Any]) -> None:
    validate_required_keys(payload, MANIFEST_REQUIRED_KEYS, "run_manifest")


def validate_cosmos_request(payload: Dict[str, Any]) -> None:
    validate_required_keys(payload, COSMOS_REQUEST_REQUIRED_KEYS, "cosmos_request")


def validate_cosmos_response(payload: Dict[str, Any]) -> None:
    validate_required_keys(payload, COSMOS_RESPONSE_REQUIRED_KEYS, "cosmos_response")


def validate_decision(payload: Dict[str, Any]) -> None:
    validate_required_keys(payload, DECISION_REQUIRED_KEYS, "decision")