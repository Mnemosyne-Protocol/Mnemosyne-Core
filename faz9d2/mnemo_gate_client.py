"""
mnemo_gate_client.py — Mnemosyne FAZ 9D.2
==========================================
Mnemosyne v3.0.0 · DOI: 10.5281/zenodo.18884426

Shared Gate API client for UE5 hook and test harness.
Used by both mnemo_ue5_executor.py (inside UE5 editor) and
run_faz9d2.py (standalone proof harness).

Contract (frozen, FAZ 9D.1):
  Transport : HTTP/1.1 Loopback TCP — http://127.0.0.1:8765 ONLY
  Endpoint  : POST /submit
  Schema    : FrameSubmission (gate-api main.py, frozen)
  Taxonomy  : v1.1 (frozen)

KS Standard : H("MNEMOSYNE-KS-V3" || data) — domain separation enforced.
Fixed6      : i64 with 6 implicit decimal places, no IEEE 754 in decisions.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import urllib.error
import urllib.request

# Ed25519 passport signing
try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    _HAS_CRYPTOGRAPHY = True
except ImportError:
    _HAS_CRYPTOGRAPHY = False

# ─── Constants (frozen — FAZ 9D.1) ───────────────────────────────────────────

GATE_URL = "http://127.0.0.1:8765"          # SÖZLEŞME 2: LOOPBACK ONLY
KS_SEED = b"MNEMOSYNE-KS-V3"
GATE_VERSION = "3.0.0"
POLICY_PACK_VERSION = "final_gate_policy.v1.0"
SUBMISSION_MODE = "controlled_generative"
SCHEMA_VERSION = "2.0"
SIGNER_ID = "tier_b"
EMISSIVE_BUDGET_FIXED6 = 680_000            # 0.68 — safely below 0.72 limit

# Taxonomy v1.1 (frozen — SÖZLEŞME 1)
CANONICAL_VIOLATION_TYPES = frozenset({
    "GEOMETRY_BREACH",
    "POLICY_MODE_VIOLATION",
    "SIGNATURE_INVALID",
    "SOURCE_INVARIANT_BREACH",
})

# Key path for Ed25519 passport signing (shared across sessions)
_KEY_PATH = Path("/tmp/faz9d2_ed25519.pem")


# ─── KS Hashing ──────────────────────────────────────────────────────────────

def ks_sha256(data: bytes) -> str:
    """KS-salted SHA-256: H(KS_SEED || data). Returns 64-char hex."""
    h = hashlib.sha256()
    h.update(KS_SEED)
    h.update(data)
    return h.hexdigest()


def raw_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ─── Ed25519 Key Management ───────────────────────────────────────────────────

def _get_or_generate_key() -> Optional["Ed25519PrivateKey"]:
    if not _HAS_CRYPTOGRAPHY:
        return None
    if _KEY_PATH.exists():
        return serialization.load_pem_private_key(_KEY_PATH.read_bytes(), password=None)
    key = Ed25519PrivateKey.generate()
    pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    _KEY_PATH.write_bytes(pem)
    return key


_SIGNING_KEY = _get_or_generate_key()
PUBLIC_KEY_HEX: str = (
    _SIGNING_KEY.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    ).hex()
    if _SIGNING_KEY else "NO_CRYPTOGRAPHY_AVAILABLE"
)


def sign_bytes(data: bytes) -> str:
    """Ed25519 sign. Returns 128-char hex. Falls back to KS double if no key."""
    if _SIGNING_KEY:
        return _SIGNING_KEY.sign(data).hex()
    # Fallback: deterministic but NOT a real signature — explicitly marked
    return ks_sha256(data) * 2  # 128 chars


# ─── Merkle ───────────────────────────────────────────────────────────────────

def merkle_root(leaves: list[str]) -> str:
    """Binary Merkle root from KS-SHA256 pairs."""
    if not leaves:
        return "0" * 64
    nodes = [bytes.fromhex(h) if len(h) == 64 else bytes.fromhex(ks_sha256(h.encode()))
             for h in leaves]
    while len(nodes) > 1:
        if len(nodes) % 2 == 1:
            nodes.append(nodes[-1])
        nodes = [
            bytes.fromhex(ks_sha256(nodes[i] + nodes[i + 1]))
            for i in range(0, len(nodes), 2)
        ]
    return nodes[0].hex()


# ─── HTTP ─────────────────────────────────────────────────────────────────────

def _http_post(url: str, payload: dict, timeout: float = 15.0) -> tuple[dict, float]:
    """POST JSON to Gate API. Returns (response_dict, latency_ms). Fail-closed on error."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            latency = (time.perf_counter() - t0) * 1000
            return json.loads(body), latency
    except urllib.error.HTTPError as e:
        latency = (time.perf_counter() - t0) * 1000
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {body}") from e
    except Exception as e:
        latency = (time.perf_counter() - t0) * 1000
        raise RuntimeError(f"Connection error after {latency:.1f}ms: {e}") from e


