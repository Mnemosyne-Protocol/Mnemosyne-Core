"""
ledger-service — Mnemosyne FAZ 9A Append-Only Ledger
=====================================================
Mnemosyne v3.0.0 · DOI: 10.5281/zenodo.18884426

Internal service — NOT exposed to host.
Accessible only via mnemosyne-net bridge (from gate-api).

Responsibilities:
  - Receive approved gate decisions (ψ=1).
  - Sign each record with Ed25519.
  - Append to a hash-chained JSONL ledger.
  - Return record_id to gate-api.

Chain integrity: each record includes prev_hash = KS-SHA256 of the previous
record's canonical JSON. Tampering with any record breaks the chain.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# ─── Constants ────────────────────────────────────────────────────────────────

KS_SEED: bytes = b"MNEMOSYNE-KS-V3"
LEDGER_FILE = Path("/tmp/mnemosyne_ledger.jsonl")
GENESIS_HASH = "0" * 64  # Chain genesis

logging.basicConfig(level=logging.INFO, format="%(asctime)s [ledger] %(levelname)s %(message)s")
logger = logging.getLogger("mnemosyne.ledger")


# ─── KS Hashing ──────────────────────────────────────────────────────────────

def ks_sha256(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(KS_SEED)
    h.update(data)
    return h.hexdigest()


# ─── Ed25519 Key Management ───────────────────────────────────────────────────

def _generate_or_load_key() -> Ed25519PrivateKey:
    key_path = Path("/tmp/ledger_ed25519.pem")
    if key_path.exists():
        pem = key_path.read_bytes()
        return serialization.load_pem_private_key(pem, password=None)

    key = Ed25519PrivateKey.generate()
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    key_path.write_bytes(pem)
    logger.info("Generated new Ed25519 keypair at %s", key_path)
    return key


_SIGNING_KEY: Ed25519PrivateKey = _generate_or_load_key()
_PUBLIC_KEY_HEX: str = _SIGNING_KEY.public_key().public_bytes(
    serialization.Encoding.Raw,
    serialization.PublicFormat.Raw,
).hex()


def sign_payload(canonical_bytes: bytes) -> str:
    """Ed25519 sign. Returns 128-char hex (64-byte signature)."""
    sig = _SIGNING_KEY.sign(canonical_bytes)
    return sig.hex()


# ─── Ledger State ─────────────────────────────────────────────────────────────

def _load_ledger() -> list[dict]:
    if not LEDGER_FILE.exists():
        return []
    records = []
    for line in LEDGER_FILE.read_text().splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def _get_prev_hash() -> str:
    records = _load_ledger()
    if not records:
        return GENESIS_HASH
    last = records[-1]
    canonical = json.dumps(last, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return ks_sha256(canonical)


def _append_record(record: dict) -> None:
    LEDGER_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER_FILE, "a") as f:
        f.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")


# ─── Pydantic Models ──────────────────────────────────────────────────────────

class LedgerRecordRequest(BaseModel):
    asset_id: str
    verdict: str
    psi: int
    hash_canonical: str
    hash_ks: str
    gate_version: str
    policy_pack_version: str
    benchmark_run_id: str
    timestamp_utc: str


class LedgerRecordResponse(BaseModel):
    record_id: str
    prev_hash: str
    record_hash: str
    signature_hex: str
    public_key_hex: str
    ledger_height: int


# ─── FastAPI App ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="Mnemosyne Ledger Service",
    description="FAZ 9A internal ledger — hash-chained, Ed25519-signed",
    version="3.0.0",
)


@app.get("/health")
async def health() -> dict:
    records = _load_ledger()
    return {
        "status": "healthy",
        "service": "ledger-service",
        "ledger_height": len(records),
        "public_key_hex": _PUBLIC_KEY_HEX[:16] + "...",
    }


@app.post("/record", response_model=LedgerRecordResponse)
async def append_record(req: LedgerRecordRequest) -> LedgerRecordResponse:
    """
    Append a gate-approved record to the hash-chained ledger.
    Signs the canonical record with Ed25519.
    Fail-closed: any exception → 503.
    """
    record_id = str(uuid.uuid4())
    prev_hash = _get_prev_hash()
    timestamp = datetime.now(timezone.utc).isoformat()

    record = {
        "record_id": record_id,
        "prev_hash": prev_hash,
        "asset_id": req.asset_id,
        "verdict": req.verdict,
        "psi": req.psi,
        "hash_canonical": req.hash_canonical,
        "hash_ks": req.hash_ks,
        "gate_version": req.gate_version,
        "policy_pack_version": req.policy_pack_version,
        "benchmark_run_id": req.benchmark_run_id,
        "timestamp_utc": timestamp,
        "ledger_schema": "mnemosyne.ledger.v1",
    }

    # Canonical bytes for signing and chain hash
    canonical_bytes = json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
    record_hash = ks_sha256(canonical_bytes)
    signature_hex = sign_payload(canonical_bytes)

    record["record_hash"] = record_hash
    record["signature_hex"] = signature_hex
    record["public_key_hex"] = _PUBLIC_KEY_HEX

    try:
        _append_record(record)
    except Exception as exc:
        logger.error("LEDGER APPEND FAILED record_id=%s error=%s", record_id, exc)
        raise HTTPException(status_code=503, detail=f"Ledger append failed: {exc}")

    ledger_height = len(_load_ledger())
    logger.info("LEDGER record_id=%s asset_id=%s height=%d prev=%s...",
                record_id, req.asset_id, ledger_height, prev_hash[:16])

    return LedgerRecordResponse(
        record_id=record_id,
        prev_hash=prev_hash,
        record_hash=record_hash,
        signature_hex=signature_hex,
        public_key_hex=_PUBLIC_KEY_HEX,
        ledger_height=ledger_height,
    )


@app.get("/chain")
async def get_chain() -> dict:
    """Return the full ledger chain for audit."""
    records = _load_ledger()
    return {
        "ledger_height": len(records),
        "genesis_hash": GENESIS_HASH,
        "public_key_hex": _PUBLIC_KEY_HEX,
        "records": records,
    }


@app.get("/verify-chain")
async def verify_chain() -> dict:
    """Verify hash-chain integrity — each record's prev_hash must match KS-SHA256 of previous."""
    records = _load_ledger()
    if not records:
        return {"valid": True, "height": 0, "message": "Empty ledger"}

    errors = []
    expected_prev = GENESIS_HASH

    for i, record in enumerate(records):
        actual_prev = record.get("prev_hash", "")
        if actual_prev != expected_prev:
            errors.append({"index": i, "record_id": record.get("record_id"),
                           "expected": expected_prev[:16], "actual": actual_prev[:16]})

        # Recompute record hash (exclude record_hash and signature_hex for canonical form)
        r_copy = {k: v for k, v in record.items()
                  if k not in ("record_hash", "signature_hex", "public_key_hex")}
        canonical = json.dumps(r_copy, sort_keys=True, separators=(",", ":")).encode("utf-8")
        expected_prev = ks_sha256(canonical)

    return {
        "valid": len(errors) == 0,
        "height": len(records),
        "errors": errors,
    }
