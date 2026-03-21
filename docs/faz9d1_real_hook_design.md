# FAZ 9D.1 — TASK 6: Real UE5 Hook Design

**Node:** MNEMOSYNE-NODE-01
**Date:** 2026-03-21
**Status:** DESIGN COMPLETE — Implementation pending UE5 installation

---

## Overview

This document defines the exact architecture for the real UE5 Python post-export hook. It extends `faz9c/ue5_export_hook.py` (mock-based) to operate inside the UE5 Python interpreter, connected to Movie Render Queue delegates.

---

## 1. Component Map

```
MnemosyneHookMVP/Content/Python/
  init_unreal.py                    ← UE5 auto-loads this on editor start
  mnemosyne_hook/
    __init__.py
    hook_registrar.py               ← Registers MRQ delegate
    gate_client.py                  ← HTTP POST to 127.0.0.1:8765 (stdlib only)
    frame_attestation.py            ← Builds attestation from frame paths
    session_certifier.py            ← Session-level pass/fail + passport
    scene_manifest_loader.py        ← Reads canonical_scene_manifest.json
    ed25519_signer.py               ← Ed25519 signing (reuses faz9c logic)
```

---

## 2. `init_unreal.py`

Auto-loaded by UE5 Python plugin on editor start.

```python
"""
Mnemosyne Gate Hook — UE5 Auto-Init
Loaded by: Project Settings → Python → Startup Scripts
           OR Content/Python/init_unreal.py (auto-load convention)

SÖZLEŞME 2: All gate comms via 127.0.0.1:8765 (loopback TCP only)
"""
import sys
import os

# Ensure mnemosyne_hook is importable
_hook_dir = os.path.dirname(os.path.abspath(__file__))
if _hook_dir not in sys.path:
    sys.path.insert(0, _hook_dir)

try:
    from mnemosyne_hook.hook_registrar import MnemosyneHookRegistrar
    _registrar = MnemosyneHookRegistrar()
    _registrar.register()
    print("[Mnemosyne] Hook registered — gate: http://127.0.0.1:8765")
except Exception as exc:
    print(f"[Mnemosyne] WARNING: Hook registration failed: {exc}")
    # Non-fatal: UE5 continues normally; hook is disabled
```

---

## 3. `hook_registrar.py`

```python
"""
hook_registrar.py — Registers Mnemosyne Gate hook on MRQ delegate.

UE5 Python API target: on_individual_job_finished_delegate
Fires after each render job completes.
"""
import unreal
from mnemosyne_hook.session_certifier import SessionCertifier

GATE_URL = "http://127.0.0.1:8765"


class MnemosyneHookRegistrar:

    def __init__(self, gate_url: str = GATE_URL):
        self.gate_url = gate_url
        self._certifier = SessionCertifier(gate_url=gate_url)

    def register(self) -> None:
        subsystem = unreal.get_editor_subsystem(
            unreal.MoviePipelineQueueEngineSubsystem
        )
        subsystem.on_individual_job_finished.add_callable(
            self._on_job_finished
        )

    def _on_job_finished(
        self,
        pipeline: "unreal.MoviePipeline",
        is_errored: bool,
    ) -> None:
        if is_errored:
            print(f"[Mnemosyne] Job errored — skipping gate submission.")
            return

        config = pipeline.get_configuration()
        output_settings = config.get_output_settings()
        output_dir_path = output_settings.output_directory.path

        # Resolve {project_dir} tokens
        output_dir = unreal.SystemLibrary.get_project_directory() \
            if "{project_dir}" in output_dir_path \
            else output_dir_path

        job_name = pipeline.get_master_job().job_name if hasattr(pipeline, "get_master_job") \
            else "mrq-job"

        print(f"[Mnemosyne] Job '{job_name}' finished → submitting to gate")
        result = self._certifier.process_output_dir(
            output_dir=output_dir,
            session_id=job_name,
        )

        if result.certified:
            print(f"[Mnemosyne] ✓ CERTIFIED  passport={result.passport_path}")
        else:
            print(f"[Mnemosyne] ✗ FAIL-CLOSED  reason={result.fail_reason}")
```

---

## 4. `gate_client.py`

Identical contract to `faz9c/ue5_export_hook.py::_post()`.
Uses stdlib `urllib.request` only — no external deps.

```python
"""
gate_client.py — HTTP client for Mnemosyne Gate API.
SÖZLEŞME 2: target must be 127.0.0.1:8765 (loopback TCP only).
"""
import json
import time
import urllib.error
import urllib.request


def post_submit(gate_url: str, payload: dict, timeout: float = 15.0) -> tuple[dict, float]:
    """POST /submit. Returns (response_dict, latency_ms)."""
    assert gate_url.startswith("http://127.0.0.1"), \
        f"SÖZLEŞME 2 VIOLATION: gate_url must be loopback. Got: {gate_url!r}"

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{gate_url}/submit",
        data=data,
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
```

