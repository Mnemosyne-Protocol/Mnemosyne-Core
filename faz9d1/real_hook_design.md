# FAZ 9D.1 — TASK 6: Real Hook Architecture Design
**ec:** ec6_real_hook_design_written
**Date:** 2026-03-21

## Architecture Overview

```
UE5 Editor (MnemosyneHookMVP)
│
├── Movie Render Queue → renders frame N → writes PNG to Saved/MovieRenders/
│
└── MnemosyneExecutor (Python, MoviePipelinePythonHostExecutor)
    ├── on_begin_frame()          — build scene_manifest_v1 header
    ├── on_individual_shot_work_finished()
    │    └── for each rendered frame:
    │         1. Read PNG → extract hash (KS-SHA256)
    │         2. Build submit_payload (scene_manifest_v1 + frame_data)
    │         3. POST http://127.0.0.1:8765/submit
    │         4. Parse verdict:
    │              ψ=1 → log APPROVED, continue
    │              ψ=0 → write quarantine JSON (schema v1.1) → RAISE → pipeline abort
    │
    └── on_executor_finished()
         └── if all_frames_approved:
               generate Mnemosyne_Certified_Passport.json (Ed25519 signed)
             else:
               fail-closed, no passport
```

## Key Components

### 1. MnemosyneExecutor (`mnemo_ue5_executor.py`)
```python
# Placed at: MnemosyneHookMVP/Content/Python/mnemo_ue5_executor.py
import unreal
import urllib.request
import json
import hashlib

GATE_URL = "http://127.0.0.1:8765/submit"
KS_SEED = "MNEMOSYNE-KS-V3"

@unreal.uclass()
class MnemosyneExecutor(unreal.MoviePipelinePythonHostExecutor):

    approved_frames = unreal.uproperty(int)
    rejected_frames = unreal.uproperty(int)

    @unreal.ufunction(override=True)
    def execute_delayed(self, pipeline_queue):
        ...

    @unreal.ufunction(override=True)
    def on_individual_shot_work_finished_impl(self, shot_info):
        frame_path = shot_info.output_state.source_frame_number
        verdict = self._submit_frame(frame_path)
        if verdict["psi"] == 0:
            self._write_quarantine(verdict)
            raise RuntimeError(f"MNEMOSYNE FAIL-CLOSED: frame {frame_path} rejected — {verdict['violation_type']}")
        self.approved_frames += 1

    def _ks_hash(self, data: bytes) -> str:
        seed = KS_SEED.encode("ascii")
        return hashlib.sha256(seed + data).hexdigest()

    def _submit_frame(self, frame_path: str) -> dict:
        with open(frame_path, "rb") as f:
            raw = f.read()
        ks_hash = self._ks_hash(raw)
        payload = json.dumps({
            "asset_id": frame_path,
            "hash_ks": ks_hash,
            "source_pipeline": "UE5_MRQ",
            "source_model": "UE5_RENDERER",
            "gate_version": "1.0",
            "policy_pack_version": "1.0"
        }).encode()
        req = urllib.request.Request(GATE_URL, data=payload,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())

    def _write_quarantine(self, verdict: dict):
        import datetime, os
        record = {
            "asset_id": verdict["asset_id"],
            "timestamp_utc": datetime.datetime.utcnow().isoformat() + "Z",
            "source_model": "UE5_RENDERER",
            "source_pipeline": "UE5_MRQ",
            "violation_type": verdict["violation_type"],         # taxonomy v1.1
            "decision_reason": verdict.get("decision_reason", ""),
            "psi": 0,
            "hash_canonical": verdict.get("hash_canonical", ""),
            "hash_ks": verdict.get("hash_ks", ""),
            "policy_pack_version": "1.0",
            "gate_version": "1.0",
            "benchmark_run_id": "",
            "replay_pointer": "",
            "operator": "UE5_HOOK",
            "admission_decision": "QUARANTINE"
        }
        os.makedirs("quarantine", exist_ok=True)
        path = f"quarantine/{record['asset_id'].replace('/', '_')}.json"
        with open(path, "w") as f:
            json.dump(record, f, indent=2)
```

### 2. Startup Registration (`init_unreal.py`)
```python
# Placed at: MnemosyneHookMVP/Content/Python/init_unreal.py
# Auto-executed by UE5 PythonScriptPlugin on editor start
import unreal
from mnemo_ue5_executor import MnemosyneExecutor

# Register executor with Movie Render Queue subsystem
subsystem = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
subsystem.get_queue().set_executor_class(MnemosyneExecutor)
unreal.log("MNEMOSYNE: Hook executor registered.")
```

### 3. Passport Generator (`mnemo_passport.py`)
```python
# Called by MnemosyneExecutor.on_executor_finished() when all frames pass
import json, datetime
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

def generate_passport(frames: list[dict], key: Ed25519PrivateKey) -> dict:
    payload = {
        "schema": "mnemosyne_passport_v1",
        "timestamp_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "total_frames": len(frames),
        "all_approved": True,
        "frames": frames,
        "gate_version": "1.0",
        "policy_pack_version": "1.0"
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    sig = key.sign(canonical).hex()
    payload["signature_ed25519"] = sig
    return payload
```

## Deployment Steps (FAZ 9D.2)

1. Edit `MnemosyneHookMVP.uproject` — enable `PythonScriptPlugin`
2. Place `mnemo_ue5_executor.py`, `init_unreal.py`, `mnemo_passport.py` under `Content/Python/`
3. Add `Content/Python` to `DefaultEngine.ini` → `[/Script/PythonScriptPlugin.PythonScriptPluginSettings]` → `AdditionalPaths`
4. Verify Gate API is running: `curl http://127.0.0.1:8765/health`
5. Launch UE5 → `init_unreal.py` auto-registers the executor
6. Run Movie Render Queue job → hook fires per-frame

## Fail-Closed Guarantee

```
Any exception in MnemosyneExecutor → UE5 catches as pipeline error
→ render job marked FAILED
→ No passport generated
→ Quarantine record written (schema v1.1)
→ Pipeline does NOT continue to next frame
```

## Communication Protocol (Locked — FAZ 9A)

```
Transport:  HTTP/1.1
Endpoint:   http://127.0.0.1:8765/submit
Method:     POST
Body:       JSON (scene_manifest_v1 frame payload)
Response:   {"psi": 0|1, "violation_type": "...", "decision_reason": "..."}
```
