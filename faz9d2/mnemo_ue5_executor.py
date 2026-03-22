"""
mnemo_ue5_executor.py — Mnemosyne FAZ 9D.2
============================================
Mnemosyne v3.0.0 · DOI: 10.5281/zenodo.18884426

Real UE5 Python hook — MoviePipelinePythonHostExecutor subclass.

DEPLOYMENT TARGET: Inside UE5 editor process (Python Script Plugin).
  Place at: MnemosyneHookMVP/Content/Python/mnemo_ue5_executor.py
  Companion: MnemosyneHookMVP/Content/Python/init_unreal.py (auto-registered)

ARCHITECTURE (frozen — FAZ 9D.1):
  Surface   : MoviePipelinePythonHostExecutor (Python Editor Scripting)
  Transport : HTTP/1.1 Loopback TCP — 127.0.0.1:8765 ONLY (SÖZLEŞME 2)
  Schema    : scene_manifest_v1 (frozen)
  Taxonomy  : v1.1 (frozen)
  Contracts : Gate API FrameSubmission (frozen — gate-api/main.py)

UE5 5.7.4 API NOTE:
  MoviePipelinePythonHostExecutor valid overrides (confirmed via UE5 API query):
    cancel_all_jobs, cancel_current_job,
    on_executor_finished_delegate, on_executor_finished_impl
  on_individual_shot_work_finished_impl does NOT exist in UE5 5.7.
  All frame processing is done in on_executor_finished_impl (post-render).

FAIL-CLOSED GUARANTEE:
  Any frame with psi=0 → quarantine written by gate-api → error logged
  → No passport generated → No partial certification.
  Communication error → same outcome.
  Render job completes before Gate evaluation; certification is blocked post-render.

OPERATOR NOTES:
  - PythonScriptPlugin must be enabled in MnemosyneHookMVP.uproject
  - Gate API must be running at 127.0.0.1:8765 before editor launch
  - See docs/faz9d2_operator_flow.md for exact workflow
"""

from __future__ import annotations

import json
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── UE5 import guard ──────────────────────────────────────────────────────────
# 'unreal' module only exists inside the UE5 editor process.
# When imported outside UE5 (e.g., test harness), _UE5_CONTEXT = False.
try:
    import unreal
    _UE5_CONTEXT = True
except ImportError:
    _UE5_CONTEXT = False

# ── Mnemosyne Gate client (project-local, no engine dep) ─────────────────────
# These files are co-located at Content/Python/ in the project.
try:
    from mnemo_gate_client import (
        submit_frame, produce_passport,
        FrameGateResult,
        GATE_URL, GATE_VERSION, POLICY_PACK_VERSION,
    )
    from mnemo_manifest import build_manifest, write_manifest
    _GATE_CLIENT_AVAILABLE = True
except ImportError as _imp_err:
    _GATE_CLIENT_AVAILABLE = False
    _GATE_IMPORT_ERROR = str(_imp_err)


# ─── Session State ────────────────────────────────────────────────────────────

@dataclass
class MnemoSessionState:
    """Mutable state for one Movie Render Queue job."""
    session_id: str = field(default_factory=lambda: f"ue5-{uuid.uuid4().hex[:12]}")
    benchmark_run_id: str = ""
    operator: str = "ks@mnemosynelabs.ai"
    source_model: str = "UE5_LUMEN"
    source_pipeline: str = "UE5_MRQ"
    project_name: str = "MnemosyneHookMVP"
    level_name: str = "Unknown"
    output_dir: Optional[Path] = None
    # output_dir_override: set from job output settings during execute_delayed
    output_dir_override: Optional[Path] = None
    frame_results: list = field(default_factory=list)
    certified: bool = False
    abort_reason: Optional[str] = None
    manifest_path: Optional[Path] = None

    def __post_init__(self):
        self.benchmark_run_id = f"ue5-{self.session_id}-{uuid.uuid4().hex[:8]}"


# ─── UE5 Executor (MoviePipelinePythonHostExecutor subclass) ──────────────────

