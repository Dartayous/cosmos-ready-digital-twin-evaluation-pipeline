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
SOURCE_PROJECT = "project_08_isaac_capture_bridge"


def make_run_id(runs_dir: Path) -> str:
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


def discover_png_frames(source_dir: Path) -> List[Path]:
    frame_paths = sorted(source_dir.glob("*.png"))
    if not frame_paths:
        raise FileNotFoundError(f"No PNG frames found in: {source_dir}")
    return frame_paths


def copy_frames(frame_paths: List[Path], frames_dir: Path) -> List[str]:
    copied_relative_paths: List[str] = []

    for index, source_path in enumerate(frame_paths):
        destination_name = f"frame_{index:04d}{source_path.suffix.lower()}"
        destination_path = frames_dir / destination_name
        shutil.copy2(source_path, destination_path)
        copied_relative_paths.append(str(destination_path))

    return copied_relative_paths


def load_optional_source_telemetry(source_dir: Path) -> Dict[str, Any] | None:
    telemetry_path = source_dir / "telemetry.json"
    if not telemetry_path.exists():
        return None

    with telemetry_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_manifest(
    run_id: str,
    scenario: Dict[str, Any],
    copied_frames: List[str],
    source_capture_dir: Path,
    used_source_telemetry: bool,
) -> Dict[str, Any]:
    sensor_outputs = [
        "rgb_frames",
        "telemetry_json",
    ]

    sensor_outputs.append(
        "lidar_summary_from_source_telemetry"
        if used_source_telemetry
        else "lidar_summary_placeholder"
    )

    return {
        "run_id": run_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "project": PROJECT_NAME,
        "scenario_id": scenario["scenario_id"],
        "usd_file": scenario["usd_file"],
        "source_project": SOURCE_PROJECT,
        "capture_mode": "isaac_import",
        "source_capture_dir": str(source_capture_dir),
        "sensor_outputs": sensor_outputs,
        "status": "completed",
        "frame_count": len(copied_frames),
        "used_source_telemetry": used_source_telemetry,
    }


def build_placeholder_telemetry(
    run_id: str,
    scenario: Dict[str, Any],
    copied_frames: List[str],
    camera_id: str,
) -> Dict[str, Any]:
    frames_payload = []

    for index, frame_path in enumerate(copied_frames):
        frames_payload.append(
            {
                "frame_index": index,
                "timestamp_sim": round(index * 0.1, 3),
                "camera_id": camera_id,
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
                    "notes": "Placeholder summary for Isaac-import v02. Replace with real exported LiDAR metrics later."
                }
            }
        )

    return {
        "run_id": run_id,
        "scenario_id": scenario["scenario_id"],
        "capture_mode": "isaac_import",
        "telemetry_source": "placeholder",
        "frames": frames_payload
    }


def build_source_telemetry(
    run_id: str,
    scenario: Dict[str, Any],
    copied_frames: List[str],
    camera_id: str,
    source_telemetry: Dict[str, Any],
) -> Dict[str, Any]:
    source_frames = source_telemetry.get("frames", [])
    frames_payload = []

    for index, frame_path in enumerate(copied_frames):
        source_frame = source_frames[index] if index < len(source_frames) else {}

        frames_payload.append(
            {
                "frame_index": index,
                "timestamp_sim": source_frame.get("timestamp_sim", round(index * 0.1, 3)),
                "camera_id": source_frame.get("camera_id", camera_id),
                "image_path": frame_path,
                "robot_pose": source_frame.get(
                    "robot_pose",
                    {
                        "position": [0.0, 0.0, 0.0],
                        "yaw_deg": 0.0
                    }
                ),
                "obstacle_metadata": source_frame.get(
                    "obstacle_metadata",
                    {
                        "obstacle_id": scenario["obstacle_id"],
                        "known_world_position": [1.2, 0.0, 0.0]
                    }
                ),
                "lidar_summary": source_frame.get(
                    "lidar_summary",
                    {
                        "obstacle_detected": True,
                        "notes": "Source telemetry present, but lidar_summary was missing for this frame."
                    }
                )
            }
        )

    return {
        "run_id": run_id,
        "scenario_id": scenario["scenario_id"],
        "capture_mode": "isaac_import",
        "telemetry_source": "source_telemetry.json",
        "frames": frames_payload
    }


def write_json(payload: Dict[str, Any], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import Isaac-captured PNG frames into a new Project 08 run bundle."
    )
    parser.add_argument(
        "--scenario-id",
        required=True,
        help="Scenario ID from configs/scenarios.json"
    )
    parser.add_argument(
        "--source-dir",
        required=True,
        help="Folder containing Isaac-exported PNG frames"
    )
    parser.add_argument(
        "--camera-id",
        default="isaac_import_cam",
        help="Camera ID to record in telemetry when source telemetry does not provide one"
    )
    parser.add_argument(
        "--runs-dir",
        default="runs",
        help="Directory where run folders will be created"
    )
    parser.add_argument(
        "--config",
        default="configs/scenarios.json",
        help="Path to scenario config JSON"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    source_dir = Path(args.source_dir)
    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    registry = ScenarioRegistry(args.config)
    scenario = registry.get_scenario(args.scenario_id)

    runs_dir = Path(args.runs_dir)
    run_id = make_run_id(runs_dir)
    run_dir = runs_dir / run_id
    subdirs = ensure_run_subdirs(run_dir)

    source_frames = discover_png_frames(source_dir)
    copied_frames = copy_frames(source_frames, subdirs["frames"])

    source_telemetry = load_optional_source_telemetry(source_dir)
    used_source_telemetry = source_telemetry is not None

    manifest = build_manifest(
        run_id=run_id,
        scenario=scenario,
        copied_frames=copied_frames,
        source_capture_dir=source_dir,
        used_source_telemetry=used_source_telemetry,
    )
    validate_manifest(manifest)

    if used_source_telemetry:
        telemetry = build_source_telemetry(
            run_id=run_id,
            scenario=scenario,
            copied_frames=copied_frames,
            camera_id=args.camera_id,
            source_telemetry=source_telemetry,
        )
    else:
        telemetry = build_placeholder_telemetry(
            run_id=run_id,
            scenario=scenario,
            copied_frames=copied_frames,
            camera_id=args.camera_id,
        )

    manifest_path = subdirs["manifests"] / "run_manifest.json"
    telemetry_path = subdirs["telemetry"] / "telemetry.json"

    write_json(manifest, manifest_path)
    write_json(telemetry, telemetry_path)

    print(f"Imported Isaac capture into run: {run_dir}")
    print(f"Source capture dir: {source_dir}")
    print(f"Used source telemetry: {used_source_telemetry}")
    print(f"Manifest: {manifest_path}")
    print(f"Telemetry: {telemetry_path}")
    print("Copied frames:")
    for frame in copied_frames:
        print(f"  - {frame}")


if __name__ == "__main__":
    main()