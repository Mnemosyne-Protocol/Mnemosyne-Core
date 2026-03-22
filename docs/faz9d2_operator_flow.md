# FAZ 9D.2 — Operator Flow
**Mnemosyne v3.0.0 · Minimum UE5 → Gate MVP Workflow**

---

## Prerequisites

Before opening UE5:

```bash
# 1. Verify Gate stack is running
cd /Volumes/MNEMOSYNE-GATE/Vault/repos/Mnemosyne-Core/faz9a
docker compose ps          # all 4 containers should be "Up (healthy)"

# 2. Health check
curl http://127.0.0.1:8765/health
# Expected: {"status":"healthy","service":"gate-api","version":"3.0.0"}
```

If gate-api is not running: `docker compose up -d` and wait 10s for all services to be healthy.

---

## Step 1 — Enable Python Plugin in Project

Edit `MnemosyneHookMVP.uproject`:

```json
{
  "FileVersion": 3,
  "EngineAssociation": "5.7",
  "Plugins": [
    {
      "Name": "ModelingToolsEditorMode",
      "Enabled": true,
      "TargetAllowList": ["Editor"]
    },
    {
      "Name": "PythonScriptPlugin",
      "Enabled": true
    }
  ]
}
```

---

## Step 2 — Install Mnemosyne Python Files

Copy the FAZ 9D.2 Python hook to the project's Content/Python directory:

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

## Step 3 — Configure DefaultEngine.ini

Add the Python startup script path to the engine config:

File: `MnemosyneHookMVP/Config/DefaultEngine.ini`

```ini
[/Script/PythonScriptPlugin.PythonScriptPluginSettings]
AdditionalPaths=(Path="Content/Python")
StartupScripts=(Path="Content/Python/init_unreal.py")
```

---

## Step 4 — Open UE5

```bash
UE5=/Volumes/MNEMOSYNE-GATE/Vault/UnrealEngine/UE_5.7/Engine/Binaries/Mac/UnrealEditor
PROJECT=/Volumes/MNEMOSYNE-GATE/Vault/repos/MnemosyneHookMVP/MnemosyneHookMVP/MnemosyneHookMVP.uproject

open -a "${UE5}.app" "${PROJECT}"
```

On editor start, `init_unreal.py` auto-executes and registers `MnemosyneExecutor` as the active MRQ executor. Check the Output Log for:

```
LogPython: MNEMOSYNE: Executor registered — gate=3.0.0 | transport=127.0.0.1:8765 (SÖZLEŞME 2: loopback TCP)
LogPython: MNEMOSYNE: All MRQ jobs will route through Mnemosyne fail-closed gate.
```

---

## Step 5 — Create and Run a Movie Render Queue Job

1. `Window → Cinematics → Movie Render Queue`
2. Click `+` → add a Level Sequence (or use any existing sequence)
3. Configure output: **PNG**, `Saved/MovieRenders/`
4. Click **Render (Local)**

The `MnemosyneExecutor` fires automatically:

```
LogPython: MNEMOSYNE: Session faz9d2-xxxxxxxx started — gate=http://127.0.0.1:8765
LogPython: MNEMOSYNE: Submitting frame 0 → http://127.0.0.1:8765/submit
LogPython: MNEMOSYNE: frame[0] APPROVED ψ=1 | 12.3ms | ledger=<uuid>
...
```

---

## Step 6 — Outcomes

### PASS Path (all frames approved)

```
LogPython: MNEMOSYNE: All N frames approved — producing passport.
LogPython: MNEMOSYNE: CERTIFIED — Passport: .../Mnemosyne_Certified_Passport.json
LogPython: MNEMOSYNE: Manifest:  .../scene_manifest_v1.json
```

Artifacts written to `Saved/MnemosyneCertification/<session_id>/`:
- `Mnemosyne_Certified_Passport.json` — Ed25519 signed
- `scene_manifest_v1.json` — export session manifest

### FAIL Path (any frame rejected)

```
LogPython Error: MNEMOSYNE FAIL-CLOSED: frame[N] ... REJECTED — <violation>
```

- No passport is written
- Quarantine record written by gate-api → quarantine-logger service
- Render job marked **FAILED** in MRQ
- Operator must investigate via: `docker compose logs quarantine-logger`

---

## Step 7 — Verify Results

```bash
# Check ledger (approved frames)
docker compose logs ledger-service | grep "RECORD"

# Check quarantine (rejected frames)
docker compose logs quarantine-logger | grep "QUARANTINE"

# Verify passport
cat /path/to/Saved/MnemosyneCertification/<session_id>/Mnemosyne_Certified_Passport.json | python3 -m json.tool
```

---

## Headless Test (without UE5 GUI)

To verify the Gate submission path without opening UE5:

```bash
cd /Volumes/MNEMOSYNE-GATE/Vault/repos/Mnemosyne-Core/faz9d2
python run_faz9d2.py
```

Expected: 8/8 EC PASS, passport written to `bench/out/faz9d2_pass_session/`.

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
