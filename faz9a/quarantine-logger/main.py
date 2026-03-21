"""
quarantine-logger — Mnemosyne FAZ 9A Quarantine Record Writer
=============================================================
Mnemosyne v3.0.0 · DOI: 10.5281/zenodo.18884426

Internal service — NOT exposed to host.
Accessible only via mnemosyne-net bridge (from gate-api).

Responsibilities:
  - POST /quarantine : Validate Quarantine Schema v1.1, write JSON to /quarantine volume.
  - GET  /records    : List quarantine records.

Schema v1.1 (strict enforcement — invalid input raises exception, no record written):
  asset_id            str   (non-empty)
  timestamp_utc       str   (ISO 8601)
  source_model        str   (non-empty)
  source_pipeline     str   (non-empty)
  violation_type      str   (non-empty)
  decision_reason     str   (non-empty)
  psi                 int   (must be 0 — QUARANTINE requires ψ=0)
  hash_canonical      str   (64 hex chars)
  hash_ks             str   (64 hex chars, must differ from hash_canonical)
  policy_pack_version str   (non-empty)
  gate_version        str   (non-empty)
  benchmark_run_id    str   (non-empty)
  replay_pointer      str   (non-empty)
  operator            str   (non-empty)
  admission_decision  str   (must be exactly "QUARANTINE")
"""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator, model_validator

# ─── Constants ────────────────────────────────────────────────────────────────

QUARANTINE_DIR = Path(os.getenv("QUARANTINE_DIR", "/quarantine"))
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
ISO8601_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

# SÖZLEŞME 1: Canonical violation_type taxonomy v1.1 (frozen)
CANONICAL_VIOLATION_TYPES = frozenset({
    "GEOMETRY_BREACH",
    "POLICY_MODE_VIOLATION",
    "SIGNATURE_INVALID",
    "SOURCE_INVARIANT_BREACH",
})

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [quarantine] %(levelname)s %(message)s")
logger = logging.getLogger("mnemosyne.quarantine")


# ─── Schema v1.1 Model ────────────────────────────────────────────────────────

class QuarantineRecord(BaseModel):
    """
    Quarantine Schema v1.1 — strict enforcement.
    Invalid input raises ValueError; no partial writes are allowed.
    """
    asset_id: str
    timestamp_utc: str
    source_model: str
    source_pipeline: str
    violation_type: str
    decision_reason: str
    psi: int
    hash_canonical: str
    hash_ks: str
    policy_pack_version: str
    gate_version: str
    benchmark_run_id: str
    replay_pointer: str
    operator: str
    admission_decision: str

    @field_validator("violation_type")
    @classmethod
    def must_be_canonical_taxonomy(cls, v: str) -> str:
        """SÖZLEŞME 1: violation_type MUST be a canonical taxonomy value."""
        if v not in CANONICAL_VIOLATION_TYPES:
            raise ValueError(
                f"violation_type must be one of {sorted(CANONICAL_VIOLATION_TYPES)}, got: {v!r}. "
                f"Apply taxonomy mapping in gate-api before submitting to quarantine-logger."
            )
        return v

    @field_validator("asset_id", "source_model", "source_pipeline", "violation_type",
                     "decision_reason", "policy_pack_version", "gate_version",
                     "benchmark_run_id", "replay_pointer", "operator")
    @classmethod
    def must_be_nonempty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError(f"field must not be empty, got: {v!r}")
        return v

    @field_validator("timestamp_utc")
    @classmethod
    def must_be_iso8601(cls, v: str) -> str:
        if not ISO8601_RE.match(v):
            raise ValueError(f"timestamp_utc must be ISO 8601, got: {v!r}")
        return v

    @field_validator("psi")
    @classmethod
    def psi_must_be_zero(cls, v: int) -> int:
        if v != 0:
            raise ValueError(f"QUARANTINE requires psi=0, got psi={v}")
        return v

    @field_validator("hash_canonical", "hash_ks")
    @classmethod
    def must_be_64hex(cls, v: str) -> str:
        if not HEX64_RE.match(v):
            raise ValueError(f"hash must be 64 lowercase hex chars, got: {v!r}")
        return v

    @field_validator("admission_decision")
    @classmethod
    def must_be_quarantine(cls, v: str) -> str:
        if v != "QUARANTINE":
            raise ValueError(f"admission_decision must be 'QUARANTINE', got: {v!r}")
        return v

    @model_validator(mode="after")
    def hashes_must_differ(self) -> "QuarantineRecord":
        """KS domain separation: hash_ks MUST differ from hash_canonical."""
        if self.hash_ks == self.hash_canonical:
            raise ValueError(
                "KS domain separation violation: hash_ks == hash_canonical. "
                "KS-salted hash must always differ from raw hash."
            )
        return self


