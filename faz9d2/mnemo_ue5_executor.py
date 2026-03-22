"""
mnemo_ue5_executor.py — Mnemosyne FAZ 9D.4
============================================
Mnemosyne v3.0.0 · DOI: 10.5281/zenodo.18884426

UE5 MRQ delegate-based Gate hook.

DEPLOYMENT TARGET: Inside UE5 editor process (Python Script Plugin).
  Place at: MnemosyneHookMVP/Content/Python/mnemo_ue5_executor.py

ARCHITECTURE (FAZ 9D.4 hardening — delegate binding path):
  Surface   : on_executor_finished_delegate.add_callable()
              confirmed via live UE5 5.7.4 reflection probe (faz9d4)
  Executor  : unreal.MoviePipelinePIEExecutor (standard, no custom subclass)
  Transport : HTTP/1.1 Loopback TCP — 127.0.0.1:8765 ONLY (SÖZLEŞME 2)
  Schema    : scene_manifest_v1 (frozen)
  Taxonomy  : v1.1 (frozen)
  Contracts : Gate API FrameSubmission (frozen — gate-api/main.py)

WHY NOT @unreal.uclass():
  UE5 C++ reflection blocks Python-defined executor subclasses from appearing
  in the MRQ dropdown and prevents @unreal.ufunction(override=True) from
  resolving correctly. Delegate binding via add_callable() is the confirmed
  stable Python surface (reflection probe 2026-03-22).

FAIL-CLOSED GUARANTEE:
  Any frame with psi=0 → quarantine written by gate-api → error logged
  → No passport generated → No partial certification.
  Communication error → same outcome.

USAGE (from trigger_mnemosyne_render.py or UE5 Python Console):
  from mnemo_ue5_executor import begin_session, on_mrq_finished_callback
  begin_session(project_name=..., level_name=..., scan_dir=...)
  executor = unreal.MoviePipelinePIEExecutor()
  executor.on_executor_finished_delegate.add_callable(on_mrq_finished_callback)
  # ec2 log fires here — "delegate bound"
  subsystem.render_queue_with_executor_instance(executor)
"""

from __future__ import annotations

import json
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ── UE5 import guard ──────────────────────────────────────────────────────────
try:
    import unreal
    _UE5_CONTEXT = True
except ImportError:
    _UE5_CONTEXT = False

# ── Gate client ───────────────────────────────────────────────────────────────
try:
    from mnemo_gate_client import (
        submit_frame, produce_passport,
        GATE_URL, GATE_VERSION, POLICY_PACK_VERSION,
    )
    from mnemo_manifest import build_manifest, write_manifest
    _GATE_CLIENT_AVAILABLE = True
except ImportError as _imp_err:
    _GATE_CLIENT_AVAILABLE = False
    _GATE_IMPORT_ERROR = str(_imp_err)

# ── Log shim ─────────────────────────────────────────────────────────────────
def _log(msg: str):
    if _UE5_CONTEXT:
        unreal.log(f"MNEMOSYNE: {msg}")
    else:
        print(f"[MNEMOSYNE] {msg}")

def _log_err(msg: str):
    if _UE5_CONTEXT:
        unreal.log_error(f"MNEMOSYNE: {msg}")
    else:
        print(f"[MNEMOSYNE ERROR] {msg}", file=sys.stderr)


# ─── Session State ────────────────────────────────────────────────────────────

@dataclass
class MnemoSessionState:
    """Mutable state for one MRQ certification session."""
    session_id: str = field(default_factory=lambda: f"ue5-{uuid.uuid4().hex[:12]}")
    benchmark_run_id: str = ""
    operator: str = "ks@mnemosynelabs.ai"
    source_model: str = "UE5_LUMEN"
    source_pipeline: str = "UE5_MRQ"
    project_name: str = "MnemosyneHookMVP"
    level_name: str = "Unknown"
    scan_dir: Optional[Path] = None          # where rendered frames are written
    cert_output_dir: Optional[Path] = None  # where passport + manifest are written
    frame_results: list = field(default_factory=list)
    certified: bool = False
    abort_reason: Optional[str] = None
    manifest_path: Optional[Path] = None

    def __post_init__(self):
        self.benchmark_run_id = f"ue5-{self.session_id}-{uuid.uuid4().hex[:8]}"


# ─── Module-level active session (set by begin_session before render) ─────────

_active_session: Optional[MnemoSessionState] = None


def begin_session(
    project_name: str = "MnemosyneHookMVP",
    level_name: str = "Unknown",
    scan_dir: Optional[Path] = None,
    cert_output_dir: Optional[Path] = None,
    operator: str = "ks@mnemosynelabs.ai",
    source_model: str = "UE5_LUMEN",
    source_pipeline: str = "UE5_MRQ",
) -> MnemoSessionState:
    """
    Initialize a new certification session.
    Must be called BEFORE binding on_executor_finished_delegate.
    """
    global _active_session
    if not _GATE_CLIENT_AVAILABLE:
        raise RuntimeError(f"Gate client unavailable: {_GATE_IMPORT_ERROR}")

    _active_session = MnemoSessionState(
        project_name=project_name,
        level_name=level_name,
        scan_dir=scan_dir,
        cert_output_dir=cert_output_dir,
        operator=operator,
        source_model=source_model,
        source_pipeline=source_pipeline,
    )
    _log(
        f"Session {_active_session.session_id} initialized — "
        f"gate={GATE_URL} (SÖZLEŞME 2: loopback TCP)"
    )
    return _active_session


