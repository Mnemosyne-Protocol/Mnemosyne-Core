"""
attestation-service — Mnemosyne FAZ 9A Attestation Verifier & Signer
=====================================================================
Mnemosyne v3.0.0 · DOI: 10.5281/zenodo.18884426

Internal service — NOT exposed to host.
Accessible only via mnemosyne-net bridge.

Responsibilities:
  - POST /verify  : Validate attestation structure (schema, KS mode, signature format).
  - POST /sign    : Produce a KS-SHA256 bound, Ed25519-signed attestation payload.
  - GET  /merkle  : Compute Merkle root over (policy_hash + render_hash + context_hash).

KS Standard: H("MNEMOSYNE-KS-V3" || data).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from fastapi import FastAPI
from pydantic import BaseModel

# ─── Constants ────────────────────────────────────────────────────────────────

KS_SEED: bytes = b"MNEMOSYNE-KS-V3"

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [attestation] %(levelname)s %(message)s")
logger = logging.getLogger("mnemosyne.attestation")


# ─── KS Hashing ──────────────────────────────────────────────────────────────

def ks_sha256(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(KS_SEED)
    h.update(data)
    return h.hexdigest()


def raw_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ─── Ed25519 ─────────────────────────────────────────────────────────────────

def _get_or_generate_key() -> Ed25519PrivateKey:
    from pathlib import Path
    key_path = Path("/tmp/attestation_ed25519.pem")
    if key_path.exists():
        pem = key_path.read_bytes()
        return serialization.load_pem_private_key(pem, password=None)
    key = Ed25519PrivateKey.generate()
    pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    key_path.write_bytes(pem)
    return key


_KEY: Ed25519PrivateKey = _get_or_generate_key()
_PUB_HEX: str = _KEY.public_key().public_bytes(
    serialization.Encoding.Raw, serialization.PublicFormat.Raw
).hex()


# ─── Merkle ───────────────────────────────────────────────────────────────────

def _merkle_root(leaves: list[str]) -> str:
    """Binary Merkle root from hex-encoded leaf hashes using KS-SHA256."""
    if not leaves:
        return "0" * 64
    nodes = [bytes.fromhex(h) if len(h) == 64 else h.encode() for h in leaves]
    while len(nodes) > 1:
        if len(nodes) % 2 == 1:
            nodes.append(nodes[-1])  # duplicate last node if odd count
        nodes = [
            bytes.fromhex(ks_sha256(nodes[i] + nodes[i + 1]))
            for i in range(0, len(nodes), 2)
        ]
    return nodes[0].hex() if isinstance(nodes[0], bytes) else ks_sha256(nodes[0])


# ─── Models ───────────────────────────────────────────────────────────────────

class VerifyRequest(BaseModel):
    attestation: dict


class SignRequest(BaseModel):
    asset_id: str
    render_hash: str
    policy_hash: str
    context_hash: str
    submission_mode: str = "controlled_generative"
    signer_tier: str = "tier_b"


class MerkleRequest(BaseModel):
    policy_hash: str
    render_hash: str
    context_hash: str


# ─── FastAPI App ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="Mnemosyne Attestation Service",
    description="FAZ 9A internal — KS-SHA256 + Ed25519 attestation signing and verification",
    version="3.0.0",
)


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy", "service": "attestation-service", "public_key_hex": _PUB_HEX[:16] + "..."}


@app.post("/verify")
async def verify(req: VerifyRequest) -> dict:
    """
    Validate attestation structure.
    Checks: required fields, KS hash mode, Ed25519 signature format.
    """
    att = req.attestation
    issues = []

    # Required fields
    for field in ["schema_version", "hash_mode", "signature", "signer",
                  "source_invariants", "render_fingerprint"]:
        if field not in att:
            issues.append(f"missing field: {field}")

    # KS mode
    if att.get("hash_mode") != "KS-salted":
        issues.append(f"non-KS hash mode: {att.get('hash_mode')!r}")

    # Signature format
    sig = att.get("signature", {})
    sig_hex = sig.get("signature_hex", "") if isinstance(sig, dict) else ""
    if not sig_hex or len(sig_hex) != 128:
        issues.append(f"invalid Ed25519 signature length: {len(sig_hex)}")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "schema_version": att.get("schema_version"),
        "hash_mode": att.get("hash_mode"),
        "signer": att.get("signer"),
    }


@app.post("/sign")
async def sign_attestation(req: SignRequest) -> dict:
    """
    Produce a KS-SHA256 bound, Ed25519-signed attestation payload.
    Computes Merkle root over (policy_hash + render_hash + context_hash).
    """
    merkle = _merkle_root([req.policy_hash, req.render_hash, req.context_hash])

    payload = {
        "schema_version": "2.0",
        "hash_mode": "KS-salted",
        "asset_id": req.asset_id,
        "merkle_root": merkle,
        "policy_hash": ks_sha256(req.policy_hash.encode()),
        "render_hash": ks_sha256(req.render_hash.encode()),
        "context_hash": ks_sha256(req.context_hash.encode()),
        "submission_mode": req.submission_mode,
        "signer": req.signer_tier,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "attestation_schema": "mnemosyne.attestation.v2",
    }

    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    sig_hex = _KEY.sign(canonical).hex()
    payload["signature"] = {
        "signature_hex": sig_hex,
        "algorithm": "Ed25519",
        "public_key_hex": _PUB_HEX,
    }

    return {"attestation": payload, "canonical_hash": ks_sha256(canonical)}


@app.post("/merkle")
async def compute_merkle(req: MerkleRequest) -> dict:
    """Compute Merkle root binding policy + render + context hashes."""
    root = _merkle_root([req.policy_hash, req.render_hash, req.context_hash])
    return {
        "merkle_root": root,
        "leaves": {
            "policy_hash": ks_sha256(req.policy_hash.encode()),
            "render_hash": ks_sha256(req.render_hash.encode()),
            "context_hash": ks_sha256(req.context_hash.encode()),
        },
    }
