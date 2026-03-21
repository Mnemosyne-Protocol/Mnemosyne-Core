# FAZ 9D.1 — TASK 4: Blank UE5 Project Creation

**Node:** MNEMOSYNE-NODE-01
**Date:** 2026-03-21
**Status:** PENDING_OPERATOR_CONFIRMATION

---

## Project Specification

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Project name | MnemosyneHookMVP | Identifies hook integration purpose |
| Template | Blank | Minimal footprint; no game logic overhead |
| Type | Game | Standard UE5 project type |
| Language | Blueprint | Avoids Xcode full IDE requirement; Python scripting works without C++ |
| Target path | `/Volumes/MNEMOSYNE-GATE/Vault/repos/MnemosyneHookMVP` | Encrypted volume |

See `bench/out/faz9d1_blank_project_status.json` for full specification.

---

## Plugins to Enable

| Plugin | Purpose |
|--------|---------|
| PythonScriptPlugin | Core MVP — Python post-export callbacks |
| EditorScriptingUtilities | Asset manipulation, batch operations from Python |
| MovieRenderPipeline | MRQ integration — production export hook target |

## Plugins to Disable (optional)

| Plugin | Reason |
|--------|--------|
| VirtualReality | Unused; reduces menu noise |
| MixedReality | Unused |
| AndroidSupport | Unused; saves compile time |
| IOSSupport | Unused |

---

## Creation Steps (for operator)

1. Launch UE5 from Epic Games Launcher
2. Click **Games** → **Blank**
3. Set Blueprint (not C++)
4. Set path: `/Volumes/MNEMOSYNE-GATE/Vault/repos/MnemosyneHookMVP`
5. Set project name: `MnemosyneHookMVP`
6. Click **Create**
7. After project opens: Edit → Plugins → enable the 3 plugins above → Restart
8. Verify Python works: Window → Output Log → look for `LogPython: Python Interpreter initialized`

---

## Current State

Project: **NOT CREATED** — awaiting UE5 installation.

---

## Awaiting Operator Input

**This task is paused.** Resume with:

```
Installation complete. Paths: [launcher path] [ue5 path] [project path]
```

---

*This document will be updated with verified project state after operator confirmation.*
