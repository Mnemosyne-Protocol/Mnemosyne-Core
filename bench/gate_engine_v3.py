
#!/usr/bin/env python3
"""
Mnemosyne Gate Engine v3
Fail-Closed + Active Quarantine + Signed Attestations + Merkle Ledger

Usage:
    python3 gate_engine_v3.py sample_frame.png

Dependencies:
    python3 -m pip install opencv-python cryptography

Behavior:
- Validates image via OpenCV
- Canonicalizes image bytes to reduce metadata influence
- Computes file and canonical hashes
- Enforces policy checks
- On FAIL:
    * quarantines file to ./vault/assets/rejected/
    * deletes original from source location
    * writes signed rejection record
- On PASS:
    * writes signed attestation
    * appends record to ledger
    * updates Merkle root
- Uses Ed25519 keypair stored in ./vault/keys/
"""

import sys
import os
import json
import hashlib
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

import cv2
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization

APP_NAME = "Mnemosyne Gate Engine"
APP_VERSION = "3.0.0"
NODE_ID = "MNEMOSYNE-NODE-01"
STAGE = "layer0_gate_precheck"
LEDGER_VERSION = "1"

POLICY = {
    "allowed_extensions": [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"],
    "min_width": 256,
    "min_height": 256,
    "max_width": 16384,
    "max_height": 16384,
    "min_channels": 1,
    "max_channels": 4,
}

BASE_DIR = Path("./vault")
QUARANTINE_DIR = Path("/Volumes/MNEMOSYNE-GATE/Vault/pipeline-tests/quarantine")
PATHS = {
    "attestations": BASE_DIR / "attestations",
    "rejections": BASE_DIR / "rejections",
    "validated_assets": BASE_DIR / "assets" / "validated",
    "rejected_assets": QUARANTINE_DIR,
    "ledger_records": BASE_DIR / "ledger" / "records",
    "ledger_state": BASE_DIR / "ledger" / "state",
    "keys": BASE_DIR / "keys",
}

PRIVATE_KEY_PATH = PATHS["keys"] / "mnemosyne_ed25519_private.pem"
PUBLIC_KEY_PATH = PATHS["keys"] / "mnemosyne_ed25519_public.pem"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def ensure_dirs() -> None:
    for p in PATHS.values():
        ensure_dir(p)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(payload: Dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def load_image(path: Path):
    return cv2.imread(str(path), cv2.IMREAD_UNCHANGED)


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
    h, w = img.shape[:2]
    return int(w), int(h)


def canonicalize_image(img, channels: int) -> bytes:
    ext = ".png"
    params = [cv2.IMWRITE_PNG_COMPRESSION, 9]
    ok, encoded = cv2.imencode(ext, img, params)
    if not ok:
        raise ValueError("OpenCV failed to canonicalize image.")
    return encoded.tobytes()


def simple_style_fingerprint(img) -> Dict[str, Any]:
    mean = cv2.mean(img)
    rounded = [round(float(x), 6) for x in mean[:4]]
    return {"pixel_mean": rounded}


def inspect_metadata(path: Path, img, width: int, height: int, channels: int) -> Dict[str, Any]:
    metadata = {
        "file_name": path.name,
        "suffix": path.suffix.lower(),
        "size_bytes": path.stat().st_size if path.exists() else None,
        "width": width,
        "height": height,
        "channels": channels,
        "dtype": str(img.dtype) if img is not None else None,
        "opencv_shape": list(img.shape) if img is not None else None,
    }
    return metadata


def validate_policy(path: Path, width: int, height: int, channels: int) -> List[Dict[str, Any]]:
    checks = [
        {
            "check": "allowed_extension",
            "passed": path.suffix.lower() in POLICY["allowed_extensions"],
            "detail": f"extension={path.suffix.lower()}",
        },
        {
            "check": "min_resolution",
            "passed": width >= POLICY["min_width"] and height >= POLICY["min_height"],
            "detail": f"width={width}, height={height}, min=({POLICY['min_width']}x{POLICY['min_height']})",
        },
        {
            "check": "max_resolution",
            "passed": width <= POLICY["max_width"] and height <= POLICY["max_height"],
            "detail": f"width={width}, height={height}, max=({POLICY['max_width']}x{POLICY['max_height']})",
        },
        {
            "check": "channel_bounds",
            "passed": POLICY["min_channels"] <= channels <= POLICY["max_channels"],
            "detail": f"channels={channels}, allowed=({POLICY['min_channels']}..{POLICY['max_channels']})",
        },
    ]
    return checks


def key_fingerprint_from_public_key(pub: Ed25519PublicKey) -> str:
    raw = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return sha256_bytes(raw)


def ensure_signing_keys() -> Dict[str, str]:
    ensure_dir(PATHS["keys"])
    if not PRIVATE_KEY_PATH.exists() or not PUBLIC_KEY_PATH.exists():
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        PRIVATE_KEY_PATH.write_bytes(private_bytes)
        PUBLIC_KEY_PATH.write_bytes(public_bytes)
        try:
            os.chmod(PRIVATE_KEY_PATH, 0o600)
        except Exception:
            pass
    else:
        private_key = serialization.load_pem_private_key(
            PRIVATE_KEY_PATH.read_bytes(),
            password=None,
        )
        public_key = serialization.load_pem_public_key(PUBLIC_KEY_PATH.read_bytes())

    pub_fpr = key_fingerprint_from_public_key(public_key)
    return {
        "private_key_path": str(PRIVATE_KEY_PATH.resolve()),
        "public_key_path": str(PUBLIC_KEY_PATH.resolve()),
        "public_key_fingerprint_sha256": pub_fpr,
    }


def load_private_key() -> Ed25519PrivateKey:
    return serialization.load_pem_private_key(PRIVATE_KEY_PATH.read_bytes(), password=None)


def sign_payload(unsigned_payload: Dict[str, Any]) -> Dict[str, Any]:
    private_key = load_private_key()
    public_key = private_key.public_key()
    signing_bytes = canonical_json_bytes(unsigned_payload)
    signature = private_key.sign(signing_bytes).hex()
    signed = dict(unsigned_payload)
    signed["signature"] = {
        "algorithm": "Ed25519",
        "public_key_fingerprint_sha256": key_fingerprint_from_public_key(public_key),
        "signature_hex": signature,
        "signed_fields_canonical_json_sha256": sha256_bytes(signing_bytes),
    }
    return signed


def quarantine_and_remove(src: Path) -> Path:
    ensure_dir(PATHS["rejected_assets"])
    dst = PATHS["rejected_assets"] / src.name
    if src.resolve() != dst.resolve():
        shutil.copy2(src, dst)
        src.unlink(missing_ok=True)
    return dst


def store_validated_copy(src: Path) -> Path:
    ensure_dir(PATHS["validated_assets"])
    dst = PATHS["validated_assets"] / src.name
    if src.resolve() != dst.resolve():
        shutil.copy2(src, dst)
    return dst


def get_ledger_chain_path() -> Path:
    return PATHS["ledger_state"] / "chain_state.json"


def get_ledger_roots_path() -> Path:
    return PATHS["ledger_state"] / "merkle_roots.json"


def load_chain_state() -> Dict[str, Any]:
    path = get_ledger_chain_path()
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {
        "version": LEDGER_VERSION,
        "record_count": 0,
        "last_record_hash": None,
        "last_record_file": None,
        "updated_at_utc": None,
    }


def save_chain_state(state: Dict[str, Any]) -> None:
    write_json(get_ledger_chain_path(), state)


def load_merkle_roots() -> Dict[str, Any]:
    path = get_ledger_roots_path()
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {
        "version": LEDGER_VERSION,
        "record_hashes": [],
        "merkle_root": None,
        "updated_at_utc": None,
    }


def save_merkle_roots(payload: Dict[str, Any]) -> None:
    write_json(get_ledger_roots_path(), payload)


def merkle_parent(a_hex: str, b_hex: str) -> str:
    return sha256_bytes(bytes.fromhex(a_hex) + bytes.fromhex(b_hex))


def compute_merkle_root(leaves: List[str]) -> Optional[str]:
    if not leaves:
        return None
    level = list(leaves)
    while len(level) > 1:
        next_level = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else level[i]
            next_level.append(merkle_parent(left, right))
        level = next_level
    return level[0]


def append_ledger_record(core_record: Dict[str, Any]) -> Dict[str, Any]:
    ensure_dir(PATHS["ledger_records"])
    ensure_dir(PATHS["ledger_state"])

    chain_state = load_chain_state()
    prev_hash = chain_state.get("last_record_hash")
    prev_file = chain_state.get("last_record_file")
    next_index = int(chain_state.get("record_count", 0)) + 1

    unsigned_record = dict(core_record)
    unsigned_record["ledger"] = {
        "version": LEDGER_VERSION,
        "record_index": next_index,
        "previous_record_hash": prev_hash,
        "previous_record_file": prev_file,
    }

    signed_record = sign_payload(unsigned_record)
    record_hash = sha256_bytes(canonical_json_bytes(signed_record))
    signed_record["ledger"]["record_hash"] = record_hash

    record_name = f"{next_index:08d}_{core_record['record_type']}_{core_record['asset_id']}.json"
    record_path = PATHS["ledger_records"] / record_name
    write_json(record_path, signed_record)

    chain_state = {
        "version": LEDGER_VERSION,
        "record_count": next_index,
        "last_record_hash": record_hash,
        "last_record_file": record_name,
        "updated_at_utc": utc_now_iso(),
    }
    save_chain_state(chain_state)

    merkle_state = load_merkle_roots()
    record_hashes = list(merkle_state.get("record_hashes", []))
    record_hashes.append(record_hash)
    merkle_root = compute_merkle_root(record_hashes)
    merkle_state = {
        "version": LEDGER_VERSION,
        "record_hashes": record_hashes,
        "merkle_root": merkle_root,
        "updated_at_utc": utc_now_iso(),
    }
    save_merkle_roots(merkle_state)

    return {
        "record_path": record_path,
        "record_hash": record_hash,
        "merkle_root": merkle_root,
        "record_index": next_index,
    }


def build_common_payload(
    asset_id: str,
    source_file: str,
    file_sha256: Optional[str],
    canonical_sha256: Optional[str],
    metadata: Dict[str, Any],
    fingerprint: Optional[Dict[str, Any]],
    status: str,
    psi: int,
) -> Dict[str, Any]:
    return {
        "asset_id": asset_id,
        "node_id": NODE_ID,
        "stage": STAGE,
        "timestamp_utc": utc_now_iso(),
        "status": status,
        "psi": psi,
        "source_file": source_file,
        "file_sha256": file_sha256,
        "canonical_sha256": canonical_sha256,
        "metadata": metadata,
        "fingerprint": fingerprint,
        "engine": {
            "name": APP_NAME,
            "version": APP_VERSION,
        },
    }


def approve(
    asset_path: Path,
    source_file: str,
    canonical_hash: str,
    file_hash: str,
    metadata: Dict[str, Any],
    fingerprint: Dict[str, Any],
    canonical_size_bytes: int,
) -> Path:
    ensure_dir(PATHS["attestations"])
    validated_copy = store_validated_copy(asset_path)

    unsigned = build_common_payload(
        asset_id=asset_path.stem,
        source_file=source_file,
        file_sha256=file_hash,
        canonical_sha256=canonical_hash,
        metadata=metadata,
        fingerprint=fingerprint,
        status="approved",
        psi=1,
    )
    unsigned["canonical_size_bytes"] = canonical_size_bytes
    unsigned["validated_asset_copy"] = str(validated_copy.resolve())

    ledger_info = append_ledger_record({
        "record_type": "approval",
        "asset_id": asset_path.stem,
        "status": "approved",
        "psi": 1,
        "source_file": source_file,
        "validated_asset_copy": str(validated_copy.resolve()),
        "file_sha256": file_hash,
        "canonical_sha256": canonical_hash,
        "metadata": metadata,
        "fingerprint": fingerprint,
        "engine": {"name": APP_NAME, "version": APP_VERSION},
        "timestamp_utc": utc_now_iso(),
    })

    unsigned["ledger"] = {
        "record_index": ledger_info["record_index"],
        "record_hash": ledger_info["record_hash"],
        "merkle_root": ledger_info["merkle_root"],
        "record_path": str(ledger_info["record_path"].resolve()),
    }

    signed = sign_payload(unsigned)
    out_path = PATHS["attestations"] / f"{asset_path.stem}.attestation.json"
    write_json(out_path, signed)
    return out_path


def reject(
    asset_path: Path,
    reasons: List[Any],
    source_file: str,
    metadata: Optional[Dict[str, Any]] = None,
    file_hash: Optional[str] = None,
    canonical_hash: Optional[str] = None,
) -> Path:
    ensure_dir(PATHS["rejections"])
    quarantined_path = None

    if asset_path.exists() and asset_path.is_file():
        try:
            quarantined_path = quarantine_and_remove(asset_path)
        except Exception as e:
            reasons = list(reasons) + [f"quarantine_failed:{e}"]

    unsigned = build_common_payload(
        asset_id=asset_path.stem,
        source_file=source_file,
        file_sha256=file_hash,
        canonical_sha256=canonical_hash,
        metadata=metadata or {},
        fingerprint=None,
        status="rejected",
        psi=0,
    )
    unsigned["reasons"] = reasons
    unsigned["quarantined_asset_copy"] = str(quarantined_path.resolve()) if quarantined_path else None

    ledger_info = append_ledger_record({
        "record_type": "rejection",
        "asset_id": asset_path.stem,
        "status": "rejected",
        "psi": 0,
        "source_file": source_file,
        "quarantined_asset_copy": str(quarantined_path.resolve()) if quarantined_path else None,
        "file_sha256": file_hash,
        "canonical_sha256": canonical_hash,
        "metadata": metadata or {},
        "reasons": reasons,
        "engine": {"name": APP_NAME, "version": APP_VERSION},
        "timestamp_utc": utc_now_iso(),
    })

    unsigned["ledger"] = {
        "record_index": ledger_info["record_index"],
        "record_hash": ledger_info["record_hash"],
        "merkle_root": ledger_info["merkle_root"],
        "record_path": str(ledger_info["record_path"].resolve()),
    }

    signed = sign_payload(unsigned)
    out_path = PATHS["rejections"] / f"{asset_path.stem}.rejection.json"
    write_json(out_path, signed)
    return out_path


def main() -> int:
    ensure_dirs()
    key_info = ensure_signing_keys()

    if len(sys.argv) != 2:
        print("Usage: python3 gate_engine_v3.py <image_file>")
        print(f"Public key: {key_info['public_key_path']}")
        return 2

    asset_path = Path(sys.argv[1])
    source_file = str(asset_path.resolve()) if asset_path.exists() else str(asset_path)

    if not asset_path.exists() or not asset_path.is_file():
        out = reject(asset_path, ["file_not_found"], source_file=source_file, metadata={}, file_hash=None)
        print("REJECTED: ψ=0")
        print(f"Rejection log: {out}")
        return 1

    try:
        original_bytes = asset_path.read_bytes()
        file_hash = sha256_bytes(original_bytes)
    except Exception as e:
        out = reject(asset_path, [f"file_read_error:{e}"], source_file=source_file, metadata={}, file_hash=None)
        print("REJECTED: ψ=0")
        print(f"Rejection log: {out}")
        return 1

    img = load_image(asset_path)
    if img is None:
        metadata = {
            "file_name": asset_path.name,
            "suffix": asset_path.suffix.lower(),
            "size_bytes": asset_path.stat().st_size if asset_path.exists() else None,
            "opencv_decode": "failed",
        }
        out = reject(asset_path, ["opencv_decode_failed"], source_file=source_file, metadata=metadata, file_hash=file_hash)
        print("REJECTED: ψ=0")
        print(f"Rejection log: {out}")
        return 1

    width, height = get_dimensions(img)
    channels = detect_channels(img)
    metadata = inspect_metadata(asset_path, img, width, height, channels)

    checks = validate_policy(asset_path, width, height, channels)
    failed_checks = [{"check": c["check"], "detail": c["detail"]} for c in checks if not c["passed"]]

    if failed_checks:
        out = reject(asset_path, failed_checks, source_file=source_file, metadata=metadata, file_hash=file_hash)
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
        out = reject(
            asset_path,
            [f"canonicalization_failed:{e}"],
            source_file=source_file,
            metadata=metadata,
            file_hash=file_hash,
            canonical_hash=None,
        )
        print("REJECTED: ψ=0")
        print(f"Rejection log: {out}")
        return 1

    out = approve(
        asset_path=asset_path,
        source_file=source_file,
        canonical_hash=canonical_hash,
        file_hash=file_hash,
        metadata=metadata,
        fingerprint=fingerprint,
        canonical_size_bytes=len(canonical_bytes),
    )

    merkle_state = load_merkle_roots()
    print("APPROVED: ψ=1")
    print(f"Source file:      {source_file}")
    print(f"File SHA256:      {file_hash}")
    print(f"Canonical SHA256: {canonical_hash}")
    print(f"Resolution:       {width}x{height}")
    print(f"Channels:         {channels}")
    print(f"Attestation:      {out}")
    print(f"Merkle root:      {merkle_state.get('merkle_root')}")
    print(f"Public key:       {PUBLIC_KEY_PATH.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
