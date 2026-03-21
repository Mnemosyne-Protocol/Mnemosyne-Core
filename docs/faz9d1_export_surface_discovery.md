# FAZ 9D.1 — TASK 5: UE5 Export Surface Discovery

**Node:** MNEMOSYNE-NODE-01
**Date:** 2026-03-21
**Status:** DESIGN COMPLETE — Implementation pending UE5 installation

---

## Overview

This document maps all viable UE5 export hook surfaces and selects the MVP integration point for Mnemosyne Gate.

---

## 1. Export Surface Candidates

### Surface A — Python Editor Scripting (RECOMMENDED MVP)

**API:** `unreal.MoviePipelineQueueEngineSubsystem` + `unreal.register_slate_post_tick_callback()`

**How it works:**
```python
# Registered in Project Settings → Python → Startup Scripts
import unreal

def on_render_finished(pipeline, success):
    """Called by MRQ after every render job completes."""
    if not success:
        return
    # Collect frame output paths
    output_dir = pipeline.get_configuration().get_output_settings().output_directory.path
    # → Submit to Mnemosyne Gate via 127.0.0.1:8765
    submit_to_gate(output_dir)

subsystem = unreal.get_editor_subsystem(unreal.MoviePipelineQueueEngineSubsystem)
subsystem.on_individual_job_finished.add_callable(on_render_finished)
```

**Pros:**
- No C++ required — Blueprint project sufficient
- Full Python 3.x interpreter embedded in UE5 (3.11.x)
- stdlib `urllib.request` available — no external deps
- Direct access to MRQ output paths, job metadata
- Can run inline with editor (no separate process)
- Identical attestation payload shape to `faz9c/ue5_export_hook.py`

**Cons:**
- Python UE5 API changes between engine versions (5.3 → 5.5 has minor renames)
- Editor-only (not available in packaged/commandlet build without plugin)

**Verdict:** ✓ MVP path. Lowest friction, no build tools required.

---

### Surface B — Editor Utility Blueprint (EUB)

**API:** `Editor Utility Widget` with `Run Python Script` node or custom BP event

**How it works:**
- Create `Editor Utility Blueprint`
- Override `OnMoviePipelineExecutorFinished` delegate
- Call Python script via `Execute Python Command` node

**Pros:**
- Visual; no Python expertise needed for wiring
- Can trigger Mnemosyne check from Toolbar button

**Cons:**
- Delegates Python execution to a subprocess — less direct
- Harder to pass structured data (frame list, metadata)
- Blueprint graph is not version-controlled cleanly

**Verdict:** Secondary option. Use as UI trigger wrapper if needed.

---

### Surface C — C++ FAssetExportTask

**API:** `FAssetExportTask`, `UExporter`, `IAssetTools`

**How it works:**
```cpp
FAssetExportTask Task;
Task.Object = AssetToExport;
Task.Exporter = NewObject<UMnemosyneExporter>();
Task.Filename = OutputPath;
UExporter::RunAssetExportTask(Task);
```

**Pros:**
- Tightest engine integration
- Can intercept pre/post export at any asset type
- Plugin distributable via Marketplace

**Cons:**
- Requires Xcode full IDE (NOT installed on NODE-01)
- Plugin build: `~/UnrealEngine/GenerateProjectFiles.sh` + `xcodebuild`
- ~1–2 week implementation vs. 1 day for Python

**Verdict:** FAZ 9E target. Not for MVP.

---

### Surface D — CommandLet

**API:** `UCommandlet`, `-run=MnemosyneGateCommandlet`

**How it works:**
```bash
/path/to/UnrealEditor-Cmd MnemosyneHookMVP.uproject \
  -run=MnemosyneGateCommandlet \
  -session_dir=/path/to/export \
  -gate_url=http://127.0.0.1:8765
```

**Pros:**
- Headless — no editor UI needed
- CI/CD friendly
- Can be triggered from shell scripts, Makefile, cron

**Cons:**
- Also requires C++ for commandlet registration
- No Python access in commandlet without separate setup

**Verdict:** Production path (FAZ 9E). Pairs with C++ plugin.

---

## 2. Movie Render Queue Architecture

```
[UE5 Editor]
    └── Movie Render Queue (MRQ)
          ├── Queue: List of render jobs
          ├── Job: Scene + configuration + output settings
          │     └── Output: frame images + metadata
          └── Executor: MoviePipelineQueueEngineSubsystem
                ├── on_executor_errored_delegate
                ├── on_executor_finished_delegate        ← HOOK POINT A (batch done)
                └── on_individual_job_finished_delegate  ← HOOK POINT B (per-job done)
```

**Target hook point for MVP:** `on_individual_job_finished_delegate` (Hook Point B)
- Fires once per job (each job = one rendered sequence)
- Provides: `UMoviePipeline` object with full output configuration
- Post-hook: iterate output frames → build attestation → submit to Gate

---

## 3. Python Startup Script Architecture

UE5 Python startup scripts run when the editor opens:
- Location: Project Settings → Plugins → Python → Startup Scripts
- Or: `Content/Python/init_unreal.py` (auto-loaded convention)

**MVP startup script location:**
```
MnemosyneHookMVP/
  Content/
    Python/
      init_unreal.py            ← auto-loaded by UE5
      mnemosyne_hook/
        __init__.py
        gate_client.py          ← urllib.request POST to 127.0.0.1:8765
        hook_registrar.py       ← registers MRQ delegate
        frame_attestation.py    ← builds attestation from UE5 frame metadata
        session_certifier.py    ← wraps ue5_export_hook.UE5ExportHook logic
```

---

## 4. Attestation Data Available from UE5 Python

| Attestation Field | UE5 Source | Notes |
|-------------------|------------|-------|
| `frame_id` | Job name + frame number | Deterministic |
| `session_id` | Job name | Set by operator |
| `source_model` | `"ue5-lumen"` literal | Fixed for Lumen render |
| `source_pipeline` | `"ue5-mrq-post-job"` literal | Identifies hook surface |
| `render_fingerprint.roi_hashes` | Frame image files (PNG/EXR) | Computed post-export |
| `source_invariants` | Scene manifest hash | Requires `canonical_scene_manifest.json` |
| `signature` | Ed25519 signing key | `/tmp/faz9c_ed25519.pem` (reuse) |
| `hash_mode` | `"KS-salted"` | Fixed |
| `metrics.emissive_budget` | Luminance measurement | Requires EXR beauty pass |

---

## 5. Selected MVP Architecture

```
[UE5 Editor]
  init_unreal.py (auto-loaded on editor start)
    └── hook_registrar.py
          └── registers on_individual_job_finished_delegate

[User triggers MRQ render]
  MRQ Executor renders sequence → job complete
    └── on_individual_job_finished fires
          └── session_certifier.process_session(output_dir)
                ├── For each frame: build attestation → POST 127.0.0.1:8765/submit
                ├── All ψ=1: produce Mnemosyne_Certified_Passport.json
                └── Any ψ=0: fail-closed, no passport, quarantine written by gate-api
```

**SÖZLEŞME 2 compliance:** All gate communication via `urllib.request` to `127.0.0.1:8765` only.

---

## 6. Deferred Surfaces (FAZ 9E)

| Surface | Blocker | Target Phase |
|---------|---------|--------------|
| C++ FAssetExportTask | Xcode full IDE required | FAZ 9E |
| CommandLet | C++ required | FAZ 9E |
| UE5 Marketplace Plugin | C++ + plugin signing | FAZ 9F |
| CI/CD headless render | CommandLet dependency | FAZ 9E |
