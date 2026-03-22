# FAZ 9D.3 — Live UE5 Operator Execution Guide
**Mnemosyne v3.0.0 · Bypass UI Dropdown · Python Console Path**

---

## Context

UE5 C++ UI reflection blocks the custom executor from appearing in the
Movie Render Queue dropdown. We bypass the dropdown entirely and drive
execution from the UE5 Python Console. The pipeline is the product, not the UI.

---

## Prerequisites (before opening UE5)

```bash
# 1. Gate stack must be running
cd /Volumes/MNEMOSYNE-GATE/Vault/repos/Mnemosyne-Core/faz9a
docker compose ps    # all 4 containers must show "Up (healthy)"

# 2. If not running:
docker compose up -d
sleep 10
curl http://127.0.0.1:8765/health
# Expected: {"status":"healthy","service":"gate-api","version":"3.0.0"}
```

---

## Step 1 — Verify PythonScriptPlugin is enabled (ec1)

Open `MnemosyneHookMVP.uproject` and confirm this entry exists under `"Plugins"`:

```json
{
  "Name": "PythonScriptPlugin",
  "Enabled": true
}
```

If missing, add it now. Save the file before opening UE5.

---

## Step 2 — Copy hook files to project

```bash
PROJECT=/Volumes/MNEMOSYNE-GATE/Vault/repos/MnemosyneHookMVP/MnemosyneHookMVP
HOOKS=/Volumes/MNEMOSYNE-GATE/Vault/repos/Mnemosyne-Core/faz9d2

mkdir -p "${PROJECT}/Content/Python"
cp "${HOOKS}/mnemo_gate_client.py"  "${PROJECT}/Content/Python/"
cp "${HOOKS}/mnemo_manifest.py"     "${PROJECT}/Content/Python/"
cp "${HOOKS}/mnemo_ue5_executor.py" "${PROJECT}/Content/Python/"
cp "${HOOKS}/init_unreal.py"        "${PROJECT}/Content/Python/"
```

---

## Step 3 — Open UE5

```bash
UE5=/Volumes/MNEMOSYNE-GATE/Vault/UnrealEngine/UE_5.7/Engine/Binaries/Mac/UnrealEditor
PROJECT=/Volumes/MNEMOSYNE-GATE/Vault/repos/MnemosyneHookMVP/MnemosyneHookMVP/MnemosyneHookMVP.uproject
open -a "${UE5}.app" "${PROJECT}"
```

---

## Step 4 — Confirm executor registration in Output Log (ec2)

After editor loads, check the Output Log for:

```
LogPython: MNEMOSYNE: Gate API healthy — version=3.0.0 policy=gate-api
LogPython: MNEMOSYNE: MnemosyneGateExecutor registered with Movie Render Queue subsystem.
LogPython: MNEMOSYNE:   Transport: http://127.0.0.1:8765 (SÖZLEŞME 2: loopback TCP only)
```

If you see `gate-api unreachable` instead — start the Docker stack and restart UE5.

---

## Step 5 — Open the Python Console

`Window → Developer Tools → Output Log`
Switch the bottom input bar tab to **Python**.

---

## Step 6 — Run the PASS test (ec3, ec4)

Copy and paste the following into the Python Console, then press **Enter**:

```python
exec(open("/Volumes/MNEMOSYNE-GATE/Vault/repos/Mnemosyne-Core/faz9d3/trigger_mnemosyne_render.py").read())
```

Expected Output Log output:

```
MNEMOSYNE: ========================================================
MNEMOSYNE: FAZ 9D.3 — Live Operator Execution
MNEMOSYNE: ========================================================
MNEMOSYNE: Session [pass] started — id=faz9d3-pass-XXXXXXXX frames=3
MNEMOSYNE:   [000] APPROVED ψ=1 ...ms
MNEMOSYNE:   [001] APPROVED ψ=1 ...ms
MNEMOSYNE:   [002] APPROVED ψ=1 ...ms
MNEMOSYNE:   ALL 3 frames APPROVED ψ=1
MNEMOSYNE:   CERTIFIED — Passport: .../faz9d3_pass_session/Mnemosyne_Certified_Passport.json
```

---

## Step 7 — Verify FAIL test (ec5)

The same trigger script automatically runs the FAIL session after PASS.
Expected Output Log:

```
MNEMOSYNE: Session [fail] started — id=faz9d3-fail-XXXXXXXX frames=3
MNEMOSYNE:   [000] APPROVED ψ=1 ...ms
MNEMOSYNE:   [001] REJECTED ψ=0 ...ms
MNEMOSYNE ERROR: FAIL-CLOSED: frame[1] ... REJECTED — non-KS hash mode: 'raw'
MNEMOSYNE ERROR: No certification issued.
MNEMOSYNE:   Session BLOCKED — no passport written.
```

The FAIL run intentionally submits an invalid attestation at frame[1]:
- `hash_mode = "raw"` (not KS-salted) → `POLICY_MODE_VIOLATION`
- Bad signature format → `SIGNATURE_INVALID`
- Source invariants FAIL → `SOURCE_INVARIANT_BREACH`

No passport is written. Quarantine record is created by gate-api.

---

## Step 8 — Collect artifacts (ec6)

After both sessions complete, find artifacts at:

```
bench/out/
  faz9d3_pass_run.json          ← PASS session full record
  faz9d3_fail_run.json          ← FAIL session full record
  faz9d3_report.json            ← Consolidated phase report
  faz9d3_pass_session/
    scene_manifest_v1.json      ← Export manifest
    Mnemosyne_Certified_Passport.json  ← Ed25519 signed passport
    frame_0000.png / frame_0001.png / frame_0002.png
  faz9d3_fail_session/
    scene_manifest_v1.json
    (no passport — fail-closed)
```

Verify passport:
```bash
python3 -c "
import json
p = json.load(open('bench/out/faz9d3_pass_session/Mnemosyne_Certified_Passport.json'))
print('schema:', p['schema'])
print('certified:', p['all_frames_approved'])
print('frames:', p['frame_count'])
print('sig_alg:', p['signature']['algorithm'])
"
```

Verify quarantine (check gate-api logs):
```bash
cd faz9a && docker compose logs quarantine-logger | tail -20
```

---

## Step 9 — Final EC check

When run from inside UE5, the trigger prints:

```
MNEMOSYNE: PASS ec1_python_plugin_enabled
MNEMOSYNE: PASS ec2_executor_registered_in_log
MNEMOSYNE: PASS ec3_pass_job_runs_from_editor
MNEMOSYNE: PASS ec4_passport_written_from_real_editor_run
MNEMOSYNE: PASS ec5_fail_job_blocks_and_writes_no_passport
MNEMOSYNE: PASS ec6_artifacts_collected
MNEMOSYNE: PASS ec7_report_written
MNEMOSYNE: PASS ec8_scope_preserved
MNEMOSYNE: Result: ALL PASS
```

---

## Architecture Constraints (Non-negotiable)

| Constraint | Status |
|-----------|--------|
| Python only — no C++ plugin | ✅ Enforced |
| Loopback TCP 127.0.0.1:8765 only | ✅ Enforced |
| No cloud dependencies | ✅ Enforced |
| scene_manifest_v1 frozen | ✅ Enforced |
| Taxonomy v1.1 frozen | ✅ Enforced |
| Quarantine schema v1.1 frozen | ✅ Enforced |
| Fail-closed on first rejection | ✅ Enforced |
