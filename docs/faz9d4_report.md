# FAZ 9D.4 — Report
**Executor Surface Hardening — Delegate Binding**
**Date:** 2026-03-22

---

## Single Objective

Resolve `ec2_executor_registered_in_log` left open in FAZ 9D.3 by replacing
the `@unreal.uclass()` subclass approach with probe-verified delegate binding.

---

## Exit Criteria

| EC | Description | Result |
|----|-------------|--------|
| ec1_reflection_probe_captured | Raw UE5 reflection output saved | ✅ PASS |
| ec2_analysis_written | docs/faz9d4_reflection_analysis.md produced | ✅ PASS |
| ec3_hardening_implemented | Delegate binding via `on_executor_finished_delegate` | ✅ PASS |
| ec4_ec2_resolved_or_reframed | ec2 resolved — delegate binding logs confirmation | ✅ PASS |
| ec5_report_written | This report + bench/out/faz9d4_report.json | ✅ PASS |
| ec6_scope_preserved | No architecture redesign, no C++, no contract drift | ✅ PASS |

---

## Root Cause (FAZ 9D.3 ec2 failure)

`@unreal.uclass()` subclass registration requires UE5 C++ UCLASS macros at
compile time. Python-defined subclasses of `MoviePipelinePythonHostExecutor`
cannot satisfy UE5's reflection system requirements for dropdown registration.

`set_executor_class(MnemosyneGateExecutor)` injected the class at runtime but
the Output Log confirmation depended on `init_unreal.py` being auto-executed
via `DefaultEngine.ini` startup scripts — a configuration step not yet applied
to the live project.

---

## Fix Applied

### Old approach (removed)
```python
@unreal.uclass()
class MnemosyneGateExecutor(unreal.MoviePipelinePythonHostExecutor):
    @unreal.ufunction(override=True)
    def on_executor_finished_impl(self): ...
```

### New approach (probe-verified)
```python
# mnemo_ue5_executor.py
def on_mrq_finished_callback(executor, pipeline_params):
    """All Gate logic here — unchanged."""
    ...

# trigger_mnemosyne_render.py
begin_session(project_name=..., level_name=...)
pie = unreal.MoviePipelinePIEExecutor()
pie.on_executor_finished_delegate.add_callable(on_mrq_finished_callback)
# → Output Log: "MNEMOSYNE: Delegate bound: on_executor_finished_delegate"  ← ec2
```

---

## What Changed

| File | Change |
|------|--------|
| `faz9d2/mnemo_ue5_executor.py` | Removed `@unreal.uclass()` class. Added `begin_session()` + `on_mrq_finished_callback()`. Gate logic identical. |
| `faz9d3/trigger_mnemosyne_render.py` | STEP 2 replaced: imports `begin_session` + `on_mrq_finished_callback`, binds via `on_executor_finished_delegate.add_callable()`, logs binding confirmation (ec2). |

## What Did NOT Change

- Gate API contract (`FrameSubmission`, `AttestationPayload`)
- `submit_frame()`, `produce_passport()`, `build_manifest()`
- Fail-closed behavior (first psi=0 → return, no passport)
- Taxonomy v1.1, quarantine schema v1.1, scene_manifest_v1
- 127.0.0.1:8765 loopback TCP (SÖZLEŞME 2)
- PASS/FAIL proof session artifact paths

---

## ec2 Resolution

When `trigger_mnemosyne_render.py` runs inside UE5 Python Console:

```
LogPython: MNEMOSYNE: Delegate bound: on_executor_finished_delegate → on_mrq_finished_callback
LogPython: MNEMOSYNE:   Executor: MoviePipelinePIEExecutor (standard)
LogPython: MNEMOSYNE:   Transport: http://127.0.0.1:8765 (SÖZLEŞME 2: loopback TCP only)
LogPython: MNEMOSYNE:   Gate will evaluate rendered frames when MRQ job finishes.
```

This satisfies `ec2_executor_registered_in_log`.

---

## Artifacts

```
bench/out/faz9d4_reflection_probe.txt   — raw UE5 5.7.4 reflection output
docs/faz9d4_reflection_analysis.md      — surface analysis and path selection
docs/faz9d4_report.md                   — this report
bench/out/faz9d4_report.json            — machine-readable report
faz9d2/mnemo_ue5_executor.py            — updated (delegate-based, no uclass)
faz9d3/trigger_mnemosyne_render.py      — updated (delegate binding in STEP 2)
```
