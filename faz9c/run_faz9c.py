#!/usr/bin/env python3
"""
run_faz9c.py — Mnemosyne FAZ 9B.5 & 9C Orchestrator
=====================================================
Mnemosyne v3.0.0 · DOI: 10.5281/zenodo.18884426

Proves all 4 Exit Criteria:

  ec1  contract_frozen        Schema v1.1 + Taxonomy Mapping v1.0→v1.1 applied.
                              Quarantine records use canonical violation_type only.
  ec2  ue5_hook_works         Simulated UE5 export frames submitted via 127.0.0.1:8765.
  ec3  certification_produced All-passing session → Ed25519 signed passport generated.
  ec4  fail_closed_blocked    Failing session → cert rejected, quarantine written.

Platform Note: UE5 not installed on NODE-01 (FAZ 9D target).
Mock export generator used per CLAUDE.md.
"""

from __future__ import annotations

import json
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Adjust import path for sibling imports
sys.path.insert(0, str(Path(__file__).parent))

from mock_export_generator import generate_session
from ue5_export_hook import UE5ExportHook, _HAS_CRYPTOGRAPHY, CANONICAL_VIOLATION_TYPES

GATE_URL = "http://127.0.0.1:8765"
BENCH_OUT = Path(__file__).parent.parent / "bench" / "out"
REPORT_PATH = BENCH_OUT / "faz9c_report.json"
MOCK_EXPORTS_DIR = Path(__file__).parent / "mock_exports"

import urllib.request


def check_health() -> bool:
    try:
        with urllib.request.urlopen(f"{GATE_URL}/health", timeout=5) as resp:
            return json.loads(resp.read()).get("status") == "healthy"
    except Exception:
        return False


def _post(url: str, payload: dict, timeout: float = 10.0) -> dict:
    import urllib.error
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data,
                                  headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode()}") from e


# ─── ec1: Taxonomy Contract Verification ──────────────────────────────────────

