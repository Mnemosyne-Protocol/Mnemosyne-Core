#!/usr/bin/env python3
"""
Mnemosyne Gate Engine v2 (Fail-Closed + Quarantine)

Usage:
    python3 gate_engine_v2.py <image_file>

Behavior:
- Validates image via OpenCV
- Canonicalizes (re-encodes) to remove metadata influence
- Computes hashes
- Applies policy checks
- On FAIL: moves file to /vault/assets/rejected/ and deletes original
- On PASS: writes attestation
"""

import sys
import json
import hashlib
import shutil
from pathlib import Path
from datetime import datetime, timezone

import cv2

NODE_ID = "MNEMOSYNE-NODE-01"
QUARANTINE_DIR = Path("/Volumes/MNEMOSYNE-GATE/Vault/pipeline-tests/quarantine")

POLICY = {
    "allowed_extensions": [".png", ".jpg", ".jpeg", ".webp"],
    "min_width": 256,
    "min_height": 256,
}

def now():
    return datetime.now(timezone.utc).isoformat()

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def ensure(p):
    p.mkdir(parents=True, exist_ok=True)

def quarantine_and_remove(src):
    dst_dir = QUARANTINE_DIR
    ensure(dst_dir)
    dst = dst_dir / src.name
    shutil.copy2(src, dst)
    src.unlink(missing_ok=True)
    return dst

def reject(path, reason):
    q = quarantine_and_remove(path)
    ensure(Path("./vault/rejections"))
    log = {
        "status": "rejected",
        "psi": 0,
        "reason": reason,
        "file": str(q),
        "timestamp": now()
    }
    out = Path("./vault/rejections") / f"{path.stem}.json"
    with open(out, "w") as f:
        json.dump(log, f, indent=2)
    print("REJECTED:", reason)
    return 1

def approve(path, canonical_hash):
    ensure(Path("./vault/attestations"))
    log = {
        "status": "approved",
        "psi": 1,
        "hash": canonical_hash,
        "file": str(path),
        "timestamp": now()
    }
    out = Path("./vault/attestations") / f"{path.stem}.json"
    with open(out, "w") as f:
        json.dump(log, f, indent=2)
    print("APPROVED")
    return 0

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 gate_engine_v2.py <image>")
        return 2

    p = Path(sys.argv[1])
    if not p.exists():
        return reject(p, "file_not_found")

    if p.suffix.lower() not in POLICY["allowed_extensions"]:
        return reject(p, "invalid_extension")

    img = cv2.imread(str(p))
    if img is None:
        return reject(p, "decode_failed")

    h, w = img.shape[:2]

    if w < POLICY["min_width"] or h < POLICY["min_height"]:
        return reject(p, "resolution_too_small")

    # canonicalize
    ok, buf = cv2.imencode(".png", img)
    if not ok:
        return reject(p, "canonicalization_failed")

    canonical_bytes = buf.tobytes()
    hsh = sha256(canonical_bytes)

    return approve(p, hsh)

if __name__ == "__main__":
    raise SystemExit(main())
