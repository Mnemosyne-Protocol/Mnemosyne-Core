#!/usr/bin/env python3
"""
Mnemosyne Runway AI Stress Test

Simulates a Runway AI generative output pipeline. Each synthetic frame is
passed through gate_engine_v3 (fail-closed, Ed25519 signed, Merkle ledger).

Usage:
    python3 bench/runway_stress_test.py [--frames N] [--seed S]
    python3 bench/runway_stress_test.py --self-test

Vault:      bench/out/runway_stress_vault/   (isolated from production)
Quarantine: /Volumes/MNEMOSYNE-GATE/Vault/pipeline-tests/quarantine/
Report:     bench/out/runway_stress_report.json

Dependencies:
    python3 -m pip install opencv-python cryptography numpy
"""

import sys
import os
import argparse
import json
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, List

BENCH_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH_DIR))

import numpy as np
import cv2
import gate_engine_v3 as gate

# ── Isolated stress-test vault (never touches production vault) ─────────────────
STRESS_VAULT = BENCH_DIR / "out" / "runway_stress_vault"
QUARANTINE_DIR = Path("/Volumes/MNEMOSYNE-GATE/Vault/pipeline-tests/quarantine")
REPORT_PATH = BENCH_DIR / "out" / "runway_stress_report.json"


def configure_gate_vault() -> None:
    """Patch gate_engine_v3 module globals to use the isolated stress-test vault."""
    gate.BASE_DIR = STRESS_VAULT
    gate.PATHS.update({
        "attestations":     STRESS_VAULT / "attestations",
        "rejections":       STRESS_VAULT / "rejections",
        "validated_assets": STRESS_VAULT / "assets" / "validated",
        "rejected_assets":  QUARANTINE_DIR,
        "ledger_records":   STRESS_VAULT / "ledger" / "records",
        "ledger_state":     STRESS_VAULT / "ledger" / "state",
        "keys":             STRESS_VAULT / "keys",
    })
    gate.PRIVATE_KEY_PATH = gate.PATHS["keys"] / "mnemosyne_ed25519_private.pem"
    gate.PUBLIC_KEY_PATH = gate.PATHS["keys"] / "mnemosyne_ed25519_public.pem"


# ── Synthetic Runway AI output scenarios ───────────────────────────────────────
# (label, width, height, channels, suffix, corrupt_bytes, expected_psi)
SCENARIOS: List[tuple] = [
    ("runway_hd_rgb",       1920, 1080, 3, ".png", False, 1),
    ("runway_4k_rgb",       3840, 2160, 3, ".png", False, 1),
    ("runway_rgba_alpha",    512,  512, 4, ".png", False, 1),
    ("runway_fail_tiny",     128,  128, 3, ".png", False, 0),
    ("runway_fail_ext",      512,  512, 3, ".gif", False, 0),
    ("runway_fail_corrupt",  512,  512, 3, ".png", True,  0),
]


def make_synthetic_frame(width: int, height: int, channels: int, seed: int):
    """Deterministic synthetic Runway output frame via numpy."""
    rng = np.random.default_rng(seed)
    shape = (height, width) if channels == 1 else (height, width, channels)
    return rng.integers(0, 256, shape, dtype=np.uint8)


def write_temp_frame(img, suffix: str, corrupt: bool) -> Path:
    """Encode a frame to a temp file with the given extension. Returns Path."""
    fd, tmp = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    p = Path(tmp)
    if corrupt:
        p.write_bytes(b"\xff\xd8CORRUPTED_RUNWAY_FRAME\x00\xff" * 64)
    else:
        ok, buf = cv2.imencode(".png", img, [cv2.IMWRITE_PNG_COMPRESSION, 9])
        if not ok:
            p.unlink(missing_ok=True)
            raise RuntimeError("cv2.imencode failed for synthetic frame")
        p.write_bytes(buf.tobytes())
    return p


def run_frame(label: str, frame_path: Path) -> Dict[str, Any]:
    """
    Run one frame through gate_engine_v3 internals.
    Mirrors the gate main() pipeline; returns a result dict.
    """
    t0 = time.perf_counter()
    source = str(frame_path.resolve()) if frame_path.exists() else str(frame_path)

    def elapsed() -> float:
        return round((time.perf_counter() - t0) * 1000, 3)

    if not frame_path.exists() or not frame_path.is_file():
        gate.reject(frame_path, ["file_not_found"], source_file=source)
        return {"label": label, "psi": 0, "status": "rejected",
                "reasons": ["file_not_found"], "elapsed_ms": elapsed()}

    try:
        raw = frame_path.read_bytes()
        file_hash = gate.sha256_bytes(raw)
    except Exception as e:
        gate.reject(frame_path, [f"file_read_error:{e}"], source_file=source)
        return {"label": label, "psi": 0, "status": "rejected",
                "reasons": ["file_read_error"], "elapsed_ms": elapsed()}

    img = gate.load_image(frame_path)
    if img is None:
        meta = {
            "file_name": frame_path.name,
            "suffix": frame_path.suffix.lower(),
            "opencv_decode": "failed",
        }
        gate.reject(frame_path, ["opencv_decode_failed"],
                    source_file=source, metadata=meta, file_hash=file_hash)
        return {"label": label, "psi": 0, "status": "rejected",
                "reasons": ["opencv_decode_failed"], "elapsed_ms": elapsed()}

    w, h = gate.get_dimensions(img)
    ch = gate.detect_channels(img)
    meta = gate.inspect_metadata(frame_path, img, w, h, ch)

    checks = gate.validate_policy(frame_path, w, h, ch)
    failed = [{"check": c["check"], "detail": c["detail"]}
              for c in checks if not c["passed"]]

    if failed:
        gate.reject(frame_path, failed,
                    source_file=source, metadata=meta, file_hash=file_hash)
        return {"label": label, "psi": 0, "status": "rejected",
                "reasons": [f["check"] for f in failed], "elapsed_ms": elapsed()}

    try:
        canon = gate.canonicalize_image(img, ch)
        canon_hash = gate.sha256_bytes(canon)
        fp = gate.simple_style_fingerprint(img)
    except Exception as e:
        gate.reject(frame_path, [f"canonicalization_failed:{e}"],
                    source_file=source, metadata=meta, file_hash=file_hash)
        return {"label": label, "psi": 0, "status": "rejected",
                "reasons": ["canonicalization_failed"], "elapsed_ms": elapsed()}

    gate.approve(
        asset_path=frame_path,
        source_file=source,
        canonical_hash=canon_hash,
        file_hash=file_hash,
        metadata=meta,
        fingerprint=fp,
        canonical_size_bytes=len(canon),
    )
    # gate.approve copies to validated_assets but does not remove original
    frame_path.unlink(missing_ok=True)

    return {"label": label, "psi": 1, "status": "approved",
            "reasons": [], "elapsed_ms": elapsed()}


