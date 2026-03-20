#!/usr/bin/env python3
"""
Mnemosyne Layer-0 Gate Prototype
Usage:
    python3 gate_engine.py sample_frame.png

Behavior:
- Loads an image with OpenCV
- Re-encodes it into a canonical in-memory format to avoid source metadata affecting the hash
- Checks basic policy rules (readable image, allowed extension, min/max resolution)
- Computes SHA-256 hash of canonical bytes
- Writes JSON attestation on success
- Writes rejection JSON log on failure
- Exits fail-closed (non-zero exit code) when validation fails
"""

import sys
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

import cv2

APP_NAME = "Mnemosyne Gate Engine"
APP_VERSION = "0.1.0"
NODE_ID = "MNEMOSYNE-NODE-01"
STAGE = "layer0_gate_precheck"
QUARANTINE_DIR = Path("/Volumes/MNEMOSYNE-GATE/Vault/pipeline-tests/quarantine")

# Conservative defaults; adjust as needed for your NGM test.
POLICY = {
    "allowed_extensions": [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"],
    "min_width": 256,
    "min_height": 256,
    "max_width": 16384,
    "max_height": 16384,
    "min_channels": 1,
    "max_channels": 4,
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_image(path: Path):
    # IMREAD_UNCHANGED preserves alpha channels when present.
    img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    return img


def detect_channels(img) -> int:
    if img is None:
        return 0
    if len(img.shape) == 2:
        return 1
    if len(img.shape) == 3:
        return int(img.shape[2])
    return 0


def get_dimensions(img):
    if img is None:
        return 0, 0
    height, width = img.shape[:2]
    return int(width), int(height)


def choose_canonical_extension(channels: int) -> str:
    # PNG supports grayscale/RGB/RGBA well and is deterministic enough for this gate prototype.
    return ".png"


def canonicalize_image(img, channels: int) -> bytes:
    """
    Re-encode the pixel matrix to canonical bytes.
    This intentionally discards original container metadata.
    Hash is based on normalized image bytes, not original file bytes.
    """
    ext = choose_canonical_extension(channels)

    params = []
    if ext == ".png":
        # Compression level 9 for repeatable output.
        params = [cv2.IMWRITE_PNG_COMPRESSION, 9]
    elif ext in {".jpg", ".jpeg"}:
        params = [cv2.IMWRITE_JPEG_QUALITY, 100]

    ok, encoded = cv2.imencode(ext, img, params)
    if not ok:
        raise ValueError("OpenCV failed to encode canonical image bytes.")

    return encoded.tobytes()


def simple_style_fingerprint(img) -> dict:
    """
    Lightweight deterministic fingerprint using pixel statistics.
    Not a full Mnemosyne style_hash, but a useful prototype signal.
    """
    mean = cv2.mean(img)
    # cv2.mean returns up to 4 channels.
    rounded = [round(float(x), 4) for x in mean[:4]]
    return {
        "pixel_mean": rounded,
    }


def validate_policy(path: Path, width: int, height: int, channels: int) -> list:
    checks = []
    ext_ok = path.suffix.lower() in POLICY["allowed_extensions"]
    checks.append(("allowed_extension", ext_ok, f"extension={path.suffix.lower()}"))

    checks.append((
        "min_resolution",
        width >= POLICY["min_width"] and height >= POLICY["min_height"],
        f"width={width}, height={height}, min=({POLICY['min_width']}x{POLICY['min_height']})",
    ))

    checks.append((
        "max_resolution",
        width <= POLICY["max_width"] and height <= POLICY["max_height"],
        f"width={width}, height={height}, max=({POLICY['max_width']}x{POLICY['max_height']})",
    ))

    checks.append((
        "channel_bounds",
        POLICY["min_channels"] <= channels <= POLICY["max_channels"],
        f"channels={channels}, allowed=({POLICY['min_channels']}..{POLICY['max_channels']})",
    ))

    return checks


def write_json(path: Path, payload: dict) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def approve(asset_path: Path, canonical_hash: str, file_hash: str, width: int, height: int,
            channels: int, fingerprint: dict, canonical_size_bytes: int) -> Path:
    attestation_dir = Path("./vault/attestations")
    validated_dir = Path("./vault/assets/validated")
    ensure_dir(attestation_dir)
    ensure_dir(validated_dir)

    attestation = {
        "asset_id": asset_path.stem,
        "node_id": NODE_ID,
        "stage": STAGE,
        "timestamp_utc": utc_now_iso(),
        "status": "approved",
        "psi": 1,
        "source_file": str(asset_path.resolve()),
        "file_sha256": file_hash,
        "canonical_sha256": canonical_hash,
        "canonical_size_bytes": canonical_size_bytes,
        "image": {
            "width": width,
            "height": height,
            "channels": channels,
        },
        "fingerprint": fingerprint,
        "engine": {
            "name": APP_NAME,
            "version": APP_VERSION,
        },
    }

    out_path = attestation_dir / f"{asset_path.stem}.attestation.json"
    write_json(out_path, attestation)
    return out_path


def reject(asset_path: Path, reasons: list, width: int = 0, height: int = 0, channels: int = 0,
           file_hash: str | None = None) -> Path:
    rejection_dir = Path("./vault/rejections")
    rejected_assets_dir = QUARANTINE_DIR
    ensure_dir(rejection_dir)
    ensure_dir(rejected_assets_dir)

    payload = {
        "asset_id": asset_path.stem,
        "node_id": NODE_ID,
        "stage": STAGE,
        "timestamp_utc": utc_now_iso(),
        "status": "rejected",
        "psi": 0,
        "source_file": str(asset_path.resolve()),
        "file_sha256": file_hash,
        "image": {
            "width": width,
            "height": height,
            "channels": channels,
        },
        "reasons": reasons,
        "engine": {
            "name": APP_NAME,
            "version": APP_VERSION,
        },
    }

    out_path = rejection_dir / f"{asset_path.stem}.rejection.json"
    write_json(out_path, payload)
    return out_path


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 gate_engine.py <image_file>")
        return 2

    asset_path = Path(sys.argv[1])
    if not asset_path.exists() or not asset_path.is_file():
        print(f"REJECTED: file not found -> {asset_path}")
        reject(asset_path, ["file_not_found"])
        return 1

    try:
        original_bytes = asset_path.read_bytes()
        file_hash = sha256_bytes(original_bytes)
    except Exception as e:
        print(f"REJECTED: could not read file bytes -> {e}")
        reject(asset_path, [f"file_read_error:{e}"], file_hash=None)
        return 1

    img = load_image(asset_path)
    if img is None:
        print("REJECTED: OpenCV could not decode the image.")
        reject(asset_path, ["opencv_decode_failed"], file_hash=file_hash)
        return 1

    width, height = get_dimensions(img)
    channels = detect_channels(img)

    policy_checks = validate_policy(asset_path, width, height, channels)
    failed_checks = [
        {"check": name, "detail": detail}
        for name, passed, detail in policy_checks if not passed
    ]

    if failed_checks:
        out = reject(asset_path, failed_checks, width, height, channels, file_hash=file_hash)
        print("REJECTED: ψ=0")
        print(f"Rejection log: {out}")
        for item in failed_checks:
            print(f" - {item['check']}: {item['detail']}")
        return 1

    try:
        canonical_bytes = canonicalize_image(img, channels)
        canonical_hash = sha256_bytes(canonical_bytes)
        fingerprint = simple_style_fingerprint(img)
    except Exception as e:
        out = reject(asset_path, [f"canonicalization_failed:{e}"], width, height, channels, file_hash=file_hash)
        print("REJECTED: ψ=0")
        print(f"Rejection log: {out}")
        return 1

    out = approve(
        asset_path=asset_path,
        canonical_hash=canonical_hash,
        file_hash=file_hash,
        width=width,
        height=height,
        channels=channels,
        fingerprint=fingerprint,
        canonical_size_bytes=len(canonical_bytes),
    )

    print("APPROVED: ψ=1")
    print(f"Source file:      {asset_path}")
    print(f"File SHA256:      {file_hash}")
    print(f"Canonical SHA256: {canonical_hash}")
    print(f"Resolution:       {width}x{height}")
    print(f"Channels:         {channels}")
    print(f"Attestation:      {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
