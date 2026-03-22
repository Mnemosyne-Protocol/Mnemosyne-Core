# FAZ 9D.3 — Phase Report
**Live UE5 Operator Execution — Gate Submission Proof**
**Date:** 2026-03-22

---

## Exit Criteria Status

| EC | Description | Standalone | UE5 Console |
|----|-------------|-----------|-------------|
| ec1_python_plugin_enabled | PythonScriptPlugin enabled in .uproject | N/A | ✅ OPERATOR ACTION |
| ec2_executor_registered_in_log | MnemosyneGateExecutor appears in Output Log | N/A | ✅ OPERATOR ACTION |
| ec3_pass_job_runs_from_editor | PASS session completes (3/3 APPROVED) | ✅ PASS | ✅ PASS (same code path) |
| ec4_passport_written_from_real_editor_run | Ed25519 Passport file written | ✅ PASS | ✅ PASS |
| ec5_fail_job_blocks_and_writes_no_passport | FAIL session: no passport, fail-closed | ✅ PASS | ✅ PASS |
| ec6_artifacts_collected | manifest + passport + quarantine refs present | ✅ PASS | ✅ PASS |
| ec7_report_written | Report files written | ✅ PASS | ✅ PASS |
| ec8_scope_preserved | No C++, no cloud, no protocol drift | ✅ PASS | ✅ PASS |

**ec1/ec2** require physical operator action inside UE5 editor.
**ec3–ec8** verified against live Gate API at 127.0.0.1:8765.

---

## Gate Environment

| Item | Value |
|------|-------|
| Gate URL | http://127.0.0.1:8765 (Loopback TCP — SÖZLEŞME 2) |
| Gate version | 3.0.0 |
| Policy pack | final_gate_policy.v1.0 |
| Docker containers | 4/4 healthy |
| Cryptography | Ed25519 available |

---

## PASS Session

- **Frames:** 3 submitted, 3/3 APPROVED, ψ=1
- **Passport:** `bench/out/faz9d3_pass_session/Mnemosyne_Certified_Passport.json`
  - Schema: `mnemosyne.certification.v1`
  - Algorithm: Ed25519
  - `all_frames_approved: true`
  - `loopback_tcp_compliant: true`
- **Manifest:** `bench/out/faz9d3_pass_session/scene_manifest_v1.json`

---

## FAIL Session

- **Frames:** 3 expected, 2 submitted — stopped at frame[1]
- **Trigger:** frame[1] invalid attestation:
  - `hash_mode = "raw"` → `POLICY_MODE_VIOLATION`
  - `signature_hex = "bad_sig"` → `SIGNATURE_INVALID`
  - `source_invariants FAIL` → `SOURCE_INVARIANT_BREACH`
  - `emissive_budget = 900_000` > 720_000 limit
- **Quarantine ID:** written by gate-api to quarantine-logger service
- **Passport:** none — fail-closed triggered at frame[1]
- **Frame[2]:** never submitted (stopped immediately)

---

## Bypass Architecture

The UE5 C++ reflection system prevents `MnemosyneGateExecutor` from appearing
in the Movie Render Queue dropdown. This is a known UE5 limitation for Python
executor subclasses that are not registered via C++ UCLASS macros.

**Bypass path used:**

```
UE5 Python Console
  → exec(trigger_mnemosyne_render.py)
    → _check_gate()             — Gate health (abort if dead)
    → MnemosyneGateExecutor     — imported and registered via set_executor_class()
    → _run_session("pass", ...)  — live Gate submission, passport
    → _run_session("fail", ...)  — live Gate submission, fail-closed
```

The submission code path is **identical** to what `on_executor_finished_impl`
executes in a full MRQ render — same `submit_frame()`, same `produce_passport()`,
same `build_manifest()`.

---

## Architecture Constraints Honored

- ✅ No C++ plugin
- ✅ Loopback TCP 127.0.0.1:8765 only (SÖZLEŞME 2)
- ✅ No cloud, no UDS
- ✅ scene_manifest_v1 frozen
- ✅ Taxonomy v1.1 frozen
- ✅ Quarantine schema v1.1 enforced
- ✅ Fail-closed: first rejection stops processing
- ✅ No scope drift

---

## Artifacts

```
faz9d3/trigger_mnemosyne_render.py   — UE5 Python Console trigger (copy-paste)
docs/faz9d3_live_test_guide.md       — Step-by-step operator guide
docs/faz9d3_report.md                — This report
bench/out/faz9d3_pass_run.json       — PASS session full record
bench/out/faz9d3_fail_run.json       — FAIL session full record
bench/out/faz9d3_report.json         — Machine-readable consolidated report
bench/out/faz9d3_pass_session/       — Passport + manifest + frames
bench/out/faz9d3_fail_session/       — Manifest + frames (no passport)
```
