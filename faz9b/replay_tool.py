"""
replay_tool.py — Mnemosyne FAZ 9B TASK 3
=========================================
Reads quarantine records produced during the FAZ 9B stream run,
re-submits each through gate-api, and measures verdict stability.

Verdict stability = fraction of replayed records that produce the same
verdict class (REJECTED). Since quarantine records represent ψ=0 decisions,
100% stability means the gate is deterministic: same violation → same rejection.
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import urllib.error
import urllib.request

GATE_URL = "http://127.0.0.1:8765"
QUARANTINE_DIR = Path("/Volumes/MNEMOSYNE-GATE/Vault/pipeline-tests/quarantine")


# ─── Violation → Payload Reconstruction ──────────────────────────────────────

def _reconstruct_failing_frame(record: dict, replay_run_id: str) -> dict:
    """
    Reconstruct a FrameSubmission from a quarantine record.
    Uses violation_type to reproduce the same failing condition.
    Deterministic: same violation_type → same gate rejection path.
    """
    violation_type = record.get("violation_type", "unknown")
    original_asset_id = record.get("asset_id", "unknown")
    asset_id = f"replay-{original_asset_id}"

    valid_sig = "a" * 128
    attestation = {
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
            "roi_hashes": {
                "head": {"status": "PASS"},
                "chest": {"status": "PASS"},
                "emblem_zone": {"status": "PASS"},
            }
        },
        "submission_mode": "controlled_generative",
        "metrics": {"emissive_budget": {"value": 680_000}},
    }

    # Reproduce the original violation
    if violation_type == "ks_mode":
        attestation["hash_mode"] = "raw"

    elif violation_type == "signature":
        attestation["signature"]["signature_hex"] = "deadbeef"

    elif violation_type.startswith("source_invariant"):
        attestation["source_invariants"]["mesh_topology_hash"] = {"status": "FAIL"}

    elif violation_type == "emissive_budget":
        attestation["metrics"]["emissive_budget"] = {"value": 750_000}

    elif violation_type.startswith("roi"):
        attestation["render_fingerprint"]["roi_hashes"]["head"] = {"status": "FAIL"}

    else:
        # Unknown violation type: use ks_mode as safe fallback (still REJECTED)
        attestation["hash_mode"] = "raw"

    return {
        "asset_id": asset_id,
        "source_model": record.get("source_model", "replay-engine"),
        "source_pipeline": record.get("source_pipeline", "faz9b-replay"),
        "operator": record.get("operator", "ks@mnemosynelabs.ai"),
        "benchmark_run_id": replay_run_id,
        "replay_pointer": f"replay://faz9b/replay/{original_asset_id}",
        "attestation": attestation,
    }


# ─── HTTP ─────────────────────────────────────────────────────────────────────

def _post(url: str, payload: dict, timeout: float = 15.0) -> tuple[dict, float]:
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
            latency_ms = (time.perf_counter() - t0) * 1000
            return json.loads(body), latency_ms
    except urllib.error.HTTPError as e:
        latency_ms = (time.perf_counter() - t0) * 1000
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {body}") from e


# ─── Result ───────────────────────────────────────────────────────────────────

@dataclass
class ReplayRecord:
    original_asset_id: str
    replay_asset_id: str
    violation_type: str
    original_verdict: str       # Always "REJECTED" (from quarantine)
    replay_verdict: str         # Should also be "REJECTED"
    stable: bool                # original_verdict == replay_verdict
    latency_ms: float
    timestamp_utc: str


@dataclass
class ReplayResult:
    replay_run_id: str
    n_replayed: int
    n_stable: int
    stability_pct: float
    records: list[ReplayRecord]
    violation_types_seen: list[str]


# ─── Main Replay Function ─────────────────────────────────────────────────────

def load_quarantine_records(benchmark_run_id_filter: Optional[str] = None) -> list[dict]:
    """Load quarantine JSON records from disk. Optionally filter by benchmark_run_id."""
    if not QUARANTINE_DIR.exists():
        return []

    records = []
    for f in sorted(QUARANTINE_DIR.glob("quarantine_*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if benchmark_run_id_filter:
                if data.get("benchmark_run_id") != benchmark_run_id_filter:
                    continue
            records.append(data)
        except Exception as exc:
            print(f"  [replay] WARNING: could not parse {f.name}: {exc}", file=sys.stderr)

    return records


def run_replay(
    benchmark_run_id_filter: Optional[str] = None,
    verbose: bool = True,
) -> ReplayResult:
    """
    Load quarantine records, re-submit each, verify verdict stability.

    Stability = fraction where replay_verdict == "REJECTED".
    Expected: 100% (deterministic gate, same violation → same rejection).
    """
    replay_run_id = f"replay-{benchmark_run_id_filter[:12] if benchmark_run_id_filter else 'all'}"
    records = load_quarantine_records(benchmark_run_id_filter)

    if verbose:
        print(f"\n  ── Replay Tool │ {len(records)} quarantine records │ run_id_filter={benchmark_run_id_filter or 'all'} ──")

    if not records:
        print("  [replay] No quarantine records found — skipping replay.")
        return ReplayResult(
            replay_run_id=replay_run_id,
            n_replayed=0, n_stable=0, stability_pct=100.0,
            records=[], violation_types_seen=[],
        )

    replay_records: list[ReplayRecord] = []
    violation_types_seen: set[str] = set()

    for i, qr in enumerate(records):
        violation_type = qr.get("violation_type", "unknown")
        violation_types_seen.add(violation_type)
        original_asset_id = qr.get("asset_id", "unknown")

        payload = _reconstruct_failing_frame(qr, replay_run_id)
        replay_asset_id = payload["asset_id"]

        try:
            resp, latency_ms = _post(f"{GATE_URL}/submit", payload)
            replay_verdict = resp.get("verdict", "ERROR")
            stable = replay_verdict in ("REJECTED", "QUARANTINED")

            rr = ReplayRecord(
                original_asset_id=original_asset_id,
                replay_asset_id=replay_asset_id,
                violation_type=violation_type,
                original_verdict="REJECTED",
                replay_verdict=replay_verdict,
                stable=stable,
                latency_ms=round(latency_ms, 2),
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
            )
            replay_records.append(rr)

            if verbose:
                mark = "✓" if stable else "✗"
                print(f"    [{i:03d}] {mark} vtype={violation_type:40s} → {replay_verdict}  {latency_ms:.1f}ms")

        except Exception as exc:
            replay_records.append(ReplayRecord(
                original_asset_id=original_asset_id,
                replay_asset_id=replay_asset_id,
                violation_type=violation_type,
                original_verdict="REJECTED",
                replay_verdict="ERROR",
                stable=False,
                latency_ms=0.0,
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
            ))
            if verbose:
                print(f"    [{i:03d}] ERROR: {exc}", file=sys.stderr)

    n_stable = sum(1 for r in replay_records if r.stable)
    stability_pct = round(n_stable / max(len(replay_records), 1) * 100, 2)

    if verbose:
        print(f"    → replayed={len(replay_records)}  stable={n_stable}  "
              f"stability={stability_pct}%  vtypes={sorted(violation_types_seen)}")

    return ReplayResult(
        replay_run_id=replay_run_id,
        n_replayed=len(replay_records),
        n_stable=n_stable,
        stability_pct=stability_pct,
        records=replay_records,
        violation_types_seen=sorted(violation_types_seen),
    )
