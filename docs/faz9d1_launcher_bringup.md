# FAZ 9D.1 — TASK 2: Epic Games Launcher & UE5 5.5 Bring-Up Plan

**Node:** MNEMOSYNE-NODE-01
**Date:** 2026-03-21
**Status:** READY — Awaiting Operator Execution

---

## Pre-Flight Summary

| Check | Status | Notes |
|-------|--------|-------|
| Disk space | ✓ OK | 903 GB available; UE5 needs ~80 GB install + ~60 GB project cache |
| Python 3.12 | ✓ OK | arm64, pyenv |
| Xcode CLI Tools | ✓ OK | clang 17.0.0, SDK 26.2 |
| Xcode full IDE | NOT REQUIRED | Only needed for C++ plugin path (not MVP) |
| macOS Tahoe 26.3.1 | VERIFY | UE5 5.5 officially supports macOS 14+ (Sonoma). Tahoe (25.x) is post-Sonoma — verify release notes before install |
| Epic Games Launcher | NOT INSTALLED | Step 1 below |
| UE5 5.5 | NOT INSTALLED | Step 3 below |

---

## Step 1 — Download Epic Games Launcher

1. Open browser → go to **epicgames.com/store/download**
2. Click **Download Epic Games Launcher**
3. Save `EpicInstaller-*.dmg` to `/Users/ksadmin/Downloads/`

---

## Step 2 — Install Epic Games Launcher

```bash
# Mount the DMG
hdiutil attach ~/Downloads/EpicInstaller-*.dmg

# Drag Epic Games Launcher.app to /Applications
cp -R "/Volumes/Epic Games Launcher/Epic Games Launcher.app" /Applications/

# Eject
hdiutil detach "/Volumes/Epic Games Launcher"

# Launch and sign in
open "/Applications/Epic Games Launcher.app"
```

**Verify installation:**
```bash
ls -la "/Applications/Epic Games Launcher.app"
# Expected: drwxr-xr-x ... Epic Games Launcher.app
```

---

## Step 3 — Install Unreal Engine 5.5

Inside Epic Games Launcher:
1. Sign in with Epic account (create one if needed — free)
2. Left sidebar → **Unreal Engine** → **Library**
3. Click **+** (Engine Versions) → select **5.5.x** (latest stable)
4. Click **Install**
5. Choose install path:
   - Default: `/Users/Shared/Epic Games/UE_5.5/`
   - Alternate: `/Volumes/MNEMOSYNE-GATE/Vault/UE_5.5/` ← recommended (encrypted volume)
6. Wait for download + install (~80 GB, time varies by network)

**Verify install:**
```bash
# Check default path
ls "/Users/Shared/Epic Games/UE_5.5/Engine/Binaries/Mac/UnrealEditor.app" 2>/dev/null && echo "FOUND"

# Check alternate path (if used)
ls "/Volumes/MNEMOSYNE-GATE/Vault/UE_5.5/Engine/Binaries/Mac/UnrealEditor.app" 2>/dev/null && echo "FOUND"

# Check binary
find "/Users/Shared/Epic Games" -name "UnrealEditor" -type f 2>/dev/null | head -3
```

---

## Step 4 — macOS Tahoe Compatibility Check

UE5 5.5 release notes list macOS 14.x (Sonoma) as minimum. Tahoe (26.x) is a later release.

If a compatibility warning appears at first launch:
- Try launching anyway — UE5 often runs on newer macOS despite outdated release notes
- Check Epic's UDN / release notes for 5.5.x patch notes mentioning Tahoe support

If UE5 fails to launch on Tahoe:
- Consider building from source from GitHub (requires Epic account with UE5 source access)
- Alternative: install UE5 5.4.4 (older, confirmed macOS 14 support)

---

## Step 5 — First Launch & Plugins

On first UE5 launch, the engine will compile shaders (~5–15 minutes).

After first launch, verify Python plugin:
1. Edit menu → Plugins → search "Python"
2. Enable **Python Editor Script Plugin** ← CRITICAL for MVP hook
3. Enable **Editor Scripting Utilities**
4. Enable **Movie Render Pipeline**
5. Disable: VirtualReality, MixedReality, AndroidSupport, IOSSupport (optional — reduces menu noise)
6. Restart UE5 when prompted

**Verify Python in UE5 Output Log:**
- Window → Output Log
- Expected on startup: `LogPython: Python Interpreter initialized (3.11.x)`

---

## Step 6 — Operator Confirmation

After completing Steps 1–5, report paths to Claude Code in this exact form:

```
Installation complete. Paths: [launcher path] [ue5 path] [project path]
```

Example:
```
Installation complete. Paths: /Applications/Epic Games Launcher.app /Users/Shared/Epic Games/UE_5.5 /Volumes/MNEMOSYNE-GATE/Vault/repos/MnemosyneHookMVP
```

The `[project path]` should be the directory where `MnemosyneHookMVP.uproject` will live.
Recommended: `/Volumes/MNEMOSYNE-GATE/Vault/repos/MnemosyneHookMVP`

---

## Notes

- **No C++ compiler required** for Blueprint + Python MVP path. Xcode full IDE is NOT needed.
- **Disk pressure:** UE5 DerivedDataCache can grow to 20–60 GB. Default DDC location is `~/Library/UnrealEngine/`. Consider setting `[InstalledDerivedDataBackend] Root` to the MNEMOSYNE-GATE volume if disk space is a concern.
- **Time estimate:** Download + install: 1–3 hours depending on network. Shader compile: 5–15 min.
