"""
init_unreal.py — Mnemosyne FAZ 9D.2
=====================================
Mnemosyne v3.0.0 · DOI: 10.5281/zenodo.18884426

UE5 Python startup script — auto-executed by PythonScriptPlugin on editor start.

DEPLOYMENT:
  Place at: MnemosyneHookMVP/Content/Python/init_unreal.py
  UE5 executes all scripts in Content/Python/ on editor start when
  PythonScriptPlugin is enabled (AdditionalPaths configured in DefaultEngine.ini
  or startup_scripts in plugin settings).

EFFECT:
  Registers MnemosyneGateExecutor as the active executor for the project's
  Movie Render Queue subsystem. From this point, all MRQ jobs will run
  through the Mnemosyne fail-closed gate path.

OPERATOR NOTES:
  - Gate API must be running at 127.0.0.1:8765 BEFORE editor launch.
  - Check: curl http://127.0.0.1:8765/health
  - This script is idempotent: safe to re-execute.
  - See docs/faz9d2_operator_flow.md for full workflow.
"""

from __future__ import annotations

import sys

try:
    import unreal
except ImportError:
    # Not inside UE5 — silently skip (safe for CI import)
    print("[mnemo/init_unreal] Not in UE5 context — skipping executor registration.")
    sys.exit(0)

try:
    from mnemo_ue5_executor import MnemosyneGateExecutor
    _EXECUTOR_AVAILABLE = True
except Exception as e:
    _EXECUTOR_AVAILABLE = False
    _EXECUTOR_ERROR = str(e)

try:
    import urllib.request, json
    with urllib.request.urlopen("http://127.0.0.1:8765/health", timeout=5) as resp:
        health = json.loads(resp.read())
    _GATE_LIVE = health.get("status") == "healthy"
    _GATE_VERSION = health.get("version", "unknown")
except Exception as _ge:
    _GATE_LIVE = False
    _GATE_VERSION = "unreachable"
    _GATE_ERROR = str(_ge)


def _register_executor():
    if not _EXECUTOR_AVAILABLE:
        unreal.log_error(f"MNEMOSYNE: Executor import failed — {_EXECUTOR_ERROR}")
        unreal.log_error("MNEMOSYNE: MRQ jobs will NOT be gated. Fix import before rendering.")
        return

    if not _GATE_LIVE:
        unreal.log_error(
            f"MNEMOSYNE: gate-api unreachable at 127.0.0.1:8765 — "
            f"start Docker stack before launching editor."
        )
        unreal.log_error("MNEMOSYNE: MRQ jobs will NOT be gated. Fix gate before rendering.")
        return

    try:
        subsystem = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
        subsystem.get_queue().set_executor_class(MnemosyneGateExecutor)
        unreal.log(
            f"MNEMOSYNE: Executor registered — gate={_GATE_VERSION} | "
            f"transport=127.0.0.1:8765 (SÖZLEŞME 2: loopback TCP)"
        )
        unreal.log("MNEMOSYNE: All MRQ jobs will route through Mnemosyne fail-closed gate.")
    except Exception as e:
        unreal.log_error(f"MNEMOSYNE: Executor registration failed — {e}")
        unreal.log_error("MNEMOSYNE: MRQ jobs will NOT be gated.")


# Auto-execute on editor start
_register_executor()