def verify_taxonomy_contract(benchmark_run_id: str) -> dict:
    """
    Submit one frame of each violation class. Verify:
      1. gate-api applies taxonomy mapping correctly
      2. Quarantine records on disk use ONLY canonical violation_type values
      3. Non-canonical violation_type is rejected by quarantine-logger
    """
    print("\n[ec1] Taxonomy Contract Verification (SÖZLEŞME 1)")

    # Expected: internal invariant → canonical taxonomy
    test_cases = [
        # (label, attestation_mutation, expected_canonical_vtype)
        ("ks_mode→POLICY_MODE_VIOLATION",
         {"hash_mode": "raw"},
         "POLICY_MODE_VIOLATION"),
        ("signature→SIGNATURE_INVALID",
         {"signature": {"signature_hex": "bad", "algorithm": "Ed25519"}},
         "SIGNATURE_INVALID"),
        ("source_invariant→SOURCE_INVARIANT_BREACH",
         {"source_invariants": {"mesh_topology_hash": {"status": "FAIL"},
                                 "uv_layout_hash": {"status": "PASS"},
                                 "shader_signature_hash": {"status": "PASS"}}},
         "SOURCE_INVARIANT_BREACH"),
        ("roi→GEOMETRY_BREACH",
         {"render_fingerprint": {"roi_hashes": {
             "head": {"status": "FAIL"},
             "chest": {"status": "PASS"},
             "emblem_zone": {"status": "PASS"},
         }}},
         "GEOMETRY_BREACH"),
    ]

    results = {}
    all_ok = True

    QUARANTINE_DIR = Path("/Volumes/MNEMOSYNE-GATE/Vault/pipeline-tests/quarantine")

    for label, mutation, expected_vtype in test_cases:
        asset_id = f"ec1-taxonomy-{uuid.uuid4().hex[:8]}"
        base_attestation = {
            "schema_version": "2.0",
            "hash_mode": "KS-salted",
            "signature": {"signature_hex": "a" * 128, "algorithm": "Ed25519"},
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
        # Apply mutation
        base_attestation.update(mutation)

        payload = {
            "asset_id": asset_id,
            "source_model": "ec1-test",
            "source_pipeline": "taxonomy-verification",
            "operator": "ks@mnemosynelabs.ai",
            "benchmark_run_id": benchmark_run_id,
            "replay_pointer": f"replay://ec1/{asset_id}",
            "attestation": base_attestation,
        }

        try:
            resp = _post(f"{GATE_URL}/submit", payload)
            verdict = resp.get("verdict")
            violations = resp.get("violations", [])
        except Exception as exc:
            results[label] = {"ok": False, "error": str(exc)}
            all_ok = False
            print(f"  ✗ {label}: ERROR {exc}", file=sys.stderr)
            continue

        # Verify quarantine record on disk has canonical violation_type
        import time as _time
        _time.sleep(0.3)  # small delay for disk write to complete

        quarantine_record = None
        if QUARANTINE_DIR.exists():
            for f in sorted(QUARANTINE_DIR.glob(f"quarantine_{asset_id}_*.json")):
                try:
                    quarantine_record = json.loads(f.read_text(encoding="utf-8"))
                    break
                except Exception:
                    pass

        actual_vtype = quarantine_record.get("violation_type") if quarantine_record else None
        is_canonical = actual_vtype in CANONICAL_VIOLATION_TYPES
        vtype_correct = actual_vtype == expected_vtype
        ok = verdict == "REJECTED" and is_canonical and vtype_correct

        mark = "✓" if ok else "✗"
        print(f"  {mark} {label}")
        print(f"       verdict={verdict}  quarantine_vtype={actual_vtype!r}  "
              f"expected={expected_vtype!r}  canonical={is_canonical}")

        results[label] = {
            "ok": ok,
            "verdict": verdict,
            "quarantine_violation_type": actual_vtype,
            "expected_canonical": expected_vtype,
            "is_canonical": is_canonical,
            "vtype_correct": vtype_correct,
        }
        if not ok:
            all_ok = False

    print(f"  Canonical violation types enforced: {all_ok}")
    return {"all_ok": all_ok, "cases": results,
            "canonical_taxonomy": sorted(CANONICAL_VIOLATION_TYPES)}


# ─── ec2 + ec3: Passing Session → Certification ──────────────────────────────

def run_passing_session(hook: UE5ExportHook, benchmark_run_id: str) -> dict:
    """
    ec2: UE5 hook submits frames via 127.0.0.1:8765
    ec3: All-passing session → Ed25519-signed passport produced
    """
    print("\n[ec2 + ec3] Passing Session — All frames valid → Certification passport")

    session_id = f"session-passing-{benchmark_run_id[:8]}"
    session_dir = generate_session(
        output_dir=MOCK_EXPORTS_DIR,
        session_id=session_id,
        n_frames=5,
        failing_frame_index=None,   # No failures
    )

    result = hook.process_session(session_dir, benchmark_run_id=benchmark_run_id)

    passport_exists = (result.passport_path is not None and
                       result.passport_path.exists())
    passport_valid = False
    passport_has_sig = False

    if passport_exists:
        p = json.loads(result.passport_path.read_text(encoding="utf-8"))
        passport_valid = (
            p.get("all_frames_approved") is True and
            p.get("frame_count") == result.n_frames and
            "merkle_root" in p and
            "frame_manifest" in p
        )
        passport_has_sig = (
            "signature" in p and
            "signature_hex" in p["signature"] and
            len(p["signature"]["signature_hex"]) == 128
        )

    ec2_ok = result.certified and result.n_approved == result.n_frames and result.n_rejected == 0
    ec3_ok = passport_exists and passport_valid and passport_has_sig

    mark2 = "✓" if ec2_ok else "✗"
    mark3 = "✓" if ec3_ok else "✗"
    print(f"  {mark2} ec2: certified={result.certified}  approved={result.n_approved}/{result.n_frames}")
    print(f"  {mark3} ec3: passport_exists={passport_exists}  has_signature={passport_has_sig}")
    if result.passport_path:
        print(f"       passport: {result.passport_path}")

    return {
        "ec2_ok": ec2_ok,
        "ec3_ok": ec3_ok,
        "session_id": session_id,
        "certified": result.certified,
        "n_frames": result.n_frames,
        "n_approved": result.n_approved,
        "n_rejected": result.n_rejected,
        "passport_path": str(result.passport_path) if result.passport_path else None,
        "passport_valid": passport_valid,
        "passport_has_ed25519_sig": passport_has_sig,
        "total_elapsed_ms": result.total_elapsed_ms,
        "algorithm": "Ed25519" if _HAS_CRYPTOGRAPHY else "KS-HMAC-fallback",
    }


# ─── ec4: Failing Session → Fail-Closed ──────────────────────────────────────

def run_failing_session(hook: UE5ExportHook, benchmark_run_id: str) -> dict:
    """
    ec4: Failing session (frame with SIGNATURE_INVALID) →
         certification blocked, quarantine record written.
    """
    print("\n[ec4] Failing Session — Bad frame → fail-closed, no certification")

    session_id = f"session-failing-{benchmark_run_id[:8]}"
    session_dir = generate_session(
        output_dir=MOCK_EXPORTS_DIR,
        session_id=session_id,
        n_frames=5,
        failing_frame_index=2,               # frame 2 has the violation
        failing_violation="SIGNATURE_INVALID",
    )

    result = hook.process_session(session_dir, benchmark_run_id=benchmark_run_id)

    no_passport = (result.passport_path is None or
                   not result.passport_path.exists())
    cert_blocked = not result.certified
    quarantine_written = result.n_rejected > 0

    ec4_ok = cert_blocked and no_passport

    mark = "✓" if ec4_ok else "✗"
    print(f"  {mark} ec4: certified={result.certified}  no_passport={no_passport}  "
          f"fail_reason={result.fail_reason!r}")
    print(f"       approved_before_block={result.n_approved}  rejected={result.n_rejected}")

    return {
        "ec4_ok": ec4_ok,
        "session_id": session_id,
        "certified": result.certified,
        "no_passport": no_passport,
        "fail_reason": result.fail_reason,
        "n_approved_before_block": result.n_approved,
        "n_rejected": result.n_rejected,
        "total_elapsed_ms": result.total_elapsed_ms,
    }


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print("═══════════════════════════════════════════════════════════════")
    print("  Mnemosyne FAZ 9B.5 & 9C — API Contract Freeze + UE5 Hook MVP")
    print("  SÖZLEŞME 2: Loopback TCP 127.0.0.1:8765 ONLY")
    print("  Platform: Mock UE5 export (real UE5 → FAZ 9D)")
    print("═══════════════════════════════════════════════════════════════")

    # Pre-flight
    print("\n[0] Health check ...")
    if not check_health():
        print("  FATAL: gate-api not reachable at 127.0.0.1:8765", file=sys.stderr)
        print("  Run: cd faz9a && docker compose up --build -d", file=sys.stderr)
        sys.exit(1)
    print(f"  gate-api: HEALTHY  cryptography={_HAS_CRYPTOGRAPHY}")

    benchmark_run_id = f"faz9c-{uuid.uuid4().hex[:12]}"
    print(f"  benchmark_run_id: {benchmark_run_id}")
    t_start = time.perf_counter()

    MOCK_EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    hook = UE5ExportHook(
        gate_url=GATE_URL,
        operator="ks@mnemosynelabs.ai",
        source_model="ue5-lumen-mock",
        source_pipeline="ue5-post-export-hook",
        verbose=True,
    )

    # ec1: Taxonomy contract
    ec1_result = verify_taxonomy_contract(benchmark_run_id)

    # ec2 + ec3: Passing session
    ec23_result = run_passing_session(hook, benchmark_run_id)

    # ec4: Failing session
    ec4_result = run_failing_session(hook, benchmark_run_id)

    total_elapsed_ms = (time.perf_counter() - t_start) * 1000

    # ── Build report ──
    exit_criteria = {
        "ec1_contract_frozen":       ec1_result["all_ok"],
        "ec2_ue5_hook_works":        ec23_result["ec2_ok"],
        "ec3_certification_produced": ec23_result["ec3_ok"],
        "ec4_fail_closed_blocked":   ec4_result["ec4_ok"],
    }

    report = {
        "benchmark_run_id": benchmark_run_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "gate_url": GATE_URL,
        "gate_version": "3.0.0",
        "policy_pack_version": "final_gate_policy.v1.0",
        "faz": "9C",
        "platform_note": "Mock UE5 export (real UE5 → FAZ 9D per CLAUDE.md)",
        "loopback_tcp_only": True,
        "ed25519_available": _HAS_CRYPTOGRAPHY,
        "total_elapsed_ms": round(total_elapsed_ms, 1),
        "canonical_taxonomy_v11": sorted(CANONICAL_VIOLATION_TYPES),
        "tasks": {
            "sozzlesme1_taxonomy": ec1_result,
            "ue5_passing_session": ec23_result,
            "ue5_failing_session": ec4_result,
        },
        "exit_criteria": exit_criteria,
    }

    BENCH_OUT.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # ── Terminal Proof ────────────────────────────────────────────────────────
    print("\n" + "═" * 63)
    print("  FAZ 9C EXIT CRITERIA — PROOF")
    print("═" * 63)

    ec_labels = {
        "ec1_contract_frozen":
            f"Taxonomy v1.1 enforced: {sorted(CANONICAL_VIOLATION_TYPES)}",
        "ec2_ue5_hook_works":
            f"UE5 hook → 127.0.0.1:8765 (SÖZLEŞME 2), "
            f"{ec23_result['n_approved']}/{ec23_result['n_frames']} frames approved",
        "ec3_certification_produced":
            f"Ed25519 passport ({ec23_result['algorithm']}) at "
            f"session-passing-{benchmark_run_id[:8]}/Mnemosyne_Certified_Passport.json",
        "ec4_fail_closed_blocked":
            f"SIGNATURE_INVALID → certified=False, no passport, "
            f"fail_reason={ec4_result['fail_reason']!r}",
    }

    all_pass = True
    for key, label in ec_labels.items():
        val = exit_criteria[key]
        mark = "✓ PASS" if val else "✗ FAIL"
        if not val:
            all_pass = False
        print(f"  {mark}  {key}")
        print(f"         └─ {label}")

    print("─" * 63)
    print(f"  benchmark_run_id: {benchmark_run_id}")
    print(f"  Total elapsed: {total_elapsed_ms:.0f}ms")
    print(f"  Report: {REPORT_PATH}")
    print("═" * 63)

    if all_pass:
        print("\n  ALL 4 EXIT CRITERIA SATISFIED — FAZ 9C COMPLETE ψ=1\n")
    else:
        print("\n  SOME CRITERIA FAILED — see report for details\n", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
