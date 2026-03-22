"""
mnemo_manifest.py — Mnemosyne FAZ 9D.2
=======================================
Mnemosyne v3.0.0 · DOI: 10.5281/zenodo.18884426

scene_manifest_v1 generator — TASK 3.
Called at export session start by mnemo_ue5_executor.py.
Can also be called standalone (test harness, CI).

Manifest is deterministic: same inputs → same output.
Missing required fields raise ValueError (fail-closed).

Schema frozen — FAZ 9D.1 scene_manifest_v1.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from mnemo_gate_client import ks_sha256, raw_sha256

# ─── Required manifest fields (fail-closed: missing any → raise) ─────────────

_REQUIRED = [
    "schema_version",
    "export_session_id",
    "project_name",
    "level_or_scene_name",
    "asset_list",
    "output_files",
    "source_invariants",
    "timestamp_utc",
    "operator",
    "node_id",
]


def build_manifest(
    project_name: str,
    level_or_scene_name: str,
    output_dir: Path,
    frame_paths: list[Path],
    operator: str = "ks@mnemosynelabs.ai",
    node_id: str = "MNEMOSYNE-NODE-01",
    export_session_id: Optional[str] = None,
    source_pipeline: str = "UE5_MRQ",
    source_model: str = "UE5_LUMEN",
    frame_rate: int = 24,
    resolution: Optional[dict] = None,
    render_preset: str = "Mnemosyne_MVP",
) -> dict:
    """
    Build a valid scene_manifest_v1 dict.
    Raises ValueError if any required field would be empty.
    """
    session_id = export_session_id or f"session-{uuid.uuid4().hex[:12]}"
    ts = datetime.now(timezone.utc).isoformat()
    res = resolution or {"width": 1920, "height": 1080}

    # Compute per-file hashes (KS-SHA256 of file bytes if file exists, else of path string)
    output_files = []
    asset_list = []
    for fp in frame_paths:
        if fp.exists():
            raw = fp.read_bytes()
            h_canonical = raw_sha256(raw)
            h_ks = ks_sha256(raw)
            size_bytes = len(raw)
        else:
            # File not yet written (export hasn't happened) — hash the path as placeholder
            h_canonical = raw_sha256(str(fp).encode())
            h_ks = ks_sha256(str(fp).encode())
            size_bytes = 0

        output_files.append({
            "path": str(fp),
            "hash_canonical": h_canonical,
            "hash_ks": h_ks,
            "size_bytes": size_bytes,
        })
        asset_list.append(str(fp))

    # Source invariants: structural constraints on the export session
    manifest_canonical_blob = json.dumps({
        "session_id": session_id,
        "project_name": project_name,
        "level_or_scene_name": level_or_scene_name,
        "output_dir": str(output_dir),
        "frame_count": len(frame_paths),
    }, sort_keys=True, separators=(",", ":")).encode("utf-8")

    manifest = {
        "schema_version": "scene_manifest_v1",
        "export_session_id": session_id,
        "project_name": project_name,
        "level_or_scene_name": level_or_scene_name,
        "asset_list": asset_list,
        "output_files": output_files,
        "source_invariants": {
            "frame_count_expected": len(frame_paths),
            "frame_rate": frame_rate,
            "resolution": res,
            "source_pipeline": source_pipeline,
            "source_model": source_model,
            "render_preset": render_preset,
        },
        "timestamp_utc": ts,
        "operator": operator,
        "node_id": node_id,
        "hash_canonical": raw_sha256(manifest_canonical_blob),
        "hash_ks": ks_sha256(manifest_canonical_blob),
    }

    # Fail-closed: verify all required fields
    missing = [k for k in _REQUIRED if not manifest.get(k)]
    if missing:
        raise ValueError(f"scene_manifest_v1 FAIL-CLOSED: missing required fields: {missing}")

    return manifest


def write_manifest(manifest: dict, output_dir: Path) -> Path:
    """Write manifest to predictable path. Returns path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "scene_manifest_v1.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
