
#!/usr/bin/env python3
"""
Mnemosyne Ledger Verifier v4
Independent verifier for signed ledger records, chain integrity, and Merkle root.

Usage:
    python3 verify_mnemosyne_ledger.py
    python3 verify_mnemosyne_ledger.py ./vault
    python3 verify_mnemosyne_ledger.py ./vault /path/to/public_key.pem

Dependencies:
    python3 -m pip install cryptography

What it verifies:
- All ledger record JSON files under ./vault/ledger/records/
- Ed25519 signatures using the public key
- Canonical JSON hash of signed payload
- previous_record_hash chain links
- previous_record_file chain links
- chain_state.json consistency
- merkle_roots.json consistency

Exit codes:
- 0 = VERIFIED
- 1 = CHAIN COMPROMISED / verification failed
- 2 = usage or environment error
"""

import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(payload: Dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_public_key(path: Path) -> Ed25519PublicKey:
    data = path.read_bytes()
    return serialization.load_pem_public_key(data)


def public_key_fingerprint(pub: Ed25519PublicKey) -> str:
    raw = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return sha256_bytes(raw)


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


def verify_record_signature(record: Dict[str, Any], public_key: Ed25519PublicKey) -> List[str]:
    errors = []
    signature_block = record.get("signature")
    if not isinstance(signature_block, dict):
        return ["missing_signature_block"]

    sig_hex = signature_block.get("signature_hex")
    declared_signed_sha = signature_block.get("signed_fields_canonical_json_sha256")
    if not sig_hex or not declared_signed_sha:
        return ["incomplete_signature_block"]

    unsigned_record = dict(record)
    unsigned_record.pop("signature", None)
    signing_bytes = canonical_json_bytes(unsigned_record)
    calculated_signed_sha = sha256_bytes(signing_bytes)

    if calculated_signed_sha != declared_signed_sha:
        errors.append(
            f"signed_payload_hash_mismatch: declared={declared_signed_sha} calculated={calculated_signed_sha}"
        )

    try:
        public_key.verify(bytes.fromhex(sig_hex), signing_bytes)
    except InvalidSignature:
        errors.append("invalid_ed25519_signature")
    except Exception as e:
        errors.append(f"signature_verification_error:{e}")

    return errors


def verify_record_hash(record: Dict[str, Any]) -> List[str]:
    errors = []
    ledger = record.get("ledger", {})
    declared_record_hash = ledger.get("record_hash")
    if not declared_record_hash:
        return ["missing_ledger_record_hash"]

    calculated_record_hash = sha256_bytes(canonical_json_bytes(record))
    if calculated_record_hash != declared_record_hash:
        errors.append(
            f"record_hash_mismatch: declared={declared_record_hash} calculated={calculated_record_hash}"
        )
    return errors


def main() -> int:
    if len(sys.argv) > 3:
        print("Usage: python3 verify_mnemosyne_ledger.py [vault_dir] [public_key_path]")
        return 2

    vault_dir = Path(sys.argv[1]) if len(sys.argv) >= 2 else Path("./vault")
    public_key_path = (
        Path(sys.argv[2])
        if len(sys.argv) == 3
        else vault_dir / "keys" / "mnemosyne_ed25519_public.pem"
    )

    records_dir = vault_dir / "ledger" / "records"
    chain_state_path = vault_dir / "ledger" / "state" / "chain_state.json"
    merkle_roots_path = vault_dir / "ledger" / "state" / "merkle_roots.json"

    if not vault_dir.exists():
        print(f"ERROR: vault dir not found -> {vault_dir}")
        return 2
    if not records_dir.exists():
        print(f"ERROR: ledger records dir not found -> {records_dir}")
        return 2
    if not public_key_path.exists():
        print(f"ERROR: public key not found -> {public_key_path}")
        return 2

    try:
        public_key = load_public_key(public_key_path)
        expected_pub_fpr = public_key_fingerprint(public_key)
    except Exception as e:
        print(f"ERROR: could not load public key -> {e}")
        return 2

    record_files = sorted(records_dir.glob("*.json"))
    if not record_files:
        print("ERROR: no ledger record files found")
        return 2

    compromised = False
    all_record_hashes = []
    previous_record_hash = None
    previous_record_file = None
    expected_index = 1

    print("MNEMOSYNE LEDGER VERIFIER V4")
    print(f"Vault:       {vault_dir.resolve()}")
    print(f"Public key:  {public_key_path.resolve()}")
    print(f"Fingerprint: {expected_pub_fpr}")
    print(f"Records:     {len(record_files)}")
    print("-" * 60)

    for record_path in record_files:
        record_errors = []
        try:
            record = read_json(record_path)
        except Exception as e:
            print(f"[FAIL] {record_path.name} -> unreadable_json:{e}")
            compromised = True
            continue

        signature_block = record.get("signature", {})
        record_pub_fpr = signature_block.get("public_key_fingerprint_sha256")
        if record_pub_fpr != expected_pub_fpr:
            record_errors.append(
                f"public_key_fingerprint_mismatch: record={record_pub_fpr} expected={expected_pub_fpr}"
            )

        record_errors.extend(verify_record_signature(record, public_key))
        record_errors.extend(verify_record_hash(record))

        ledger = record.get("ledger", {})
        record_index = ledger.get("record_index")
        prev_hash_declared = ledger.get("previous_record_hash")
        prev_file_declared = ledger.get("previous_record_file")
        declared_record_hash = ledger.get("record_hash")

        if record_index != expected_index:
            record_errors.append(
                f"record_index_gap_or_reorder: declared={record_index} expected={expected_index}"
            )

        if prev_hash_declared != previous_record_hash:
            record_errors.append(
                f"previous_record_hash_mismatch: declared={prev_hash_declared} expected={previous_record_hash}"
            )

        if prev_file_declared != previous_record_file:
            record_errors.append(
                f"previous_record_file_mismatch: declared={prev_file_declared} expected={previous_record_file}"
            )

        if record_errors:
            compromised = True
            print(f"[FAIL] {record_path.name}")
            for err in record_errors:
                print(f"       - {err}")
        else:
            print(f"[ OK ] {record_path.name}")

        all_record_hashes.append(declared_record_hash)
        previous_record_hash = declared_record_hash
        previous_record_file = record_path.name
        expected_index += 1

    print("-" * 60)

    try:
        chain_state = read_json(chain_state_path)
    except Exception as e:
        print(f"[FAIL] chain_state.json unreadable -> {e}")
        compromised = True
        chain_state = None

    if chain_state:
        expected_count = len(record_files)
        if chain_state.get("record_count") != expected_count:
            compromised = True
            print(
                f"[FAIL] chain_state.record_count mismatch: "
                f"{chain_state.get('record_count')} != {expected_count}"
            )
        else:
            print("[ OK ] chain_state.record_count")

        if chain_state.get("last_record_hash") != previous_record_hash:
            compromised = True
            print(
                f"[FAIL] chain_state.last_record_hash mismatch: "
                f"{chain_state.get('last_record_hash')} != {previous_record_hash}"
            )
        else:
            print("[ OK ] chain_state.last_record_hash")

        if chain_state.get("last_record_file") != previous_record_file:
            compromised = True
            print(
                f"[FAIL] chain_state.last_record_file mismatch: "
                f"{chain_state.get('last_record_file')} != {previous_record_file}"
            )
        else:
            print("[ OK ] chain_state.last_record_file")

    try:
        merkle_state = read_json(merkle_roots_path)
    except Exception as e:
        print(f"[FAIL] merkle_roots.json unreadable -> {e}")
        compromised = True
        merkle_state = None

    calculated_merkle_root = compute_merkle_root(all_record_hashes)

    if merkle_state:
        stored_hashes = merkle_state.get("record_hashes", [])
        stored_root = merkle_state.get("merkle_root")

        if stored_hashes != all_record_hashes:
            compromised = True
            print("[FAIL] merkle_roots.record_hashes mismatch")
        else:
            print("[ OK ] merkle_roots.record_hashes")

        if stored_root != calculated_merkle_root:
            compromised = True
            print(
                f"[FAIL] merkle_root mismatch: stored={stored_root} calculated={calculated_merkle_root}"
            )
        else:
            print("[ OK ] merkle_root")

    print("-" * 60)
    print(f"Calculated Merkle Root: {calculated_merkle_root}")

    if compromised:
        print("ZİNCİR KIRILDI — CHAIN COMPROMISED")
        return 1

    print("LEDGER VERIFIED — CHAIN INTACT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