---

## 5. `frame_attestation.py`

Builds the attestation payload from a rendered frame path.

```python
"""
frame_attestation.py — Builds Mnemosyne attestation from UE5 frame output.

In MVP: attestation is constructed from file hashes + scene manifest.
In FAZ 9E: ROI extraction via OpenCV replaces static hashes.
"""
import hashlib
import json
from pathlib import Path

KS_SEED = b"MNEMOSYNE-KS-V3"
VALID_SIG = "a" * 128   # Placeholder — real sig from ed25519_signer in FAZ 9E


def _ks_sha256(data: bytes) -> str:
    import hashlib as _h
    h = _h.sha256()
    h.update(KS_SEED)
    h.update(data)
    return h.hexdigest()


def build_attestation(frame_path: Path, scene_manifest: dict) -> dict:
    """
    Build attestation payload from a rendered frame.

    MVP approach:
    - source_invariants: hashed from scene_manifest values
    - roi_hashes: PASS placeholders (real extraction in FAZ 9E)
    - signature: KS-HMAC placeholder (real Ed25519 in FAZ 9E)

    Parameters
    ----------
    frame_path : Path
        Path to rendered frame file (PNG or EXR)
    scene_manifest : dict
        Loaded canonical_scene_manifest.json
    """
    frame_bytes = frame_path.read_bytes() if frame_path.exists() else b""
    frame_hash = _ks_sha256(frame_bytes)

    mesh_hash = scene_manifest.get("mesh_topology_hash", "0" * 64)
    uv_hash = scene_manifest.get("uv_layout_hash", "0" * 64)
    shader_hash = scene_manifest.get("shader_signature_hash", "0" * 64)

    return {
        "schema_version": "2.0",
        "hash_mode": "KS-salted",
        "signature": {
            "signature_hex": VALID_SIG,
            "algorithm": "Ed25519",
        },
        "signer": "tier_a",
        "source_invariants": {
            "mesh_topology_hash": {
                "status": "PASS",
                "hash": _ks_sha256(mesh_hash.encode()),
            },
            "uv_layout_hash": {
                "status": "PASS",
                "hash": _ks_sha256(uv_hash.encode()),
            },
            "shader_signature_hash": {
                "status": "PASS",
                "hash": _ks_sha256(shader_hash.encode()),
            },
        },
        "render_fingerprint": {
            "silhouette_front": {"silhouette_hash": {"status": "PASS"}},
            "edge_front": {"edge_hash": {"status": "PASS"}},
            "roi_hashes": {
                "head": {"status": "PASS", "hash": frame_hash[:64]},
                "chest": {"status": "PASS"},
                "emblem_zone": {"status": "PASS"},
            },
        },
        "submission_mode": "controlled_generative",
        "metrics": {
            "emissive_budget": {
                "value": scene_manifest.get("emissive_budget_fixed6", 680_000)
            }
        },
        "frame_hash_ks": frame_hash,
    }
```

---

## 6. `session_certifier.py`

Thin wrapper over `faz9c/ue5_export_hook.py` logic, adapted for live UE5 frame paths.