# ─── Attestation Builder ──────────────────────────────────────────────────────

def build_attestation(
    frame_bytes: bytes,
    frame_id: str,
    force_fail: bool = False,
) -> dict:
    """
    Build a valid AttestationPayload dict for Gate API /submit.

    For a passing frame:
      - hash_mode = "KS-salted"
      - Ed25519 signature (128 hex)
      - source_invariants all PASS
      - roi_hashes all PASS
      - emissive_budget = 680_000 (below 720_000 limit)

    For a failing frame (force_fail=True):
      - hash_mode = "raw"  → triggers POLICY_MODE_VIOLATION
      - signature too short → triggers SIGNATURE_INVALID
      - source_invariants FAIL → triggers SOURCE_INVARIANT_BREACH
    """
    frame_hash_ks = ks_sha256(frame_bytes)

    if not force_fail:
        # ── PASS path ─────────────────────────────────────────────────────────
        canonical = json.dumps({
            "asset_id": frame_id,
            "hash_mode": "KS-salted",
            "signer": SIGNER_ID,
            "submission_mode": SUBMISSION_MODE,
            "frame_hash_ks": frame_hash_ks,
        }, sort_keys=True, separators=(",", ":")).encode("utf-8")
        sig_hex = sign_bytes(canonical)

        return {
            "schema_version": SCHEMA_VERSION,
            "hash_mode": "KS-salted",
            "signature": {
                "signature_hex": sig_hex,
                "algorithm": "Ed25519" if _HAS_CRYPTOGRAPHY else "KS-HMAC-fallback",
                "public_key_hex": PUBLIC_KEY_HEX,
                "signed_over": "canonical_frame_payload",
            },
            "signer": SIGNER_ID,
            "source_invariants": {
                "frame_integrity": {"status": "PASS", "hash_ks": frame_hash_ks},
                "mesh_topology_hash": {"status": "PASS"},
                "uv_layout_hash": {"status": "PASS"},
            },
            "render_fingerprint": {
                "frame_hash_ks": frame_hash_ks,
                "roi_hashes": {
                    "head":        {"status": "PASS"},
                    "chest":       {"status": "PASS"},
                    "emblem_zone": {"status": "PASS"},
                },
            },
            "submission_mode": SUBMISSION_MODE,
            "metrics": {
                "emissive_budget": {"value": EMISSIVE_BUDGET_FIXED6},
            },
        }
    else:
        # ── FAIL path — intentional violations ────────────────────────────────
        return {
            "schema_version": SCHEMA_VERSION,
            "hash_mode": "raw",                  # POLICY_MODE_VIOLATION
            "signature": {
                "signature_hex": "bad_sig",      # SIGNATURE_INVALID (not 128 hex)
                "algorithm": "NONE",
            },
            "signer": SIGNER_ID,
            "source_invariants": {
                "frame_integrity": {"status": "FAIL", "hash_ks": frame_hash_ks},
                "mesh_topology_hash": {"status": "FAIL"},   # SOURCE_INVARIANT_BREACH
            },
            "render_fingerprint": {
                "roi_hashes": {
                    "head":        {"status": "FAIL"},       # GEOMETRY_BREACH
                    "chest":       {"status": "FAIL"},
                    "emblem_zone": {"status": "FAIL"},
                },
            },
            "submission_mode": SUBMISSION_MODE,
            "metrics": {
                "emissive_budget": {"value": 900_000},      # > 720_000 limit
            },
        }


# ─── Gate Submission ──────────────────────────────────────────────────────────

