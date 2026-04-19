from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from scenario_registry import ScenarioRegistry
from schemas import validate_manifest


PROJECT_NAME = "project_08_cosmos_integration_demo"
SOURCE_PROJECT = "project_03_interactive_robotics_twin"


def make_run_id(runs_dir: Path) -> str:
    """Create the next sequential run ID based on existing run folders."""
    runs_dir.mkdir(parents=True, exist_ok=True)

    existing = []
    for path in runs_dir.iterdir():
        if path.is_dir() and path.name.startswith("run_"):
            suffix = path.name.replace("run_", "")
            if suffix.isdigit():
                existing.append(int(suffix))

    next_index = (max(existing) + 1) if existing else 1
    return f"run_{next_index:04d}"


def ensure_run_subdirs(run_dir: Path) -> Dict[str, Path]:
    """Create standard subdirectories for a run bundle."""
    subdirs = {
        "frames": run_dir / "frames",
        "video": run_dir / "video",
        "telemetry": run_dir / "telemetry",
        "manifests": run_dir / "manifests",
        "requests": run_dir / "requests",
        "responses": run_dir / "responses",
        "decisions": run_dir / "decisions",
        "reports": run_dir / "reports",
    }

    for path in subdirs.values():
        path.mkdir(parents=True, exist_ok=True)

    return subdirs


def copy_frames(frame_paths: List[str], frames_dir: Path) -> List[str]:
    """
    Copy source frames into the run bundle.
    Returns relative paths to copied frames inside the run folder.
    """
    copied_relative_paths: List[str] = []

    for index, frame_path_str in enumerate(frame_paths):
        source_path = Path(frame_path_str)

        if not source_path.exists():
            raise FileNotFoundError(f"Frame not found: {source_path}")

        destination_name = f"frame_{index:04d}{source_path.suffix.lower()}"
        destination_path = frames_dir / destination_name
        shutil.copy2(source_path, destination_path)

        copied_relative_paths.append(str(destination_path))

    return copied_relative_paths


def build_manifest(
    run_id: str,
    scenario: Dict[str, Any],
    copied_frames: List[str],
) -> Dict[str, Any]:
    """Build the run manifest JSON payload."""
    return {
        "run_id": run_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "project": PROJECT_NAME,
        "scenario_id": scenario["scenario_id"],
        "usd_file": scenario["usd_file"],
        "source_project": SOURCE_PROJECT,
        "capture_mode": "offline_replay",
        "sensor_outputs": [
            "rgb_frames",
            "telemetry_json",
            "lidar_summary_placeholder"
        ],
        "status": "completed",
        "frame_count": len(copied_frames),
    }


def build_telemetry(
    run_id: str,
    scenario: Dict[str, Any],
    copied_frames: List[str],
) -> Dict[str, Any]:
    """
    Build placeholder telemetry for v01.
    Later this can be replaced by real Isaac-exported telemetry.
    """
    frames_payload = []

    for index, frame_path in enumerate(copied_frames):
        frames_payload.append(
            {
                "frame_index": index,
                "timestamp_sim": round(index * 0.1, 3),
                "camera_id": "front_eval_cam",
                "image_path": frame_path,
                "robot_pose": {
                    "position": [0.0, 0.0, 0.0],
                    "yaw_deg": 0.0
                },
                "obstacle_metadata": {
                    "obstacle_id": scenario["obstacle_id"],
                    "known_world_position": [1.2, 0.0, 0.0]
                },
                "lidar_summary": {
                    "obstacle_detected": True,
                    "notes": "Placeholder summary for v01. Replace with real exported LiDAR metrics later."
                }
            }
        )

    return {
        "run_id": run_id,
        "scenario_id": scenario["scenario_id"],
        "frames": frames_payload
    }


def write_json(payload: Dict[str, Any], path: Path) -> None:
    """Write JSON payload to disk with readable formatting."""
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a Project 08 run bundle from selected frame images."
    )
    parser.add_argument(
        "--scenario-id",
        required=True,
        help="Scenario ID from configs/scenarios.json"
    )
    parser.add_argument(
        "--frame",
        action="append",
        required=True,
        help="Path to a source frame image. Use multiple --frame arguments."
    )
    parser.add_argument(
        "--runs-dir",
        default="runs",
        help="Directory where run folders will be created."
    )
    parser.add_argument(
        "--config",
        default="configs/scenarios.json",
        help="Path to the scenario config JSON."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    registry = ScenarioRegistry(args.config)
    scenario = registry.get_scenario(args.scenario_id)

    runs_dir = Path(args.runs_dir)
    run_id = make_run_id(runs_dir)
    run_dir = runs_dir / run_id
    subdirs = ensure_run_subdirs(run_dir)

    copied_frames = copy_frames(args.frame, subdirs["frames"])

    manifest = build_manifest(run_id, scenario, copied_frames)
    validate_manifest(manifest)

    telemetry = build_telemetry(run_id, scenario, copied_frames)

    manifest_path = subdirs["manifests"] / "run_manifest.json"
    telemetry_path = subdirs["telemetry"] / "telemetry.json"

    write_json(manifest, manifest_path)
    write_json(telemetry, telemetry_path)

    print(f"Created run bundle: {run_dir}")
    print(f"Manifest: {manifest_path}")
    print(f"Telemetry: {telemetry_path}")
    print("Copied frames:")
    for frame in copied_frames:
        print(f"  - {frame}")


if __name__ == "__main__":
    main()