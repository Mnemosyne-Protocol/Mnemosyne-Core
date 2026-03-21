"""
mock_export_generator.py — Mnemosyne FAZ 9C
============================================
Generates simulated UE5 post-export frame files.

Platform Note (CLAUDE.md): UE5 is not installed on NODE-01.
This module produces a mock UE5 export folder that the ue5_export_hook
processes identically to real UE5 output.

Each "frame" is a JSON file containing:
  - UE5-style export metadata (renderer, scene_id, render_pass)
  - A pre-built attestation payload ready for gate-api submission

Two session types:
  PASSING_SESSION  — all frames valid (ψ=1 for every frame → certification issued)
  FAILING_SESSION  — contains one invalid frame (ψ=0 → fail-closed, no certification)
"""

from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Literal

KS_SEED = b"MNEMOSYNE-KS-V3"


def _ks_sha256(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(KS_SEED)
    h.update(data)
    return h.hexdigest()


def _make_frame_file(
    frame_index: int,
    session_id: str,
    violation: Literal["none", "SIGNATURE_INVALID", "SOURCE_INVARIANT_BREACH",
                        "POLICY_MODE_VIOLATION", "GEOMETRY_BREACH"] = "none",
) -> dict:
    """
    Build a single mock UE5 export frame JSON payload.

    violation="none"  → valid frame, gate will APPROVE
    violation=<type>  → introduces the corresponding fault
    """
    frame_id = f"{session_id}-frame-{frame_index:04d}"
    valid_sig = "a" * 128   # valid Ed25519 format: 128 hex chars

    # Base attestation (always valid)
    attestation: dict = {
        "schema_version": "2.0",
        "hash_mode": "KS-salted",
        "signature": {"signature_hex": valid_sig, "algorithm": "Ed25519"},
        "signer": "tier_a",
        "source_invariants": {
            "mesh_topology_hash": {"status": "PASS"},
            "uv_layout_hash": {"status": "PASS"},
            "shader_signature_hash": {"status": "PASS"},
        },
        "render_fingerprint": {
            "silhouette_front": {"silhouette_hash": {"status": "PASS"}},
            "edge_front": {"edge_hash": {"status": "PASS"}},
            "roi_hashes": {
                "head": {"status": "PASS"},
                "chest": {"status": "PASS"},
                "emblem_zone": {"status": "PASS"},
            },
        },
        "submission_mode": "controlled_generative",
        "metrics": {"emissive_budget": {"value": 680_000}},  # Fixed6: 0.68 < 0.72 limit
    }

    # Inject the requested violation
    if violation == "SIGNATURE_INVALID":
        # Bad signature length (not 128 hex chars)
        attestation["signature"]["signature_hex"] = "dead" * 8   # 32 chars, invalid

    elif violation == "SOURCE_INVARIANT_BREACH":
        # Mesh topology hash failed
        attestation["source_invariants"]["mesh_topology_hash"] = {"status": "FAIL"}

    elif violation == "POLICY_MODE_VIOLATION":
        # Wrong hash mode (non-KS) → POLICY_MODE_VIOLATION
        attestation["hash_mode"] = "raw"

    elif violation == "GEOMETRY_BREACH":
        # ROI head hash failed
        attestation["render_fingerprint"]["roi_hashes"]["head"] = {"status": "FAIL"}

    return {
        "frame_id": frame_id,
        "session_id": session_id,
        "export_metadata": {
            "renderer": "UE5-Lumen-RayTracing",
            "render_pass": "beauty",
            "scene_id": "mnemo_cosmetic_scene_v1",
            "ue5_version": "5.4.0",
            "export_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "frame_index": frame_index,
            "resolution": "3840x2160",
        },
        "attestation": attestation,
        "expected_verdict": "APPROVED" if violation == "none" else "REJECTED",
        "expected_violation": violation if violation != "none" else None,
    }


def generate_session(
    output_dir: Path,
    session_id: str,
    n_frames: int = 5,
    failing_frame_index: int | None = None,
    failing_violation: str = "SIGNATURE_INVALID",
) -> Path:
    """
    Write mock UE5 export frame JSON files to output_dir/session_id/.
    Returns the session directory path.

    Parameters
    ----------
    failing_frame_index : int or None
        If set, frame at this index has the specified violation injected.
    """
    session_dir = output_dir / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    for i in range(n_frames):
        violation = "none"
        if failing_frame_index is not None and i == failing_frame_index:
            violation = failing_violation

        frame = _make_frame_file(
            frame_index=i,
            session_id=session_id,
            violation=violation,
        )

        frame_path = session_dir / f"frame_{i:04d}.json"
        frame_path.write_text(
            json.dumps(frame, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # Write session manifest
    manifest = {
        "session_id": session_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_frames": n_frames,
        "failing_frame_index": failing_frame_index,
        "failing_violation": failing_violation if failing_frame_index is not None else None,
        "source": "mock_export_generator — simulated UE5 post-export output",
        "platform_note": "UE5 not installed on NODE-01 (FAZ 9D target). Mock used per CLAUDE.md.",
    }
    (session_dir / "session_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    return session_dir
