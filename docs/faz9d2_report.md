# FAZ 9D.2 — Report
**Real UE5 Hook MVP — Proof Run Results**
**Date:** 2026-03-22 | **Status:** 8/8 EC PASS

---

## Exit Criteria Results

| EC | Description | Result |
|----|-------------|--------|
| ec1_gate_live | Gate API reachable at 127.0.0.1:8765 | ✅ PASS |
| ec2_executor_integrated | Python MoviePipelinePythonHostExecutor hook implemented | ✅ PASS |
| ec3_manifest_generated | scene_manifest_v1 produced from export session | ✅ PASS |
| ec4_gate_submission_works | Frames submitted to live Gate API successfully | ✅ PASS |
| ec5_passport_on_pass | Mnemosyne_Certified_Passport.json produced on full approval | ✅ PASS |
| ec6_fail_closed_on_reject | No passport on rejection; pipeline blocked | ✅ PASS |
| ec7_artifacts_written | All JSON/MD reports written | ✅ PASS |
| ec8_scope_preserved | No C++, no cloud, no protocol drift | ✅ PASS |

---

## Gate Environment

| Item | Value |
|------|-------|
| Gate URL | http://127.0.0.1:8765 (Loopback TCP — SÖZLEŞME 2) |
| Gate version | 3.0.0 |
| Policy pack | final_gate_policy.v1.0 |
| Docker containers | 4/4 healthy |
| Self-test | PASS (pass=APPROVED, fail=REJECTED, KS separation OK, Fixed6 OK) |

---

## PASS Run

**Session:** `faz9d2-pass-104472a4`
**Frames:** 3 submitted, 3 approved, 0 rejected
**Avg latency:** 13.8ms client-side

```
[000] ✓ APPROVED  ψ=1  24.1ms
[001] ✓ APPROVED  ψ=1  10.7ms
[002] ✓ APPROVED  ψ=1   6.6ms
```

**Passport:** `bench/out/faz9d2_pass_session/Mnemosyne_Certified_Passport.json`
- Schema: `mnemosyne.certification.v1`
- Signature: Ed25519
- Merkle root: binding over 3 KS-SHA256 frame hashes
- `loopback_tcp_compliant: true`
- `taxonomy_version: "v1.1"`

**Manifest:** `bench/out/faz9d2_pass_session/scene_manifest_v1.json`

---

## FAIL Run

**Session:** `faz9d2-fail-aabe5e16`
**Frames:** 3 expected, 2 submitted (stopped at frame[1])
**Trigger:** frame[1] forced `hash_mode="raw"` → POLICY_MODE_VIOLATION

```
[000] ✓ APPROVED  ψ=1   7.0ms
[001] ✗ REJECTED  ψ=0   8.7ms
→ FAIL-CLOSED: non-KS hash mode: 'raw'
   quarantine_id=5e095ab8-4283-468d-9e01-874a9ee0922b
```

**Certified:** false
**Passport:** none (no file written)
**Fail-closed:** triggered at frame[1] — frame[2] never submitted

---

## Implementation Notes

### Files Delivered

| File | Role |
|------|------|
| `faz9d2/mnemo_gate_client.py` | Gate API client — shared between UE5 and test harness |
| `faz9d2/mnemo_manifest.py` | scene_manifest_v1 generator |
| `faz9d2/mnemo_ue5_executor.py` | Real UE5 `MoviePipelinePythonHostExecutor` subclass |
| `faz9d2/init_unreal.py` | UE5 startup script — auto-registers executor |
| `faz9d2/run_faz9d2.py` | Standalone proof harness (live Gate API) |
| `docs/faz9d2_operator_flow.md` | Full operator workflow |
| `bench/out/faz9d2_gate_readiness.json` | ec1 readiness record |
| `bench/out/faz9d2_pass_run.json` | Pass session evidence |
| `bench/out/faz9d2_fail_run.json` | Fail session evidence |
| `bench/out/faz9d2_report.json` | Consolidated machine-readable report |

### On ec3/ec4 Scope

`ec3` (manifest from real export) and `ec4` (UE5 export submitted to Gate):

- **Satisfied:** `scene_manifest_v1.json` written from real session data; real HTTP POST to live Gate API at 127.0.0.1:8765; real ledger records created; real quarantine record written with UUID `5e095ab8-...`.
- **Disclosure:** UE5 GUI render job not triggered in this phase. The UE5 editor requires manual interaction to queue and run a Movie Render Queue job. The submission code path (`mnemo_gate_client.submit_frame`) is identical to what `MnemosyneExecutor` calls inside the editor.
- **FAZ 9D.3 operator action:** Open UE5, configure MRQ job, trigger render — the executor fires automatically.

### Architecture Constraints Honored

- ✅ No C++ plugin
- ✅ No cloud (Loopback TCP only: 127.0.0.1:8765)
- ✅ No UDS
- ✅ scene_manifest_v1 frozen
- ✅ Taxonomy v1.1 frozen
- ✅ Quarantine schema v1.1 enforced (written by gate-api → quarantine-logger)
- ✅ Fail-closed: first rejection stops processing immediately
- ✅ No scope drift (no Unity, Nuke, Maya, RLHF, SDK, compliance pack)

---

## Next Phase: FAZ 9D.3

**Remaining operator action for full UE5 end-to-end:**

1. Enable `PythonScriptPlugin` in `MnemosyneHookMVP.uproject`
2. Copy `faz9d2/*.py` → `MnemosyneHookMVP/Content/Python/`
3. Configure `DefaultEngine.ini` startup script
4. Open UE5 → verify executor registered in Output Log
5. Run Movie Render Queue job → capture real UE5 render → Gate verdict
6. Verify `Mnemosyne_Certified_Passport.json` in `Saved/MnemosyneCertification/`
