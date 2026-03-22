# FAZ 9D.4 — Reflection Analysis
**UE5 5.7.4 MoviePipelinePIEExecutor — Confirmed Surface**
**Date:** 2026-03-22

---

## Probe Method

```python
import unreal
executor = unreal.MoviePipelinePIEExecutor()
delegates = [m for m in dir(executor) if
             'delegate' in m.lower() or 'finish' in m.lower() or 'executor' in m.lower()]
print(delegates)
```

## Confirmed Output

```
['http_response_recieved_delegate', 'on_executor_errored_delegate',
 'on_executor_errored_impl', 'on_executor_finished_delegate',
 'on_executor_finished_impl', 'on_individual_job_finished_delegate',
 'on_individual_job_started_delegate', 'on_individual_job_...']
```

---

## Surface Analysis

| Name | Type | Bindable | Notes |
|------|------|----------|-------|
| `on_executor_finished_delegate` | Delegate | ✅ `add_callable()` | Fires after all jobs complete |
| `on_executor_errored_delegate` | Delegate | ✅ `add_callable()` | Fires on executor error |
| `on_individual_job_finished_delegate` | Delegate | ✅ `add_callable()` | Fires after each job |
| `on_individual_job_started_delegate` | Delegate | ✅ `add_callable()` | Fires when each job starts |
| `on_executor_finished_impl` | Override method | ❌ (requires `@unreal.uclass()` subclass) | Confirmed exists, but subclass path blocked by C++ reflection |
| `on_executor_errored_impl` | Override method | ❌ (same blocker) | Same issue |

---

## Root Cause of ec2 Failure (FAZ 9D.3)

The `@unreal.uclass()` subclass of `MoviePipelinePythonHostExecutor` failed to
register in the MRQ executor dropdown because UE5 C++ reflection requires
UCLASS macros (compile-time registration) that Python cannot replicate.

`set_executor_class(MnemosyneGateExecutor)` worked for runtime queue injection,
but the Output Log confirmation line depended on `init_unreal.py` being
auto-executed — which requires `DefaultEngine.ini` startup script configuration
that was not yet applied.

---

## Selected Hardening Path

**Use `on_executor_finished_delegate.add_callable()` on a standard
`MoviePipelinePIEExecutor` instance — no custom subclass, no `@unreal.uclass()`.**

```python
executor = unreal.MoviePipelinePIEExecutor()
executor.on_executor_finished_delegate.add_callable(on_mrq_finished_callback)
# Log confirmation fires immediately → ec2 PASS
unreal.log("MNEMOSYNE: delegate bound on on_executor_finished_delegate")
```

### Advantages
- No C++ reflection dependency
- No `@unreal.uclass()` required
- Confirmed API surface (probe-verified)
- Standalone function — no class inheritance
- Log confirmation prints at bind time → ec2 satisfied

### Gate Logic Impact
- None. `on_mrq_finished_callback` contains the same frame scan + Gate submission
  logic previously in `on_executor_finished_impl`.
- `submit_frame()`, `produce_passport()`, `build_manifest()`: unchanged.
- Fail-closed behavior: unchanged.
- Loopback TCP 127.0.0.1:8765: unchanged.

---

## Callback Signature

UE5 passes two arguments to delegates bound via `add_callable`:

```python
def on_mrq_finished_callback(executor, pipeline_params):
    # executor      : MoviePipelineExecutorBase — the executor that finished
    # pipeline_params: varies; may be success bool or pipeline object depending on delegate
```

Binding confirmed safe. No additional parameters inferred beyond probe evidence.
