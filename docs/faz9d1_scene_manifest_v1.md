# FAZ 9D.1 — TASK 6: Scene Manifest v1 Schema

**Node:** MNEMOSYNE-NODE-01
**Date:** 2026-03-21
**Protocol:** Mnemosyne v3.0.0 · DOI: 10.5281/zenodo.18884426

---

## Purpose

`canonical_scene_manifest.json` closes the generative trust chain by binding the **scene identity** (geometry, materials, lighting) to the verification record. Without a scene manifest, the gate can verify that *a* render passed invariants but cannot prove it came from *this specific scene configuration*.

This document defines the v1 schema.

---

## Schema v1

```json
{
  "schema": "mnemosyne.scene_manifest.v1",
  "version": "1.0.0",
  "generated_at": "ISO8601",
  "generator": "string — tool that produced this manifest",
  "scene_id": "string — human-readable scene identifier",
  "scene_uuid": "UUID4 — immutable scene identity",

  "geometry": {
    "mesh_topology_hash": "KS-SHA256 hex — hash of mesh vertex/face structure",
    "mesh_source": "string — asset path or external reference",
    "poly_count": "integer",
    "lod_levels": "integer"
  },

  "materials": {
    "uv_layout_hash": "KS-SHA256 hex — hash of UV channel layout",
    "shader_signature_hash": "KS-SHA256 hex — hash of material graph",
    "material_slot_count": "integer",
    "material_names": ["array of strings"]
  },

  "lighting": {
    "light_rig_hash": "KS-SHA256 hex — hash of light actor positions + intensities",
    "emissive_budget_fixed6": "integer — Fixed6 max emissive budget (default: 720000 = 0.72)",
    "hdri_hash": "KS-SHA256 hex or null"
  },

  "render_settings": {
    "renderer": "string — e.g. UE5-Lumen-RayTracing",
    "resolution": "string — e.g. 3840x2160",
    "render_pass": "string — e.g. beauty",
    "ue5_version": "string"
  },

  "invariants": {
    "source_invariants_frozen": "boolean — true if mesh/uv/shader hashes are frozen",
    "freeze_timestamp": "ISO8601 or null",
    "freeze_operator": "string — email of operator who froze invariants"
  },

  "signature": {
    "manifest_hash_ks": "KS-SHA256 hex of canonical manifest JSON",
    "signature_hex": "Ed25519 signature hex (128 chars)",
    "algorithm": "Ed25519",
    "public_key_hex": "hex of signing public key",
    "signed_over": "canonical_json_sorted_keys"
  }
}
```

---

## Example — `MnemosyneHookMVP` Scene v1

```json
{
  "schema": "mnemosyne.scene_manifest.v1",
  "version": "1.0.0",
  "generated_at": "2026-03-21T00:00:00+00:00",
  "generator": "faz9d1_scene_manifest_generator.py",
  "scene_id": "mnemo_cosmetic_scene_v1",
  "scene_uuid": "a3f1e7d2-0001-0001-0001-000000000001",

  "geometry": {
    "mesh_topology_hash": "PENDING — generated after blank project created",
    "mesh_source": "Content/Characters/Cosmetics/BaseMesh.uasset",
    "poly_count": 0,
    "lod_levels": 4
  },

  "materials": {
    "uv_layout_hash": "PENDING",
    "shader_signature_hash": "PENDING",
    "material_slot_count": 0,
    "material_names": []
  },

  "lighting": {
    "light_rig_hash": "PENDING",
    "emissive_budget_fixed6": 720000,
    "hdri_hash": null
  },

  "render_settings": {
    "renderer": "UE5-Lumen-RayTracing",
    "resolution": "3840x2160",
    "render_pass": "beauty",
    "ue5_version": "5.5.0"
  },

  "invariants": {
    "source_invariants_frozen": false,
    "freeze_timestamp": null,
    "freeze_operator": "ks@mnemosynelabs.ai"
  },

  "signature": {
    "manifest_hash_ks": "PENDING",
    "signature_hex": "PENDING",
    "algorithm": "Ed25519",
    "public_key_hex": "PENDING",
    "signed_over": "canonical_json_sorted_keys"
  }
}
```

---

## Hash Computation Rules

All hashes in the manifest use KS-SHA256:

```python
KS_SEED = b"MNEMOSYNE-KS-V3"

def ks_sha256(data: bytes) -> str:
    import hashlib
    h = hashlib.sha256()
    h.update(KS_SEED)
    h.update(data)
    return h.hexdigest()

# Mesh topology hash: hash of ASCII-sorted vertex list export
mesh_topology_hash = ks_sha256(mesh_export_bytes)

# UV layout hash: hash of UV channel 0 binary data
uv_layout_hash = ks_sha256(uv_channel_bytes)

# Shader signature hash: hash of RFC8785-canonical material JSON
shader_signature_hash = ks_sha256(material_canonical_json.encode())

# Light rig hash: hash of sorted light actors JSON
light_rig_hash = ks_sha256(light_actors_canonical_json.encode())

# Manifest hash: hash of canonical manifest JSON (before signature field added)
manifest_hash_ks = ks_sha256(
    json.dumps(manifest_without_signature, sort_keys=True, separators=(",", ":")).encode()
)
```

---

## Manifest Generation Workflow

```
1. Artist finalizes scene (mesh, materials, lighting)
2. Operator runs: python3 faz9d/generate_scene_manifest.py --project MnemosyneHookMVP
   → Extracts mesh/UV/shader hashes from UE5 Python API
   → Writes canonical_scene_manifest.json to Content/Python/mnemosyne_hook/
3. Operator reviews + signs: mnemosynectl sign-manifest canonical_scene_manifest.json
4. Manifest is committed to version control
5. Gate hook loads manifest at runtime; invariant hashes are frozen from this point
6. Any scene change → manifest regenerated → new freeze event logged
```

---

## Trust Chain

```
canonical_scene_manifest.json  (frozen geometry + material hashes)
          │
          ▼
frame_attestation.py           (computes source_invariants from manifest at render time)
          │
          ▼
gate-api /submit               (verifies invariants match; fail-closed on mismatch)
          │
          ▼
Ledger + Quarantine            (immutable record of every decision)
          │
          ▼
Mnemosyne_Certified_Passport.json  (Ed25519 signed; proves this render came from this scene)
```

---

## v1 Limitations (addressed in v2)

| Limitation | v2 Plan |
|------------|---------|
| No per-frame geometry snapshot | Add frame-level mesh hash (for animated scenes) |
| No skeleton/rig hash | Add skeleton topology hash for character animations |
| Emissive budget is scene-level | Add per-frame emissive measurement from EXR |
| Manual manifest generation | UE5 Python auto-generator on scene save event |