def run_stress_test(frames_per_scenario: int, seed: int) -> Dict[str, Any]:
    configure_gate_vault()
    gate.ensure_dirs()
    gate.ensure_signing_keys()
    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

    print("─" * 68)
    print("  MNEMOSYNE RUNWAY AI STRESS TEST")
    print(f"  scenarios={len(SCENARIOS)}  frames_per_scenario={frames_per_scenario}  seed={seed}")
    print(f"  vault:      {STRESS_VAULT}")
    print(f"  quarantine: {QUARANTINE_DIR}")
    print("─" * 68)

    results: List[Dict[str, Any]] = []
    frame_seed = seed

    for label, w, h, ch, ext, corrupt, expected_psi in SCENARIOS:
        for i in range(frames_per_scenario):
            frame_label = f"{label}_{i + 1:03d}"
            img = make_synthetic_frame(w, h, ch, frame_seed)
            frame_seed += 1

            frame_path = write_temp_frame(img, ext, corrupt)
            try:
                result = run_frame(frame_label, frame_path)
            except Exception as e:
                frame_path.unlink(missing_ok=True)
                result = {"label": frame_label, "psi": 0, "status": "error",
                          "reasons": [str(e)], "elapsed_ms": 0.0}

            result["expected_psi"] = expected_psi
            result["scenario"] = label
            results.append(result)

            mark = "✓" if result["psi"] == 1 else "✗"
            tag = "" if result["psi"] == expected_psi else "  ← UNEXPECTED"
            reasons = ", ".join(result["reasons"]) if result["reasons"] else "—"
            print(f"  {mark} {frame_label:<38} ψ={result['psi']}"
                  f"  {result['elapsed_ms']:.1f}ms  {reasons}{tag}")

    total = len(results)
    approved = sum(1 for r in results if r["psi"] == 1)
    rejected = total - approved
    unexpected = sum(1 for r in results if r["psi"] != r["expected_psi"])

    print("─" * 68)
    print(f"  TOTAL {total}  |  APPROVED {approved}  |  REJECTED {rejected}"
          f"  |  UNEXPECTED {unexpected}")
    print("─" * 68)

    report = {
        "test":                "runway_stress_test",
        "gate_engine":         "gate_engine_v3",
        "gate_version":        gate.APP_VERSION,
        "frames_per_scenario": frames_per_scenario,
        "seed":                seed,
        "total":               total,
        "approved":            approved,
        "rejected":            rejected,
        "unexpected_outcomes": unexpected,
        "quarantine_dir":      str(QUARANTINE_DIR),
        "vault_dir":           str(STRESS_VAULT),
        "results":             results,
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False),
                           encoding="utf-8")
    print(f"  Report → {REPORT_PATH}")
    return report


def run_self_test() -> int:
    """Self-test: validates gate_engine_v3 integration. No external file dependencies."""
    configure_gate_vault()
    gate.ensure_dirs()
    gate.ensure_signing_keys()
    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

    cases = [
        ("self_pass_512",      512, 512, 3, ".png", False, 1),
        ("self_fail_tiny",      64,  64, 3, ".png", False, 0),
        ("self_fail_corrupt",  512, 512, 3, ".png", True,  0),
    ]

    print("MNEMOSYNE RUNWAY STRESS TEST — SELF-TEST")
    errors = 0
    for label, w, h, ch, ext, corrupt, expected_psi in cases:
        img = make_synthetic_frame(w, h, ch, seed=0xDEAD)
        frame_path = write_temp_frame(img, ext, corrupt)
        result = run_frame(label, frame_path)
        ok = result["psi"] == expected_psi
        mark = "PASS" if ok else "FAIL"
        print(f"  [{mark}] {label}: ψ={result['psi']} (expected {expected_psi})")
        if not ok:
            errors += 1

    if errors == 0:
        print("SELF-TEST PASSED ψ=1")
    else:
        print(f"SELF-TEST FAILED — {errors} unexpected outcome(s)")
    return 0 if errors == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Mnemosyne Runway AI Stress Test")
    parser.add_argument("--frames", type=int, default=5,
                        help="Frames per scenario (default: 5)")
    parser.add_argument("--seed", type=int, default=42,
                        help="RNG seed for synthetic frames (default: 42)")
    parser.add_argument("--self-test", action="store_true",
                        help="Run self-test only (validates gate integration)")
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()

    report = run_stress_test(args.frames, args.seed)
    return 0 if report["unexpected_outcomes"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
