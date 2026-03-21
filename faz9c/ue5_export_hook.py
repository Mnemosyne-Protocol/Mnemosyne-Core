"""
ue5_export_hook.py — Mnemosyne FAZ 9C
======================================
Mnemosyne v3.0.0 · DOI: 10.5281/zenodo.18884426

UE5 Post-Export Hook (SÖZLEŞME 2 compliant):
  - Reads frame JSON files from a simulated UE5 export session directory.
  - Submits each frame to Gate via LOOPBACK TCP ONLY (127.0.0.1:8765/submit).
  - UDS YOK. No external connections.

Certification Logic:
  ψ=1 for ALL frames → Mnemosyne_Certified_Passport.json (Ed25519 signed)
  Any ψ=0 frame     → FAIL-CLOSED. No certificate. Quarantine written by gate-api.

Taxonomy (SÖZLEŞME 1):
  Canonical violation_type in quarantine records:
    GEOMETRY_BREACH, POLICY_MODE_VIOLATION, SIGNATURE_INVALID, SOURCE_INVARIANT_BREACH
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import urllib.error
import urllib.request

# Ed25519 for certification passport signing
try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    _HAS_CRYPTOGRAPHY = True
except ImportError:
    _HAS_CRYPTOGRAPHY = False

GATE_URL = "http://127.0.0.1:8765"   # SÖZLEŞME 2: LOOPBACK ONLY
KS_SEED = b"MNEMOSYNE-KS-V3"
GATE_VERSION = "3.0.0"
POLICY_PACK_VERSION = "final_gate_policy.v1.0"

# SÖZLEŞME 1: Canonical violation_type taxonomy v1.1 (frozen)
CANONICAL_VIOLATION_TYPES = frozenset({
    "GEOMETRY_BREACH",
    "POLICY_MODE_VIOLATION",
    "SIGNATURE_INVALID",
    "SOURCE_INVARIANT_BREACH",
})


# ─── KS / Merkle ─────────────────────────────────────────────────────────────

def _ks_sha256(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(KS_SEED)
    h.update(data)
    return h.hexdigest()


def _merkle_root(leaves: list[str]) -> str:
    """Binary Merkle root from KS-SHA256 over frame hash pairs."""
    if not leaves:
        return "0" * 64
    nodes = [bytes.fromhex(h) if len(h) == 64 else _ks_sha256(h.encode()).encode()
             for h in leaves]
    while len(nodes) > 1:
        if len(nodes) % 2 == 1:
            nodes.append(nodes[-1])
        nodes = [
            bytes.fromhex(_ks_sha256(nodes[i] + nodes[i + 1]))
            for i in range(0, len(nodes), 2)
        ]
    return nodes[0].hex()


# ─── Ed25519 Key Management ───────────────────────────────────────────────────

def _get_or_generate_key() -> Optional["Ed25519PrivateKey"]:
    if not _HAS_CRYPTOGRAPHY:
        return None
    key_path = Path("/tmp/faz9c_ed25519.pem")
    if key_path.exists():
        return serialization.load_pem_private_key(key_path.read_bytes(), password=None)
    key = Ed25519PrivateKey.generate()
    pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    key_path.write_bytes(pem)
    return key


_SIGNING_KEY = _get_or_generate_key()
_PUBLIC_KEY_HEX: str = (
    _SIGNING_KEY.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    ).hex()
    if _SIGNING_KEY else "NO_KEY"
)


def _sign(data: bytes) -> str:
    """Ed25519 sign. Returns 128-char hex. Falls back to KS-HMAC if no key."""
    if _SIGNING_KEY:
        return _SIGNING_KEY.sign(data).hex()
    # Fallback: not a real signature, only used if cryptography is unavailable
    return _ks_sha256(data) * 2   # 128 chars, clearly not Ed25519


# ─── HTTP ─────────────────────────────────────────────────────────────────────

def _post(url: str, payload: dict, timeout: float = 15.0) -> tuple[dict, float]:
    """POST JSON, return (response_dict, client_latency_ms)."""
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


# ─── Result Types ─────────────────────────────────────────────────────────────

@dataclass
class FrameGateResult:
    frame_id: str
    frame_index: int
    verdict: str
    psi: int
    violations: list[dict]
    client_latency_ms: float
    server_elapsed_ms: float
    ledger_record_id: Optional[str]
    quarantine_record_id: Optional[str]
    hash_ks: Optional[str] = None


@dataclass
class CertificationResult:
    session_id: str
    certified: bool
    n_frames: int
    n_approved: int
    n_rejected: int
    frame_results: list[FrameGateResult]
    passport_path: Optional[Path]
    fail_reason: Optional[str]
    total_elapsed_ms: float
    taxonomy_types_seen: list[str]


# ─── UE5 Export Hook ─────────────────────────────────────────────────────────

class UE5ExportHook:
    """
    Post-Export Hook for Mnemosyne Gate integration.

    Reads frame JSON files from a session directory (simulated UE5 export),
    submits each to gate-api via loopback TCP (SÖZLEŞME 2),
    and produces a certification passport or terminates fail-closed.
    """

    def __init__(
        self,
        gate_url: str = GATE_URL,
        operator: str = "ks@mnemosynelabs.ai",
        source_model: str = "ue5-lumen",
        source_pipeline: str = "ue5-post-export-hook",
        verbose: bool = True,
    ):
        self.gate_url = gate_url
        self.operator = operator
        self.source_model = source_model
        self.source_pipeline = source_pipeline
        self.verbose = verbose

    def process_session(
        self,
        session_dir: Path,
        benchmark_run_id: Optional[str] = None,
    ) -> CertificationResult:
        """
        Process all frames in a UE5 export session directory.

        Frame files: frame_NNNN.json (sorted, ascending)
        Each file must contain an 'attestation' dict and a 'frame_id' field.

        Returns CertificationResult. If any frame fails, certified=False
        and processing stops immediately (fail-closed — no partial certification).
        """
        session_id = session_dir.name
        benchmark_run_id = benchmark_run_id or f"ue5-{session_id}-{uuid.uuid4().hex[:8]}"

        frame_files = sorted(session_dir.glob("frame_*.json"))
        if not frame_files:
            return CertificationResult(
                session_id=session_id, certified=False,
                n_frames=0, n_approved=0, n_rejected=0,
                frame_results=[], passport_path=None,
                fail_reason="No frame files found in session directory",
                total_elapsed_ms=0.0, taxonomy_types_seen=[],
            )

        t_start = time.perf_counter()
        frame_results: list[FrameGateResult] = []
        taxonomy_types: set[str] = set()

        if self.verbose:
            print(f"\n  ── UE5 Export Hook │ session={session_id} │ {len(frame_files)} frames ──")
            print(f"     gate_url={self.gate_url}  (SÖZLEŞME 2: loopback TCP only)")

        for i, frame_path in enumerate(frame_files):
            frame_data = json.loads(frame_path.read_text(encoding="utf-8"))
            frame_id = frame_data.get("frame_id", f"{session_id}-frame-{i:04d}")
            attestation = frame_data.get("attestation", {})

            # Build FrameSubmission for gate-api
            payload = {
                "asset_id": frame_id,
                "source_model": self.source_model,
                "source_pipeline": self.source_pipeline,
                "operator": self.operator,
                "benchmark_run_id": benchmark_run_id,
                "replay_pointer": f"replay://ue5/{session_id}/{frame_id}",
                "attestation": attestation,
            }

            try:
                resp, latency_ms = _post(f"{self.gate_url}/submit", payload)
            except Exception as exc:
                # Communication error → fail-closed
                elapsed = (time.perf_counter() - t_start) * 1000
                if self.verbose:
                    print(f"    [{i:03d}] COMM-ERROR {exc}", file=sys.stderr)
                return CertificationResult(
                    session_id=session_id, certified=False,
                    n_frames=len(frame_files), n_approved=i, n_rejected=0,
                    frame_results=frame_results, passport_path=None,
                    fail_reason=f"gate-api communication error: {exc}",
                    total_elapsed_ms=elapsed, taxonomy_types_seen=sorted(taxonomy_types),
                )

            verdict = resp.get("verdict", "ERROR")
            psi = resp.get("psi", -1)
            server_ms = resp.get("elapsed_ms", 0.0)
            violations = resp.get("violations", [])

            # Track taxonomy (SÖZLEŞME 1) from quarantine records
            if violations:
                for v in violations:
                    vtype = v.get("taxonomy") or v.get("invariant", "")
                    if vtype:
                        taxonomy_types.add(vtype)

            fr = FrameGateResult(
                frame_id=frame_id,
                frame_index=i,
                verdict=verdict,
                psi=psi,
                violations=violations,
                client_latency_ms=round(latency_ms, 2),
                server_elapsed_ms=round(server_ms, 2),
                ledger_record_id=resp.get("ledger_record_id"),
                quarantine_record_id=resp.get("quarantine_record_id"),
                hash_ks=_ks_sha256(json.dumps(payload, sort_keys=True).encode()),
            )
            frame_results.append(fr)

            mark = "✓ APPROVED" if verdict == "APPROVED" else "✗ REJECTED"
            if self.verbose:
                print(f"    [{i:03d}] {mark}  ψ={psi}  {latency_ms:.1f}ms  {frame_id}")

            if verdict != "APPROVED":
                # FAIL-CLOSED: stop immediately, no certification issued
                elapsed = (time.perf_counter() - t_start) * 1000
                viol_detail = violations[0].get("detail", "unknown") if violations else "unknown"
                fail_reason = f"frame[{i}] {frame_id}: {viol_detail}"
                if self.verbose:
                    print(f"    → FAIL-CLOSED: {fail_reason}")
                    print(f"    → No certification issued.")
                return CertificationResult(
                    session_id=session_id, certified=False,
                    n_frames=len(frame_files), n_approved=i, n_rejected=1,
                    frame_results=frame_results, passport_path=None,
                    fail_reason=fail_reason,
                    total_elapsed_ms=elapsed, taxonomy_types_seen=sorted(taxonomy_types),
                )

        # All frames approved → produce certification passport
        total_elapsed = (time.perf_counter() - t_start) * 1000
        passport_path = self._produce_passport(
            session_id=session_id,
            session_dir=session_dir,
            frame_results=frame_results,
            benchmark_run_id=benchmark_run_id,
        )

        if self.verbose:
            print(f"    → ALL {len(frame_files)} frames APPROVED  ψ=1")
            print(f"    → Certification passport: {passport_path}")

        return CertificationResult(
            session_id=session_id, certified=True,
            n_frames=len(frame_files),
            n_approved=len(frame_results),
            n_rejected=0,
            frame_results=frame_results,
            passport_path=passport_path,
            fail_reason=None,
            total_elapsed_ms=round(total_elapsed, 2),
            taxonomy_types_seen=sorted(taxonomy_types),
        )

    def _produce_passport(
        self,
        session_id: str,
        session_dir: Path,
        frame_results: list[FrameGateResult],
        benchmark_run_id: str,
    ) -> Path:
        """
        Produce Ed25519-signed Mnemosyne_Certified_Passport.json.

        The passport binds:
          - session_id, frame_count, all ledger_record_ids
          - Merkle root of KS-SHA256(frame_id) for each frame
          - Ed25519 signature over canonical JSON
        """
        frame_hashes = [fr.hash_ks or _ks_sha256(fr.frame_id.encode())
                        for fr in frame_results]
        merkle = _merkle_root(frame_hashes)

        passport = {
            "protocol": "mnemosyne:v1.7",
            "schema": "mnemosyne.certification.v1",
            "session_id": session_id,
            "certification_timestamp": datetime.now(timezone.utc).isoformat(),
            "frame_count": len(frame_results),
            "all_frames_approved": True,
            "gate_version": GATE_VERSION,
            "policy_pack_version": POLICY_PACK_VERSION,
            "benchmark_run_id": benchmark_run_id,
            "merkle_root": merkle,
            "frame_manifest": [
                {
                    "frame_id": fr.frame_id,
                    "frame_index": fr.frame_index,
                    "verdict": fr.verdict,
                    "psi": fr.psi,
                    "hash_ks": fr.hash_ks,
                    "ledger_record_id": fr.ledger_record_id,
                    "latency_ms": fr.client_latency_ms,
                }
                for fr in frame_results
            ],
            "taxonomy_version": "v1.1",
            "loopback_tcp_compliant": True,   # SÖZLEŞME 2
        }

        canonical = json.dumps(passport, sort_keys=True, separators=(",", ":")).encode("utf-8")
        sig_hex = _sign(canonical)

        passport["signature"] = {
            "signature_hex": sig_hex,
            "algorithm": "Ed25519" if _HAS_CRYPTOGRAPHY else "KS-HMAC-fallback",
            "public_key_hex": _PUBLIC_KEY_HEX,
            "signed_over": "canonical_json_sorted_keys",
        }

        passport_path = session_dir / "Mnemosyne_Certified_Passport.json"
        passport_path.write_text(
            json.dumps(passport, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return passport_path
