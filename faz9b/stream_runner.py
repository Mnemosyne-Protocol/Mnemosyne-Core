"""
stream_runner.py — Mnemosyne FAZ 9B TASK 1 + TASK 2
=====================================================
TASK 1: Host-native synthetic stream runner.
        Modes: sustained_30fps, burst_120fps, burst_240fps, deterministic replay.

TASK 2: Violation corpus — at least 3 distinct violation_type values
        are produced in /quarantine/ with schema v1.1.

Architecture: host-native, submits to 127.0.0.1:8765/submit via loopback TCP.
No external dependencies — stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional
import urllib.error
import urllib.request

GATE_URL = "http://127.0.0.1:8765"
KS_SEED = b"MNEMOSYNE-KS-V3"


# ─── Violation Profiles ───────────────────────────────────────────────────────

class ViolationProfile(str, Enum):
    PASS               = "pass"
    KS_MODE            = "ks_mode"           # hash_mode="raw" instead of "KS-salted"
    SIGNATURE          = "signature"         # Ed25519 signature wrong length
    SOURCE_INVARIANT   = "source_invariant"  # mesh_topology_hash status=FAIL
    EMISSIVE_BUDGET    = "emissive_budget"   # Fixed6 threshold exceeded (0.75 > 0.72)
    ROI_FAILURE        = "roi.head"          # ROI head hash status=FAIL


# ─── Frame Generation ─────────────────────────────────────────────────────────

def _ks_sha256(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(KS_SEED)
    h.update(data)
    return h.hexdigest()


def build_frame(
    asset_id: str,
    profile: ViolationProfile,
    benchmark_run_id: str,
    operator: str = "ks@mnemosynelabs.ai",
    source_model: str = "runway-gen3",
    source_pipeline: str = "comfyui-mnemosyne",
) -> dict:
    """
    Build a FrameSubmission payload.
    Deterministic: same asset_id + profile → same payload.
    """
    # Canonical sig: valid 128-char hex for PASS profiles, invalid otherwise
    valid_sig = "a" * 128

    base_attestation = {
        "schema_version": "2.0",
        "hash_mode": "KS-salted",
        "signature": {"signature_hex": valid_sig, "algorithm": "Ed25519"},
        "signer": "tier_a",
        "source_invariants": {
            "mesh_topology_hash": {"status": "PASS"},
            "uv_layout_hash": {"status": "PASS"},
            "shader_signature_hash": {"status": "PASS"},
        },
        "render_fingerprint": {
            "silhouette_front": {"silhouette_hash": {"status": "PASS"}},
            "edge_front": {"edge_hash": {"status": "PASS"}},
            "roi_hashes": {
                "head": {"status": "PASS"},
                "chest": {"status": "PASS"},
                "emblem_zone": {"status": "PASS"},
            },
        },
        "submission_mode": "controlled_generative",
        "metrics": {"emissive_budget": {"value": 680_000}},  # Fixed6: 0.68 < 0.72 limit
    }

    if profile == ViolationProfile.KS_MODE:
        base_attestation["hash_mode"] = "raw"   # Non-KS → ks_mode violation

    elif profile == ViolationProfile.SIGNATURE:
        base_attestation["signature"]["signature_hex"] = "deadbeef"  # not 128 hex chars

    elif profile == ViolationProfile.SOURCE_INVARIANT:
        base_attestation["source_invariants"]["mesh_topology_hash"] = {"status": "FAIL"}

    elif profile == ViolationProfile.EMISSIVE_BUDGET:
        base_attestation["metrics"]["emissive_budget"] = {"value": 750_000}  # Fixed6: 0.75 > 0.72

    elif profile == ViolationProfile.ROI_FAILURE:
        base_attestation["render_fingerprint"]["roi_hashes"]["head"] = {"status": "FAIL"}

    return {
        "asset_id": asset_id,
        "source_model": source_model,
        "source_pipeline": source_pipeline,
        "operator": operator,
        "benchmark_run_id": benchmark_run_id,
        "replay_pointer": f"replay://faz9b/{asset_id}",
        "attestation": base_attestation,
    }


# ─── HTTP Helpers ─────────────────────────────────────────────────────────────

def _post(url: str, payload: dict, timeout: float = 15.0) -> tuple[dict, float, float]:
    """
    POST JSON payload. Returns (response_dict, client_latency_ms, serialize_ms).
    """
    t_ser = time.perf_counter()
    data = json.dumps(payload).encode("utf-8")
    serialize_ms = (time.perf_counter() - t_ser) * 1000

    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            client_latency_ms = (time.perf_counter() - t0) * 1000
            return json.loads(body), client_latency_ms, serialize_ms
    except urllib.error.HTTPError as e:
        client_latency_ms = (time.perf_counter() - t0) * 1000
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {body}") from e


# ─── Result Types ─────────────────────────────────────────────────────────────

@dataclass
class FrameResult:
    frame_index: int
    asset_id: str
    profile: str
    expected_verdict: str
    actual_verdict: str
    psi: int
    client_latency_ms: float
    server_elapsed_ms: float
    serialize_ms: float
    correct: bool
    benchmark_run_id: str
    timestamp_utc: str
    ledger_record_id: Optional[str] = None
    quarantine_record_id: Optional[str] = None
    error: Optional[str] = None


@dataclass
class StreamResult:
    mode: str
    benchmark_run_id: str
    target_fps: float
    achieved_fps: float
    total_elapsed_s: float
    n_frames: int
    n_correct: int
    n_errors: int
    n_approved: int
    n_rejected: int
    violation_type_counts: dict
    latencies_ms: list
    server_latencies_ms: list
    frames: list = field(default_factory=list)

    @property
    def accuracy_pct(self) -> float:
        return round(self.n_correct / max(self.n_frames, 1) * 100, 2)

    @property
    def p50_ms(self) -> float:
        s = sorted(self.latencies_ms)
        return s[len(s) // 2] if s else 0.0

    @property
    def p99_ms(self) -> float:
        s = sorted(self.latencies_ms)
        return s[max(0, int(len(s) * 0.99) - 1)] if s else 0.0

    @property
    def avg_ms(self) -> float:
        return sum(self.latencies_ms) / len(self.latencies_ms) if self.latencies_ms else 0.0


# ─── Stream Runner ────────────────────────────────────────────────────────────

# Frame profile distribution for mixed stream (per 10 frames):
# 4 PASS, 2 KS_MODE, 2 SIGNATURE, 1 SOURCE_INVARIANT, 1 EMISSIVE_BUDGET
_MIXED_CYCLE = [
    ViolationProfile.PASS,
    ViolationProfile.PASS,
    ViolationProfile.KS_MODE,
    ViolationProfile.SIGNATURE,
    ViolationProfile.PASS,
    ViolationProfile.PASS,
    ViolationProfile.SOURCE_INVARIANT,
    ViolationProfile.KS_MODE,
    ViolationProfile.EMISSIVE_BUDGET,
    ViolationProfile.SIGNATURE,
]


def run_stream(
    mode: str,
    n_frames: int,
    target_fps: Optional[float],
    benchmark_run_id: str,
    verbose: bool = True,
) -> StreamResult:
    """
    Run a synthetic stream.

    Parameters
    ----------
    mode       : 'sustained_30fps' | 'burst_120fps' | 'burst_240fps'
    n_frames   : total frames to submit
    target_fps : target rate (None = burst, no rate control)
    """
    target_interval = (1.0 / target_fps) if target_fps else 0.0
    frames: list[FrameResult] = []
    latencies_ms: list[float] = []
    server_latencies_ms: list[float] = []
    violation_counts: dict[str, int] = {}
    errors = 0

    if verbose:
        fps_str = f"{target_fps:.0f} FPS" if target_fps else "burst (unlimited)"
        print(f"\n  ── {mode} │ {n_frames} frames │ target={fps_str} ──")

    t_stream_start = time.perf_counter()
    # Drift-correcting: track cumulative target deadlines, not per-frame sleep
    next_frame_due = t_stream_start

    for i in range(n_frames):
        profile = _MIXED_CYCLE[i % len(_MIXED_CYCLE)]
        asset_id = f"faz9b-{benchmark_run_id[:8]}-{mode[:3]}-{i:04d}"
        expected = "APPROVED" if profile == ViolationProfile.PASS else "REJECTED"

        payload = build_frame(
            asset_id=asset_id,
            profile=profile,
            benchmark_run_id=benchmark_run_id,
        )

        frame_start = time.perf_counter()
        try:
            resp, client_ms, ser_ms = _post(f"{GATE_URL}/submit", payload)
            actual = resp.get("verdict", "ERROR")
            psi = resp.get("psi", -1)
            server_ms = resp.get("elapsed_ms", 0.0)
            correct = actual == expected

            latencies_ms.append(client_ms)
            server_latencies_ms.append(server_ms)

            if actual in ("REJECTED", "QUARANTINED"):
                vt = resp.get("violations", [{}])[0].get("invariant", "unknown") if resp.get("violations") else "unknown"
                violation_counts[vt] = violation_counts.get(vt, 0) + 1

            fr = FrameResult(
                frame_index=i,
                asset_id=asset_id,
                profile=profile.value,
                expected_verdict=expected,
                actual_verdict=actual,
                psi=psi,
                client_latency_ms=round(client_ms, 2),
                server_elapsed_ms=round(server_ms, 2),
                serialize_ms=round(ser_ms, 3),
                correct=correct,
                benchmark_run_id=benchmark_run_id,
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
                ledger_record_id=resp.get("ledger_record_id"),
                quarantine_record_id=resp.get("quarantine_record_id"),
            )
            frames.append(fr)

            if verbose and i % 30 == 0:
                mark = "✓" if correct else "✗"
                print(f"    [{i:04d}] {mark} {actual:10s} ψ={psi} {client_ms:6.1f}ms "
                      f"(srv={server_ms:.1f}ms) {profile.value}")

        except Exception as exc:
            errors += 1
            frames.append(FrameResult(
                frame_index=i, asset_id=asset_id, profile=profile.value,
                expected_verdict=expected, actual_verdict="ERROR", psi=-1,
                client_latency_ms=0, server_elapsed_ms=0, serialize_ms=0,
                correct=False, benchmark_run_id=benchmark_run_id,
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
                error=str(exc),
            ))
            if verbose:
                print(f"    [{i:04d}] ERROR: {exc}", file=sys.stderr)

        # Drift-correcting rate control (sustained mode only)
        # Advance the deadline unconditionally — prevents drift accumulation
        if target_interval > 0:
            next_frame_due += target_interval
            sleep_for = next_frame_due - time.perf_counter()
            if sleep_for > 0.001:
                time.sleep(sleep_for)
            elif sleep_for < -target_interval:
                # We've fallen more than one frame behind; re-sync to now
                next_frame_due = time.perf_counter()

    total_elapsed_s = time.perf_counter() - t_stream_start
    achieved_fps = n_frames / total_elapsed_s
    n_correct = sum(1 for f in frames if f.correct)
    n_approved = sum(1 for f in frames if f.actual_verdict == "APPROVED")
    n_rejected = sum(1 for f in frames if f.actual_verdict in ("REJECTED", "QUARANTINED"))

    result = StreamResult(
        mode=mode,
        benchmark_run_id=benchmark_run_id,
        target_fps=target_fps or 0.0,
        achieved_fps=round(achieved_fps, 2),
        total_elapsed_s=round(total_elapsed_s, 3),
        n_frames=n_frames,
        n_correct=n_correct,
        n_errors=errors,
        n_approved=n_approved,
        n_rejected=n_rejected,
        violation_type_counts=violation_counts,
        latencies_ms=latencies_ms,
        server_latencies_ms=server_latencies_ms,
        frames=frames,
    )

    if verbose:
        print(f"    → achieved={achieved_fps:.1f} fps  correct={n_correct}/{n_frames}  "
              f"avg={result.avg_ms:.1f}ms  p50={result.p50_ms:.1f}ms  p99={result.p99_ms:.1f}ms")

    return result
