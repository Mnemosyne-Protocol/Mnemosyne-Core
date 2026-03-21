"""
gate-api — Mnemosyne FAZ 9A Control Plane Entry Point
======================================================
Mnemosyne v3.0.0 · DOI: 10.5281/zenodo.18884426

Topology  : Dockerized, exposed ONLY on 127.0.0.1:8765 (loopback TCP).
Role      : Receives frame submissions from the host pipeline, runs the
            Mnemosyne gate evaluation, and routes to internal services.

Gate contract (fail-closed):
  ψ = 1 → POST /record  to ledger-service   (Ed25519-signed ledger entry)
  ψ = 0 → POST /quarantine to quarantine-logger (schema v1.1 enforced)
  Error  → 503 REJECT  (fail-closed; asset never enters production)

KS Standard : H("MNEMOSYNE-KS-V3" || data)  — domain separation enforced.
Fixed6      : i64 with 6 implicit decimal places, no IEEE 754 in decisions.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator

# ─── Constants ───────────────────────────────────────────────────────────────

KS_SEED: bytes = b"MNEMOSYNE-KS-V3"
FIXED6_SCALE: int = 1_000_000

GATE_VERSION: str = os.getenv("GATE_VERSION", "3.0.0")
POLICY_PACK_VERSION: str = os.getenv("POLICY_PACK_VERSION", "final_gate_policy.v1.0")
LEDGER_URL: str = os.getenv("LEDGER_URL", "http://ledger-service:8766")
QUARANTINE_URL: str = os.getenv("QUARANTINE_URL", "http://quarantine-logger:8768")
ATTESTATION_URL: str = os.getenv("ATTESTATION_URL", "http://attestation-service:8767")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [gate-api] %(levelname)s %(message)s")
logger = logging.getLogger("mnemosyne.gate_api")

# ─── SÖZLEŞME 1: Violation Taxonomy v1.1 ─────────────────────────────────────
# Canonical violation_type values for quarantine records.
# All internal invariant names are mapped to these 4 categories.

CANONICAL_VIOLATION_TYPES = frozenset({
    "GEOMETRY_BREACH",
    "POLICY_MODE_VIOLATION",
    "SIGNATURE_INVALID",
    "SOURCE_INVARIANT_BREACH",
})

_TAXONOMY_MAP: dict[str, str] = {
    "ks_mode":                "POLICY_MODE_VIOLATION",
    "ks_domain_separation":   "POLICY_MODE_VIOLATION",
    "emissive_budget":        "POLICY_MODE_VIOLATION",
    "schema":                 "SIGNATURE_INVALID",
    "signature":              "SIGNATURE_INVALID",
}


def apply_taxonomy(invariant: str) -> str:
    """Map internal invariant name → canonical violation_type (v1.1)."""
    if invariant in _TAXONOMY_MAP:
        return _TAXONOMY_MAP[invariant]
    if invariant.startswith("source_invariant"):
        return "SOURCE_INVARIANT_BREACH"
    if invariant.startswith("roi"):
        return "GEOMETRY_BREACH"
    return "POLICY_MODE_VIOLATION"   # fail-safe default


# ─── KS Hashing ──────────────────────────────────────────────────────────────

def ks_sha256(data: bytes) -> str:
    """KS-salted SHA-256: H(KS_SEED || data). Returns 64-char hex."""
    h = hashlib.sha256()
    h.update(KS_SEED)
    h.update(data)
    return h.hexdigest()


def raw_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ─── Fixed6 ──────────────────────────────────────────────────────────────────

def float_to_fixed6(value: float) -> int:
    """Convert float to Fixed6 i64.  Overflow → raises OverflowError (REJECT)."""
    result = int(round(value * FIXED6_SCALE))
    if abs(result) > 9_223_372_036_854_775_807:
        raise OverflowError(f"Fixed6 overflow: {value}")
    return result


def fixed6_mul(a: int, b: int) -> int:
    """Fixed6 multiplication via i128 intermediates. Overflow → REJECT."""
    result = (a * b) // FIXED6_SCALE   # Simulated i128 intermediate via Python's arbitrary int
    if abs(result) > 9_223_372_036_854_775_807:
        raise OverflowError(f"Fixed6 mul overflow: {a} * {b}")
    return result


# ─── Verdict ─────────────────────────────────────────────────────────────────

class Verdict(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    QUARANTINED = "QUARANTINED"


# ─── Pydantic Models ─────────────────────────────────────────────────────────

class AttestationPayload(BaseModel):
    schema_version: str
    hash_mode: str
    signature: dict
    signer: str
    source_invariants: dict
    render_fingerprint: dict
    submission_mode: Optional[str] = "controlled_generative"
    spec_refs: Optional[dict] = None
    metrics: Optional[dict] = None


class FrameSubmission(BaseModel):
    asset_id: str
    source_model: str
    source_pipeline: str
    operator: str
    attestation: AttestationPayload
    benchmark_run_id: Optional[str] = None
    replay_pointer: Optional[str] = None

    @field_validator("asset_id")
    @classmethod
    def asset_id_nonempty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("asset_id must not be empty")
        return v


class GateResponse(BaseModel):
    asset_id: str
    verdict: str
    psi: int
    gate_version: str
    policy_pack_version: str
    elapsed_ms: float
    violations: list[dict]
    ledger_record_id: Optional[str] = None
    quarantine_record_id: Optional[str] = None


# ─── Gate Evaluation ─────────────────────────────────────────────────────────

def evaluate_gate(submission: FrameSubmission) -> tuple[Verdict, list[dict], str, str]:
    """
    Fail-closed gate evaluation.

    Returns (verdict, violations, hash_canonical, hash_ks).

    ψ = ⋀ᵢ Iᵢ(x)  — Boolean conjunction; one failure → total rejection.
    No short-circuit: all invariants checked; full violation vector returned.
    """
    att = submission.attestation
    violations: list[dict] = []
    psi = 1

    # Step 1: Schema — required fields present
    required = ["schema_version", "hash_mode", "signature", "signer",
                "source_invariants", "render_fingerprint"]
    att_dict = att.model_dump()
    missing = [k for k in required if not att_dict.get(k)]
    if missing:
        violations.append({"invariant": "schema", "detail": f"missing fields: {missing}"})
        psi = 0

    # Step 2: KS hash mode enforced
    if att.hash_mode != "KS-salted":
        violations.append({"invariant": "ks_mode",
                           "detail": f"non-KS hash mode: '{att.hash_mode}'"})
        psi = 0

    # Step 3: Signature structure — Ed25519 = 128 hex chars
    sig = att.signature
    sig_hex = sig.get("signature_hex", sig.get("ed25519_signature", ""))
    if not isinstance(sig_hex, str) or len(sig_hex) != 128:
        violations.append({"invariant": "signature",
                           "detail": f"invalid Ed25519 format: expected 128 hex chars"})
        psi = 0

    # Step 4: Source invariants — all required to PASS
    for inv_name, inv_val in att.source_invariants.items():
        status = (inv_val.get("status") if isinstance(inv_val, dict) else inv_val)
        if status not in ("PASS", "EXACT_MATCH", True, "true"):
            violations.append({"invariant": f"source_invariant.{inv_name}",
                               "detail": f"status={status}"})
            psi = 0

    # Step 5: Render fingerprint — ROI hashes must PASS
    fp = att.render_fingerprint
    roi = fp.get("roi_hashes", {})
    for region, val in roi.items():
        status = (val.get("status") if isinstance(val, dict) else val)
        if status not in ("PASS", "EXACT_MATCH", True):
            violations.append({"invariant": f"roi.{region}", "detail": f"status={status}"})
            psi = 0

    # Step 6: Fixed6 threshold checks on metrics (if provided)
    metrics = att.metrics or {}
    for key, val in metrics.items():
        if not isinstance(val, dict):
            continue
        raw = val.get("value")
        if raw is None:
            continue
        try:
            measured = int(raw) if isinstance(raw, int) else float_to_fixed6(float(raw))
            # Emissive budget hard limit: 720_000 (0.72 in Fixed6)
            if key == "emissive_budget" and measured > 720_000:
                violations.append({"invariant": "emissive_budget",
                                   "detail": f"Fixed6 {measured} > 720000"})
                psi = 0
        except (OverflowError, ValueError) as e:
            violations.append({"invariant": key, "detail": f"Fixed6 error: {e}"})
            psi = 0

    # Canonical payload for hash binding
    canonical_payload = json.dumps(
        {
            "asset_id": submission.asset_id,
            "schema_version": att.schema_version,
            "hash_mode": att.hash_mode,
            "signer": att.signer,
            "submission_mode": att.submission_mode,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    hash_canonical = raw_sha256(canonical_payload)
    hash_ks = ks_sha256(canonical_payload)

    # Enforce domain separation (KS hash MUST differ from raw)
    if hash_ks == hash_canonical:
        violations.append({"invariant": "ks_domain_separation",
                           "detail": "KS hash equals raw hash — domain separation failure"})
        psi = 0

    verdict = Verdict.APPROVED if psi == 1 else Verdict.REJECTED
    return verdict, violations, hash_canonical, hash_ks


# ─── FastAPI App ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="Mnemosyne Gate API",
    description="FAZ 9A Control Plane entry point — fail-closed admission layer",
    version=GATE_VERSION,
)


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy", "service": "gate-api", "version": GATE_VERSION}


@app.post("/submit", response_model=GateResponse)
async def submit(submission: FrameSubmission) -> GateResponse:
    """
    Receive a frame submission from the host pipeline.
    Evaluate via the Mnemosyne gate, route to ledger or quarantine.
    """
    t_start = time.perf_counter()
    asset_id = submission.asset_id
    benchmark_run_id = submission.benchmark_run_id or str(uuid.uuid4())

    logger.info("SUBMIT asset_id=%s source_model=%s pipeline=%s",
                asset_id, submission.source_model, submission.source_pipeline)

    # Fail-closed: any exception during evaluation → REJECT
    try:
        verdict, violations, hash_canonical, hash_ks = evaluate_gate(submission)
    except Exception as exc:
        logger.error("GATE EXCEPTION asset_id=%s error=%s", asset_id, exc)
        raise HTTPException(status_code=503, detail=f"Gate evaluation error: {exc}")

    psi = 1 if verdict == Verdict.APPROVED else 0
    elapsed_ms = (time.perf_counter() - t_start) * 1000

    logger.info("VERDICT asset_id=%s verdict=%s psi=%d elapsed=%.2fms violations=%d",
                asset_id, verdict.value, psi, elapsed_ms, len(violations))

    ledger_record_id: Optional[str] = None
    quarantine_record_id: Optional[str] = None

    if verdict == Verdict.APPROVED:
        # ψ = 1 → signed ledger record
        ledger_payload = {
            "asset_id": asset_id,
            "verdict": verdict.value,
            "psi": psi,
            "hash_canonical": hash_canonical,
            "hash_ks": hash_ks,
            "gate_version": GATE_VERSION,
            "policy_pack_version": POLICY_PACK_VERSION,
            "benchmark_run_id": benchmark_run_id,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(f"{LEDGER_URL}/record", json=ledger_payload)
                resp.raise_for_status()
                ledger_record_id = resp.json().get("record_id")
        except Exception as exc:
            logger.error("LEDGER ERROR asset_id=%s error=%s", asset_id, exc)
            # Fail-closed: if ledger write fails, REJECT
            raise HTTPException(status_code=503,
                                detail="Ledger service unavailable — fail-closed REJECT")
    else:
        # ψ = 0 → quarantine record (schema v1.1 — canonical taxonomy)
        raw_invariant = violations[0]["invariant"] if violations else "UNKNOWN"
        # SÖZLEŞME 1: Map internal invariant name → canonical violation_type (v1.1)
        violation_type = apply_taxonomy(raw_invariant)
        decision_reason = (f"{raw_invariant}: " +
                           "; ".join(v["detail"] for v in violations)) if violations else "gate failure"

        quarantine_payload = {
            "asset_id": asset_id,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "source_model": submission.source_model,
            "source_pipeline": submission.source_pipeline,
            "violation_type": violation_type,
            "decision_reason": decision_reason,
            "psi": psi,
            "hash_canonical": hash_canonical,
            "hash_ks": hash_ks,
            "policy_pack_version": POLICY_PACK_VERSION,
            "gate_version": GATE_VERSION,
            "benchmark_run_id": benchmark_run_id,
            "replay_pointer": submission.replay_pointer or f"replay://{asset_id}",
            "operator": submission.operator,
            "admission_decision": "QUARANTINE",
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(f"{QUARANTINE_URL}/quarantine", json=quarantine_payload)
                resp.raise_for_status()
                quarantine_record_id = resp.json().get("record_id")
        except Exception as exc:
            logger.error("QUARANTINE ERROR asset_id=%s error=%s", asset_id, exc)
            # Fail-closed: quarantine write failure → still REJECT but log error
            logger.error("QUARANTINE WRITE FAILED — asset blocked regardless")

    elapsed_ms = (time.perf_counter() - t_start) * 1000

    return GateResponse(
        asset_id=asset_id,
        verdict=verdict.value,
        psi=psi,
        gate_version=GATE_VERSION,
        policy_pack_version=POLICY_PACK_VERSION,
        elapsed_ms=round(elapsed_ms, 2),
        violations=violations,
        ledger_record_id=ledger_record_id,
        quarantine_record_id=quarantine_record_id,
    )


@app.get("/self-test")
async def self_test() -> dict:
    """
    Internal self-test: runs a passing and a failing attestation through the gate.
    Verifies ψ=1 for passing, ψ=0 for failing, and KS domain separation.
    """
    results = {}

    # Test 1: Passing attestation
    passing = FrameSubmission(
        asset_id="self-test-pass-001",
        source_model="test-engine",
        source_pipeline="self-test",
        operator="self-test",
        benchmark_run_id="self-test",
        attestation=AttestationPayload(
            schema_version="2.0",
            hash_mode="KS-salted",
            signature={"signature_hex": "a" * 128, "algorithm": "Ed25519"},
            signer="tier_a",
            source_invariants={
                "mesh_topology_hash": {"status": "PASS"},
                "uv_layout_hash": {"status": "PASS"},
            },
            render_fingerprint={
                "roi_hashes": {
                    "head": {"status": "PASS"},
                    "chest": {"status": "PASS"},
                    "emblem_zone": {"status": "PASS"},
                }
            },
            submission_mode="controlled_generative",
            metrics={"emissive_budget": {"value": 680000}},
        ),
    )
    v1, violations1, hc1, hk1 = evaluate_gate(passing)
    results["pass_test"] = {
        "verdict": v1.value,
        "psi": 1 if v1 == Verdict.APPROVED else 0,
        "violations": len(violations1),
        "ks_domain_separation": hc1 != hk1,
        "ok": v1 == Verdict.APPROVED,
    }

    # Test 2: Failing attestation (missing signature, wrong hash mode)
    failing = FrameSubmission(
        asset_id="self-test-fail-001",
        source_model="test-engine",
        source_pipeline="self-test",
        operator="self-test",
        attestation=AttestationPayload(
            schema_version="2.0",
            hash_mode="raw",          # Non-KS → FAIL
            signature={"signature_hex": "bad"},  # invalid length → FAIL
            signer="tier_a",
            source_invariants={"mesh": {"status": "FAIL"}},  # invariant fail
            render_fingerprint={},
        ),
    )
    v2, violations2, _, _ = evaluate_gate(failing)
    results["fail_test"] = {
        "verdict": v2.value,
        "psi": 1 if v2 == Verdict.APPROVED else 0,
        "violations": len(violations2),
        "ok": v2 == Verdict.REJECTED,
    }

    # Test 3: KS domain separation proof
    test_data = b"mnemosyne-test-vector"
    ks_h = ks_sha256(test_data)
    raw_h = raw_sha256(test_data)
    results["ks_domain_separation"] = {
        "ks_hash": ks_h[:16] + "...",
        "raw_hash": raw_h[:16] + "...",
        "different": ks_h != raw_h,
        "ok": ks_h != raw_h,
    }

    # Test 4: Fixed6 arithmetic
    val_f6 = float_to_fixed6(0.72)
    val_mul = fixed6_mul(500_000, 500_000)  # 0.5 * 0.5 = 0.25 → 250_000
    results["fixed6"] = {
        "0.72_as_fixed6": val_f6,
        "expected": 720_000,
        "0.5x0.5_fixed6": val_mul,
        "expected_mul": 250_000,
        "ok": val_f6 == 720_000 and val_mul == 250_000,
    }

    all_ok = all(v.get("ok", False) for v in results.values())

    return {
        "status": "PASS" if all_ok else "FAIL",
        "gate_version": GATE_VERSION,
        "policy_pack_version": POLICY_PACK_VERSION,
        "tests": results,
    }