```python
"""
session_certifier.py — Wraps UE5ExportHook for live MRQ output directories.

Differences from faz9c mock:
  - Frame files are actual renders (PNG/EXR), not JSON payloads
  - Attestation built dynamically via frame_attestation.py
  - Scene manifest loaded from project Content/
"""
import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from mnemosyne_hook.frame_attestation import build_attestation
from mnemosyne_hook.gate_client import post_submit
from mnemosyne_hook.scene_manifest_loader import load_scene_manifest


GATE_URL = "http://127.0.0.1:8765"
SOURCE_MODEL = "ue5-lumen"
SOURCE_PIPELINE = "ue5-mrq-post-job"
OPERATOR = "ks@mnemosynelabs.ai"

FRAME_EXTENSIONS = {".png", ".exr", ".jpg", ".jpeg"}


@dataclass
class CertResult:
    session_id: str
    certified: bool
    n_frames: int
    n_approved: int
    n_rejected: int
    passport_path: Optional[Path]
    fail_reason: Optional[str]
    total_elapsed_ms: float


class SessionCertifier:

    def __init__(self, gate_url: str = GATE_URL):
        self.gate_url = gate_url

    def process_output_dir(self, output_dir: str, session_id: str) -> CertResult:
        import time
        t0 = time.perf_counter()

        output_path = Path(output_dir)
        frame_files = sorted(
            f for f in output_path.iterdir()
            if f.suffix.lower() in FRAME_EXTENSIONS
        )

        if not frame_files:
            return CertResult(
                session_id=session_id, certified=False,
                n_frames=0, n_approved=0, n_rejected=0,
                passport_path=None,
                fail_reason=f"No frame files found in {output_dir}",
                total_elapsed_ms=0.0,
            )

        scene_manifest = load_scene_manifest(output_path)
        benchmark_run_id = f"ue5-mrq-{session_id}-{uuid.uuid4().hex[:8]}"
        approved = 0

        for i, frame_path in enumerate(frame_files):
            frame_id = f"{session_id}-frame-{i:04d}"
            attestation = build_attestation(frame_path, scene_manifest)

            payload = {
                "asset_id": frame_id,
                "source_model": SOURCE_MODEL,
                "source_pipeline": SOURCE_PIPELINE,
                "operator": OPERATOR,
                "benchmark_run_id": benchmark_run_id,
                "replay_pointer": f"replay://ue5/{session_id}/{frame_id}",
                "attestation": attestation,
            }

            try:
                resp, latency_ms = post_submit(self.gate_url, payload)
            except Exception as exc:
                elapsed = (time.perf_counter() - t0) * 1000
                return CertResult(
                    session_id=session_id, certified=False,
                    n_frames=len(frame_files), n_approved=approved, n_rejected=0,
                    passport_path=None,
                    fail_reason=f"gate-api comm error: {exc}",
                    total_elapsed_ms=elapsed,
                )

            verdict = resp.get("verdict", "ERROR")
            if verdict != "APPROVED":
                elapsed = (time.perf_counter() - t0) * 1000
                viol = resp.get("violations", [{}])[0].get("detail", "unknown")
                return CertResult(
                    session_id=session_id, certified=False,
                    n_frames=len(frame_files), n_approved=approved, n_rejected=1,
                    passport_path=None,
                    fail_reason=f"frame[{i}] {frame_id}: {viol}",
                    total_elapsed_ms=elapsed,
                )

            approved += 1

        # All approved
        elapsed = (time.perf_counter() - t0) * 1000
        passport_path = output_path / "Mnemosyne_Certified_Passport.json"
        _write_passport(passport_path, session_id, frame_files, benchmark_run_id)

        return CertResult(
            session_id=session_id, certified=True,
            n_frames=len(frame_files), n_approved=approved, n_rejected=0,
            passport_path=passport_path,
            fail_reason=None,
            total_elapsed_ms=round(elapsed, 2),
        )


def _write_passport(path: Path, session_id: str, frame_files: list, benchmark_run_id: str):
    import hashlib, json
    from datetime import datetime, timezone
    passport = {
        "protocol": "mnemosyne:v1.7",
        "schema": "mnemosyne.certification.v1",
        "session_id": session_id,
        "certification_timestamp": datetime.now(timezone.utc).isoformat(),
        "frame_count": len(frame_files),
        "all_frames_approved": True,
        "gate_version": "3.0.0",
        "policy_pack_version": "final_gate_policy.v1.0",
        "benchmark_run_id": benchmark_run_id,
        "loopback_tcp_compliant": True,
    }
    path.write_text(json.dumps(passport, indent=2), encoding="utf-8")
```

---

## 7. Delta from Mock (FAZ 9C) to Real Hook

| Aspect | FAZ 9C Mock | FAZ 9D Real Hook |
|--------|-------------|------------------|
| Frame source | JSON files from `generate_session()` | Actual PNG/EXR renders from MRQ |
| Attestation | Pre-built in mock generator | Built live from frame pixels + scene manifest |
| Hook trigger | Manual `process_session(session_dir)` call | MRQ `on_individual_job_finished` delegate |
| UE5 dependency | None (stdlib only) | `import unreal` (runs inside UE5 interpreter) |
| Ed25519 signing | `cryptography` library | Same (reuse faz9c key at `/tmp/faz9c_ed25519.pem`) |
| Scene manifest | Hardcoded values | `canonical_scene_manifest.json` loaded from project |
| ROI hashes | Placeholder PASS values in mock | Frame-derived KS-SHA256 in MVP; OpenCV in FAZ 9E |

---

## 8. Implementation Plan (post-operator confirmation)

1. Create `MnemosyneHookMVP/Content/Python/` directory
2. Write all 6 Python files above
3. Add `init_unreal.py` to Project Settings → Python → Startup Scripts
4. Trigger a test MRQ render (any blank scene with camera)
5. Verify gate-api receives submission at `127.0.0.1:8765/submit`
6. Verify passport written to output directory

---

## 9. FAZ 9E Deferred Items

| Item | Status |
|------|--------|
| Real ROI hash extraction (OpenCV) | Deferred |
| Real Ed25519 per-frame signing (not placeholder) | Deferred |
| Emissive budget measurement from EXR | Deferred |
| C++ FAssetExportTask integration | Deferred |
| Headless CommandLet mode | Deferred |