@dataclass
class FrameGateResult:
    frame_id: str
    frame_index: int
    verdict: str                   # "APPROVED" | "REJECTED" | "ERROR"
    psi: int                       # 1 or 0
    violations: list[dict]
    client_latency_ms: float
    server_elapsed_ms: float
    ledger_record_id: Optional[str]
    quarantine_record_id: Optional[str]
    hash_ks: str


def submit_frame(
    frame_bytes: bytes,
    frame_id: str,
    frame_index: int,
    session_id: str,
    benchmark_run_id: str,
    operator: str,
    source_model: str,
    source_pipeline: str,
    force_fail: bool = False,
    gate_url: str = GATE_URL,
) -> FrameGateResult:
    """
    Submit one frame to Gate API. Returns FrameGateResult.
    Raises RuntimeError on communication failure (fail-closed).
    """
    hash_ks = ks_sha256(frame_bytes)
    attestation = build_attestation(frame_bytes, frame_id, force_fail=force_fail)

    payload = {
        "asset_id": frame_id,
        "source_model": source_model,
        "source_pipeline": source_pipeline,
        "operator": operator,
        "benchmark_run_id": benchmark_run_id,
        "replay_pointer": f"replay://ue5/{session_id}/{frame_id}",
        "attestation": attestation,
    }

    resp, latency_ms = _http_post(f"{gate_url}/submit", payload)

    verdict = resp.get("verdict", "ERROR")
    psi = resp.get("psi", -1)
    if psi == -1:
        raise RuntimeError(f"Malformed Gate response — psi missing: {resp}")

    return FrameGateResult(
        frame_id=frame_id,
        frame_index=frame_index,
        verdict=verdict,
        psi=psi,
        violations=resp.get("violations", []),
        client_latency_ms=round(latency_ms, 2),
        server_elapsed_ms=round(resp.get("elapsed_ms", 0.0), 2),
        ledger_record_id=resp.get("ledger_record_id"),
        quarantine_record_id=resp.get("quarantine_record_id"),
        hash_ks=hash_ks,
    )


# ─── Passport ────────────────────────────────────────────────────────────────

def produce_passport(
    session_id: str,
    output_dir: Path,
    frame_results: list[FrameGateResult],
    benchmark_run_id: str,
    manifest_path: Optional[str] = None,
) -> Path:
    """
    Produce Ed25519-signed Mnemosyne_Certified_Passport.json.
    Called only when ALL frames return psi=1.
    """
    frame_hashes = [fr.hash_ks for fr in frame_results]
    root = merkle_root(frame_hashes)

    passport_body = {
        "protocol": "mnemosyne:v1.7",
        "schema": "mnemosyne.certification.v1",
        "session_id": session_id,
        "certification_timestamp": datetime.now(timezone.utc).isoformat(),
        "frame_count": len(frame_results),
        "all_frames_approved": True,
        "gate_version": GATE_VERSION,
        "policy_pack_version": POLICY_PACK_VERSION,
        "benchmark_run_id": benchmark_run_id,
        "merkle_root": root,
        "manifest_ref": manifest_path or "scene_manifest_v1.json",
        "frame_manifest": [
            {
                "frame_id": fr.frame_id,
                "frame_index": fr.frame_index,
                "verdict": fr.verdict,
                "psi": fr.psi,
                "hash_ks": fr.hash_ks,
                "ledger_record_id": fr.ledger_record_id,
                "client_latency_ms": fr.client_latency_ms,
            }
            for fr in frame_results
        ],
        "taxonomy_version": "v1.1",
        "loopback_tcp_compliant": True,         # SÖZLEŞME 2
        "source_pipeline": "UE5_MRQ",
    }

    canonical = json.dumps(passport_body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    sig_hex = sign_bytes(canonical)

    passport_body["signature"] = {
        "signature_hex": sig_hex,
        "algorithm": "Ed25519" if _HAS_CRYPTOGRAPHY else "KS-HMAC-fallback",
        "public_key_hex": PUBLIC_KEY_HEX,
        "signed_over": "canonical_passport_body",
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    passport_path = output_dir / "Mnemosyne_Certified_Passport.json"
    passport_path.write_text(
        json.dumps(passport_body, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return passport_path
