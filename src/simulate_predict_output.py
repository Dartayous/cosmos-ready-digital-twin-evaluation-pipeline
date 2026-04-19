from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Callable, Dict, List

from PIL import Image, ImageEnhance, ImageFilter, ImageDraw


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(payload: dict, path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def apply_dim_lighting(img: Image.Image) -> Image.Image:
    return ImageEnhance.Brightness(img).enhance(0.4)


def apply_blur(img: Image.Image) -> Image.Image:
    return img.filter(ImageFilter.GaussianBlur(radius=3))


def apply_noise(img: Image.Image) -> Image.Image:
    import random

    img = img.copy()
    pixels = img.load()

    for i in range(img.size[0]):
        for j in range(img.size[1]):
            r, g, b = pixels[i, j]
            n = random.randint(-20, 20)
            pixels[i, j] = (
                max(0, min(255, r + n)),
                max(0, min(255, g + n)),
                max(0, min(255, b + n)),
            )
    return img


def apply_occlusion(img: Image.Image) -> Image.Image:
    img = img.copy()
    draw = ImageDraw.Draw(img)
    w, h = img.size
    draw.rectangle(
        [
            (int(w * 0.42), int(h * 0.40)),
            (int(w * 0.72), int(h * 0.70)),
        ],
        fill=(120, 120, 120),
    )
    return img


TRANSFORMS: Dict[str, Callable[[Image.Image], Image.Image]] = {
    "dim_lighting": apply_dim_lighting,
    "blur": apply_blur,
    "noise": apply_noise,
    "occlusion": apply_occlusion,
}


def sorted_frames(frames_dir: Path) -> List[Path]:
    frames = sorted(frames_dir.glob("frame_*.png"))
    if not frames:
        raise FileNotFoundError(f"No frame PNGs found in {frames_dir}")
    return frames


def build_predict_run_name(base_run_name: str, variant: str) -> str:
    return f"{base_run_name}_predict_{variant}"


def update_manifest(manifest: dict, new_run_id: str, variant: str, source_run: str) -> dict:
    manifest = dict(manifest)
    manifest["run_id"] = new_run_id
    manifest["source_run"] = source_run
    manifest["scenario_id"] = variant
    manifest["predict_mode"] = "simulated_predict_output"
    manifest["predict_variant"] = variant
    manifest["status"] = "completed"
    return manifest


def update_telemetry(telemetry: dict, new_run_id: str, variant: str, dest_run_dir: Path) -> dict:
    telemetry = dict(telemetry)
    telemetry["run_id"] = new_run_id
    telemetry["scenario_id"] = variant
    telemetry["predict_mode"] = "simulated_predict_output"

    updated_frames = []
    for i, frame in enumerate(telemetry.get("frames", [])):
        frame = dict(frame)
        frame["image_path"] = str(dest_run_dir / "frames" / f"frame_{i:04d}.png")

        lidar = dict(frame.get("lidar_summary", {}))
        lidar["predict_variant"] = variant
        frame["lidar_summary"] = lidar

        updated_frames.append(frame)

    telemetry["frames"] = updated_frames
    return telemetry


def create_simulated_predict_run(base_run_dir: Path, variant: str) -> Path:
    if variant not in TRANSFORMS:
        raise ValueError(f"Unsupported variant: {variant}")

    transform = TRANSFORMS[variant]
    dest_run_name = build_predict_run_name(base_run_dir.name, variant)
    dest_run_dir = base_run_dir.parent / dest_run_name

    if dest_run_dir.exists():
        shutil.rmtree(dest_run_dir)

    for subdir in [
        "frames",
        "video",
        "telemetry",
        "manifests",
        "requests",
        "responses",
        "decisions",
        "reports",
    ]:
        (dest_run_dir / subdir).mkdir(parents=True, exist_ok=True)

    source_frames = sorted_frames(base_run_dir / "frames")
    for i, src_frame in enumerate(source_frames):
        img = Image.open(src_frame).convert("RGB")
        img = transform(img)
        img.save(dest_run_dir / "frames" / f"frame_{i:04d}.png")

    source_manifest = load_json(base_run_dir / "manifests" / "run_manifest.json")
    source_telemetry = load_json(base_run_dir / "telemetry" / "telemetry.json")

    new_manifest = update_manifest(
        source_manifest,
        new_run_id=dest_run_name,
        variant=variant,
        source_run=base_run_dir.name,
    )
    new_telemetry = update_telemetry(
        source_telemetry,
        new_run_id=dest_run_name,
        variant=variant,
        dest_run_dir=dest_run_dir,
    )

    write_json(new_manifest, dest_run_dir / "manifests" / "run_manifest.json")
    write_json(new_telemetry, dest_run_dir / "telemetry" / "telemetry.json")

    return dest_run_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create simulated Cosmos Predict output runs from a baseline run."
    )
    parser.add_argument(
        "--run-dir",
        required=True,
        help="Path to the baseline run, e.g. runs/run_0004",
    )
    parser.add_argument(
        "--variant",
        choices=["dim_lighting", "blur", "noise", "occlusion", "all"],
        default="all",
        help="Which simulated Predict variant to create.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_run_dir = Path(args.run_dir)

    if not base_run_dir.exists():
        raise FileNotFoundError(f"Base run does not exist: {base_run_dir}")

    variants = list(TRANSFORMS.keys()) if args.variant == "all" else [args.variant]

    print(f"Base run: {base_run_dir}")
    for variant in variants:
        out_dir = create_simulated_predict_run(base_run_dir, variant)
        print(f"Created simulated Predict run: {out_dir}")


if __name__ == "__main__":
    main()