if _UE5_CONTEXT:
    @unreal.uclass()
    class MnemosyneExecutor(unreal.MoviePipelinePythonHostExecutor):
        """
        Mnemosyne Gate hook for Movie Render Queue.

        Registered by init_unreal.py as the active executor for
        the MnemosyneHookMVP project's Movie Render Queue subsystem.

        UE5 5.7.4 override surface: on_executor_finished_impl only.
        (on_individual_shot_work_finished_impl does not exist in UE5 5.7.)

        Flow:
          execute_delayed  → bootstrap session state, start render via super()
          on_executor_finished_impl → render complete; scan output dir;
                                      submit each frame to Gate;
                                      PASS: produce passport
                                      FAIL: log error, no passport (fail-closed)
        """

        @unreal.ufunction(override=True)
        def execute_delayed(self, pipeline_queue: unreal.MoviePipelineQueue):
            """Bootstrap session state. Store queue ref. Start render via super()."""
            if not _GATE_CLIENT_AVAILABLE:
                unreal.log_error(f"MNEMOSYNE: Gate client unavailable — {_GATE_IMPORT_ERROR}")
                raise RuntimeError("Mnemosyne gate client not found — abort")

            self._state = MnemoSessionState()
            self._pipeline_queue = pipeline_queue

            # Extract level name and output dir from first job
            jobs = pipeline_queue.get_jobs()
            if jobs:
                job = jobs[0]
                map_pkg = job.map
                self._state.level_name = str(map_pkg.asset_name) if map_pkg else "Unknown"
                # Try to get configured output directory from job settings
                try:
                    cfg = job.get_configuration()
                    out_setting = cfg.find_setting_by_class(unreal.MoviePipelineOutputSetting)
                    if out_setting:
                        raw_path = str(out_setting.output_directory.path)
                        # Resolve {project_dir} token
                        resolved = unreal.Paths.convert_relative_path_to_full(
                            raw_path.replace("{project_dir}", unreal.Paths.project_dir())
                        )
                        self._state.output_dir_override = Path(resolved)
                except Exception as e:
                    unreal.log_warning(f"MNEMOSYNE: could not resolve output dir from job: {e}")

            unreal.log(
                f"MNEMOSYNE: Session {self._state.session_id} started — "
                f"gate={GATE_URL} | level={self._state.level_name} "
                f"(SÖZLEŞME 2: loopback TCP)"
            )

            # Start the actual render
            super().execute_delayed(pipeline_queue)

        @unreal.ufunction(override=True)
        def on_executor_finished_impl(self):
            """
            Called by UE5 after all render jobs in the queue complete.

            Scans the render output directory for PNG/EXR files, submits each
            to gate-api (127.0.0.1:8765), and certifies or blocks fail-closed.

            PASS path: all frames psi=1 → Mnemosyne_Certified_Passport.json written.
            FAIL path: first frame psi=0 → processing stops, no passport, error logged.
            """
            state = self._state

            # ── Resolve output directory ──────────────────────────────────────
            # Priority: (1) override from job settings, (2) UE5 default renders path
            if state.output_dir_override and state.output_dir_override.exists():
                scan_dir = state.output_dir_override
            else:
                scan_dir = Path(unreal.Paths.project_saved_dir()) / "MovieRenders"

            unreal.log(f"MNEMOSYNE: Scanning output dir: {scan_dir}")

            # ── Collect rendered frame files (sorted, deterministic) ──────────
            frame_files: list[Path] = []
            if scan_dir.exists():
                frame_files = sorted(
                    f for f in scan_dir.rglob("*")
                    if f.suffix.lower() in (".png", ".exr") and f.is_file()
                )

            if not frame_files:
                state.abort_reason = f"No rendered frames found in {scan_dir}"
                unreal.log_error(f"MNEMOSYNE FAIL-CLOSED: {state.abort_reason}")
                return

            unreal.log(f"MNEMOSYNE: Found {len(frame_files)} frames — submitting to Gate.")

            # ── Submit each frame to Gate API (fail-closed on first rejection) ─
            for i, fp in enumerate(frame_files):
                frame_bytes = fp.read_bytes()
                frame_id = f"{state.session_id}-{fp.stem}-{i:04d}"

                unreal.log(f"MNEMOSYNE: [{i:03d}] Submitting {fp.name} → {GATE_URL}/submit")

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
                    unreal.log_error(f"MNEMOSYNE FAIL-CLOSED: {state.abort_reason}")
                    return

                state.frame_results.append(result)

                if result.verdict != "APPROVED":
                    viol = (result.violations[0].get("detail", "unknown")
                            if result.violations else "unknown")
                    state.abort_reason = (
                        f"frame[{i}] {frame_id} REJECTED — {viol} "
                        f"(quarantine_id={result.quarantine_record_id})"
                    )
                    unreal.log_error(f"MNEMOSYNE FAIL-CLOSED: {state.abort_reason}")
                    unreal.log_error("MNEMOSYNE: No certification issued.")
                    return

                unreal.log(
                    f"MNEMOSYNE: [{i:03d}] APPROVED ψ=1 | "
                    f"{result.client_latency_ms:.1f}ms | ledger={result.ledger_record_id}"
                )

            # ── All frames approved — produce certification ────────────────────
            n = len(state.frame_results)
            unreal.log(f"MNEMOSYNE: All {n} frames APPROVED ψ=1 — producing passport.")

            output_dir = Path(
                unreal.Paths.project_saved_dir(), "MnemosyneCertification", state.session_id
            )

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

            unreal.log(f"MNEMOSYNE: CERTIFIED — Passport: {passport_path}")
            unreal.log(f"MNEMOSYNE: Manifest:  {manifest_path}")

else:
    # ── Non-UE5 context: stub class for import safety ─────────────────────────
    class MnemosyneExecutor:  # type: ignore[no-redef]
        """
        Stub — not inside UE5 editor process.
        Real class requires UE5 Python environment.
        Use run_faz9d2.py for standalone Gate submission testing.
        """
        def __init__(self):
            raise RuntimeError(
                "MnemosyneExecutor requires UE5 editor Python environment. "
                "Use run_faz9d2.py for standalone proof runs."
            )


# ─── Self-test (runs without UE5) ────────────────────────────────────────────

def _self_test():
    """Verify gate client imports and Gate reachability. No UE5 required."""
    import urllib.request
    if not _GATE_CLIENT_AVAILABLE:
        print(f"FAIL: gate client unavailable — {_GATE_IMPORT_ERROR}")
        sys.exit(1)

    try:
        with urllib.request.urlopen("http://127.0.0.1:8765/health", timeout=5) as r:
            data = json.loads(r.read())
        assert data.get("status") == "healthy", f"unexpected: {data}"
        print(f"PASS: gate-api healthy — version={data.get('version')}")
    except Exception as e:
        print(f"FAIL: gate-api unreachable — {e}")
        sys.exit(1)

    print(f"PASS: UE5_CONTEXT={_UE5_CONTEXT} | cryptography={_GATE_CLIENT_AVAILABLE}")
    print("mnemo_ue5_executor.py self-test PASS")


if __name__ == "__main__":
    _self_test()
