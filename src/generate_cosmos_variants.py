from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import List
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
    enhancer = ImageEnhance.Brightness(img)
    return enhancer.enhance(0.4)


def apply_blur(img: Image.Image) -> Image.Image:
    return img.filter(ImageFilter.GaussianBlur(radius=3))


def apply_noise(img: Image.Image) -> Image.Image:
    import random

    img = img.copy()
    pixels = img.load()

    for i in range(img.size[0]):
        for j in range(img.size[1]):
            r, g, b = pixels[i, j]
            noise = random.randint(-20, 20)
            pixels[i, j] = (
                max(0, min(255, r + noise)),
                max(0, min(255, g + noise)),
                max(0, min(255, b + noise)),
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


VARIANT_FUNCTIONS = {
    "dim_lighting": apply_dim_lighting,
    "blur": apply_blur,
    "noise": apply_noise,
    "occlusion": apply_occlusion,
}


def load_frames(frames_dir: Path) -> List[Path]:
    return sorted(frames_dir.glob("frame_*.png"))


def update_manifest(manifest: dict, variant_name: str) -> dict:
    manifest = dict(manifest)
    manifest["scenario_id"] = variant_name
    manifest["variant_name"] = variant_name
    manifest["status"] = "completed"
    return manifest


def update_telemetry(telemetry: dict, variant_name: str, variant_root: Path) -> dict:
    telemetry = dict(telemetry)
    telemetry["scenario_id"] = variant_name

    updated_frames = []
    for i, frame in enumerate(telemetry.get("frames", [])):
        frame = dict(frame)
        frame["image_path"] = str(variant_root / "frames" / f"frame_{i:04d}.png")

        lidar_summary = dict(frame.get("lidar_summary", {}))
        lidar_summary["variant_name"] = variant_name
        frame["lidar_summary"] = lidar_summary

        updated_frames.append(frame)

    telemetry["frames"] = updated_frames
    return telemetry


def generate_variant(run_dir: Path, variant_name: str, transform_fn) -> None:
    source_frames = run_dir / "frames"
    source_manifest = run_dir / "manifests" / "run_manifest.json"
    source_telemetry = run_dir / "telemetry" / "telemetry.json"

    variant_root = run_dir.parent / f"{run_dir.name}_{variant_name}"
    variant_frames = variant_root / "frames"
    variant_manifest_dir = variant_root / "manifests"
    variant_telemetry_dir = variant_root / "telemetry"

    if variant_root.exists():
        shutil.rmtree(variant_root)

    variant_frames.mkdir(parents=True, exist_ok=True)
    variant_manifest_dir.mkdir(parents=True, exist_ok=True)
    variant_telemetry_dir.mkdir(parents=True, exist_ok=True)

    frame_paths = load_frames(source_frames)

    print(f"Generating variant: {variant_name}")
    print(f"Output: {variant_root}")

    for i, frame_path in enumerate(frame_paths):
        img = Image.open(frame_path).convert("RGB")
        img = transform_fn(img)
        out_path = variant_frames / f"frame_{i:04d}.png"
        img.save(out_path)

    manifest = load_json(source_manifest)
    telemetry = load_json(source_telemetry)

    manifest = update_manifest(manifest, variant_name)
    telemetry = update_telemetry(telemetry, variant_name, variant_root)

    write_json(manifest, variant_manifest_dir / "run_manifest.json")
    write_json(telemetry, variant_telemetry_dir / "telemetry.json")

    for extra_dir in ["requests", "responses", "decisions", "reports", "video"]:
        (variant_root / extra_dir).mkdir(parents=True, exist_ok=True)

    print(f"✔ Variant '{variant_name}' created\n")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate Cosmos-style visual variants from a run."
    )
    parser.add_argument(
        "--run-dir",
        required=True,
        help="Path to run directory, e.g. runs/run_0002",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    run_dir = Path(args.run_dir)

    for name, fn in VARIANT_FUNCTIONS.items():
        generate_variant(run_dir, name, fn)


if __name__ == "__main__":
    main()