# ─── FastAPI App ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="Mnemosyne Quarantine Logger",
    description="FAZ 9A internal — schema v1.1 enforced quarantine records",
    version="3.0.0",
)


@app.get("/health")
async def health() -> dict:
    records = list(QUARANTINE_DIR.glob("quarantine_*.json")) if QUARANTINE_DIR.exists() else []
    return {
        "status": "healthy",
        "service": "quarantine-logger",
        "quarantine_dir": str(QUARANTINE_DIR),
        "record_count": len(records),
    }


@app.post("/quarantine")
async def write_quarantine(record: QuarantineRecord) -> dict:
    """
    Validate Quarantine Schema v1.1 and write to disk.

    Pydantic validation is strict — if ANY field fails schema v1.1,
    a ValueError is raised and NO file is written (fail-closed contract).
    """
    record_id = str(uuid.uuid4())
    record_data = record.model_dump()
    record_data["record_id"] = record_id
    record_data["logged_at"] = datetime.now(timezone.utc).isoformat()
    record_data["schema_version"] = "quarantine.v1.1"

    if not QUARANTINE_DIR.exists():
        QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"quarantine_{record.asset_id}_{record_id[:8]}.json"
    filepath = QUARANTINE_DIR / filename

    try:
        filepath.write_text(
            json.dumps(record_data, indent=2, sort_keys=True, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError as exc:
        logger.error("QUARANTINE WRITE FAILED record_id=%s error=%s", record_id, exc)
        raise HTTPException(status_code=503, detail=f"Disk write failed: {exc}")

    logger.info("QUARANTINE record_id=%s asset_id=%s violation=%s file=%s",
                record_id, record.asset_id, record.violation_type, filename)

    return {
        "record_id": record_id,
        "filename": filename,
        "admission_decision": "QUARANTINE",
        "psi": 0,
    }


@app.get("/records")
async def list_records() -> dict:
    """List all quarantine records on disk."""
    if not QUARANTINE_DIR.exists():
        return {"count": 0, "records": []}

    files = sorted(QUARANTINE_DIR.glob("quarantine_*.json"))
    records = []
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            records.append({
                "record_id": data.get("record_id"),
                "asset_id": data.get("asset_id"),
                "violation_type": data.get("violation_type"),
                "timestamp_utc": data.get("timestamp_utc"),
                "admission_decision": data.get("admission_decision"),
            })
        except Exception as exc:
            records.append({"error": str(exc), "file": f.name})

    return {"count": len(records), "records": records}


@app.get("/records/{record_id}")
async def get_record(record_id: str) -> dict:
    """Retrieve a specific quarantine record by record_id prefix."""
    if not QUARANTINE_DIR.exists():
        raise HTTPException(status_code=404, detail="Quarantine directory not found")

    for f in QUARANTINE_DIR.glob("quarantine_*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if data.get("record_id", "").startswith(record_id):
                return data
        except Exception:
            continue

    raise HTTPException(status_code=404, detail=f"Record not found: {record_id}")