# ─── Delegate Callback ────────────────────────────────────────────────────────

def on_mrq_finished_callback(executor, pipeline_params):
    """
    Delegate callback bound via:
      executor.on_executor_finished_delegate.add_callable(on_mrq_finished_callback)

    Called by UE5 when all Movie Render Queue jobs complete.
    Confirmed binding surface: on_executor_finished_delegate (UE5 5.7.4 probe).

    Scans scan_dir for PNG/EXR frame files, submits each to Gate API,
    produces Ed25519 Passport on full approval or blocks fail-closed.
    """
    state = _active_session
    if state is None:
        _log_err("on_mrq_finished_callback: no active session — call begin_session() first.")
        return

    # ── Resolve scan directory ────────────────────────────────────────────────
    if state.scan_dir and state.scan_dir.exists():
        scan_dir = state.scan_dir
    elif _UE5_CONTEXT:
        scan_dir = Path(unreal.Paths.project_saved_dir()) / "MovieRenders"
    else:
        _log_err("scan_dir not set and not in UE5 context.")
        state.abort_reason = "scan_dir unavailable"
        return

    _log(f"Scanning output dir: {scan_dir}")

    # ── Collect rendered frames (sorted, deterministic) ───────────────────────
    frame_files: list[Path] = []
    if scan_dir.exists():
        frame_files = sorted(
            f for f in scan_dir.rglob("*")
            if f.suffix.lower() in (".png", ".exr") and f.is_file()
        )

    if not frame_files:
        state.abort_reason = f"No rendered frames found in {scan_dir}"
        _log_err(f"FAIL-CLOSED: {state.abort_reason}")
        return

    _log(f"Found {len(frame_files)} frames — submitting to Gate.")

    # ── Submit each frame (fail-closed on first rejection) ────────────────────
    for i, fp in enumerate(frame_files):
        frame_bytes = fp.read_bytes()
        frame_id = f"{state.session_id}-{fp.stem}-{i:04d}"

        _log(f"[{i:03d}] Submitting {fp.name} → {GATE_URL}/submit")

        try:
            result = submit_frame(
                frame_bytes=frame_bytes,
                frame_id=frame_id,
                frame_index=i,
                session_id=state.session_id,
                benchmark_run_id=state.benchmark_run_id,
                operator=state.operator,
                source_model=state.source_model,
                source_pipeline=state.source_pipeline,
                force_fail=False,
                gate_url=GATE_URL,
            )
        except RuntimeError as exc:
            state.abort_reason = f"Gate communication error at frame[{i}]: {exc}"
            _log_err(f"FAIL-CLOSED: {state.abort_reason}")
            return

        state.frame_results.append(result)

        if result.verdict != "APPROVED":
            viol = (result.violations[0].get("detail", "unknown")
                    if result.violations else "unknown")
            state.abort_reason = (
                f"frame[{i}] {frame_id} REJECTED — {viol} "
                f"(quarantine_id={result.quarantine_record_id})"
            )
            _log_err(f"FAIL-CLOSED: {state.abort_reason}")
            _log_err("No certification issued.")
            return

        _log(
            f"[{i:03d}] APPROVED ψ=1 | "
            f"{result.client_latency_ms:.1f}ms | ledger={result.ledger_record_id}"
        )

    # ── All frames approved — produce certification ───────────────────────────
    n = len(state.frame_results)
    _log(f"All {n} frames APPROVED ψ=1 — producing passport.")

    if state.cert_output_dir:
        output_dir = state.cert_output_dir
    elif _UE5_CONTEXT:
        output_dir = Path(
            unreal.Paths.project_saved_dir(), "MnemosyneCertification", state.session_id
        )
    else:
        output_dir = scan_dir / "MnemosyneCertification" / state.session_id

    manifest = build_manifest(
        project_name=state.project_name,
        level_or_scene_name=state.level_name,
        output_dir=output_dir,
        frame_paths=frame_files,
        operator=state.operator,
        node_id="MNEMOSYNE-NODE-01",
        export_session_id=state.session_id,
        source_pipeline=state.source_pipeline,
        source_model=state.source_model,
    )
    manifest_path = write_manifest(manifest, output_dir)
    state.manifest_path = manifest_path

    passport_path = produce_passport(
        session_id=state.session_id,
        output_dir=output_dir,
        frame_results=state.frame_results,
        benchmark_run_id=state.benchmark_run_id,
        manifest_path=str(manifest_path),
    )
    state.certified = True

    _log(f"CERTIFIED — Passport: {passport_path}")
    _log(f"Manifest:  {manifest_path}")


# ─── Self-test ────────────────────────────────────────────────────────────────

def _self_test():
    """Verify imports and Gate reachability. No UE5 required."""
    import urllib.request
    if not _GATE_CLIENT_AVAILABLE:
        print(f"FAIL: gate client unavailable — {_GATE_IMPORT_ERROR}")
        sys.exit(1)
    try:
        with urllib.request.urlopen("http://127.0.0.1:8765/health", timeout=5) as r:
            data = json.loads(r.read())
        assert data.get("status") == "healthy"
        print(f"PASS: gate-api healthy — version={data.get('version')}")
    except Exception as e:
        print(f"FAIL: gate-api unreachable — {e}")
        sys.exit(1)
    print(f"PASS: UE5_CONTEXT={_UE5_CONTEXT} | cryptography={_GATE_CLIENT_AVAILABLE}")
    print("mnemo_ue5_executor.py self-test PASS")


if __name__ == "__main__":
    _self_test()
