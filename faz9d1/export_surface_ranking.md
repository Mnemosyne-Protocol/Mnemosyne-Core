# FAZ 9D.1 — TASK 5: Export Surface Ranking
**ec:** ec5_export_surface_ranked
**Date:** 2026-03-21

## Candidates Evaluated

### Option A: Python Editor Scripting (PythonScriptPlugin)
**Hook Surface:** `startup_scripts/` + `MoviePipelinePythonHostExecutor`

| Criterion | Score | Notes |
|-----------|-------|-------|
| Compilation required | ✅ None | Prebuilt plugin binaries exist |
| UE5 version coupling | ✅ Low | Python API is stable across 5.x |
| Deployment complexity | ✅ Minimal | Drop `.py` files into project |
| Hook granularity | ✅ Frame-level | `OnMoviePipelineFinished`, per-frame callbacks |
| Gate API access | ✅ Full | `urllib.request` / `http.client` — stdlib only |
| Fail-closed enforcement | ✅ Native | Exception stops pipeline |
| CI/CD integration | ✅ Easy | `UnrealEditor -ExecutePythonScript=...` headless |
| Risk | 🟢 LOW | No compile step, no C++ ABI dependency |

**Verdict: SELECTED — MVP Surface**

---

### Option B: Editor Utility Widget / Blueprint
**Hook Surface:** Blueprint event graph + `EditorUtilityLibrary`

| Criterion | Score | Notes |
|-----------|-------|-------|
| Compilation required | ✅ None | Blueprint only |
| Hook granularity | ⚠️ Coarse | No per-frame callback; post-render only |
| Gate API access | ❌ Indirect | HTTP requires custom Blueprint node or Python bridge |
| Fail-closed enforcement | ⚠️ Fragile | Blueprint exceptions don't halt render pipeline natively |
| CI/CD integration | ❌ Hard | GUI-bound; no headless invocation |
| Risk | 🟡 MEDIUM | Better UX for manual use, worse for automation |

**Verdict: REJECTED for MVP** (possible future UX layer)

---

### Option C: C++ Plugin
**Hook Surface:** `IMoviePipelineExecutor`, `FMovieSceneExportMetadata`

| Criterion | Score | Notes |
|-----------|-------|-------|
| Hook granularity | ✅ Finest | Full access to all pipeline delegates |
| Gate API access | ✅ Full | libcurl / platform HTTP |
| Fail-closed enforcement | ✅ Strongest | Can abort at engine level |
| Compilation required | ❌ Required | ~20 min Xcode build on M3 |
| UE5 version coupling | ❌ High | ABI breaks on minor updates |
| Deployment | ❌ Complex | Requires `Build.bat` + packaging |
| Risk | 🔴 HIGH for MVP | Over-engineered for FAZ 9D scope |

**Verdict: DEFERRED to FAZ 9E+ (production hardening phase)**

---

## Decision

```
MVP Surface = Python Editor Scripting via PythonScriptPlugin
Hook entry  = MoviePipelinePythonHostExecutor (per-render job)
Fallback    = startup_scripts/ + PostEditorTick callback (per-frame file watcher)
```

**Rationale:** Zero compile cost. Stdlib HTTP. Frame-level interception via
`MoviePipelinePythonHostExecutor.receive_executor_finished_impl()` and the
`on_individual_shot_work_finished` callback. Fail-closed: Python `raise` inside
a UE5 pipeline executor propagates as a pipeline abort.
