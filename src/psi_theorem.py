"""
Mnemosyne Protocol - Core Psi (ψ) Theorem Implementation
Reference Version: v1.7.1 (Normative)

This module implements the deterministic, fail-closed governance gate.
It evaluates the Boolean conjunction function: ψ = I_1(x) ∧ I_2(x) ∧ ... ∧ I_n(x)
"""

import hashlib
import json
from typing import List, Dict, Any

class MnemosyneGate:
    def __init__(self, policy_version_hash: str):
        self.policy_hash = policy_version_hash
        
    def evaluate_psi(self, invariant_results: List[bool]) -> int:
        """
        The Core Psi Theorem Implementation.
        Fail-Closed: If ANY invariant is False (0), the entire asset is REJECTED.
        No thresholds. No probabilities. Absolute determinism.
        """
        # All conditions must be True. (Logical AND across all invariants)
        psi_value = 1 if all(invariant_results) else 0
        return psi_value

    def canonicalize_cv1(self, payload: Dict[str, Any]) -> str:
        """
        Simulates RFC 8785 JSON Canonicalization Scheme (JCS) 
        to ensure cross-platform deterministic hashing.
        """
        # Sort keys and remove whitespace to enforce strict determinism
        canonical_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        return f"sha256:{hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()}"

    def mint_attestation(self, file_name: str, asset_cid: str, invariants: List[bool], render_merkle_root: str) -> Dict[str, Any]:
        """
        Mints the final Ed25519-ready JSON Attestation Sidecar ONLY IF ψ = 1.
        """
        psi_result = self.evaluate_psi(invariants)
        
        if psi_result == 0:
            raise ValueError("FAIL-CLOSED TRIGGERED: Asset failed one or more invariants. Attestation REJECTED.")

        # Simulate generating the cryptographic passport
        cv1_mock_payload = {"emissive_budget": "0.720000", "allowed_colors": ["#000000", "#FFD700"]}
        
        return {
            "protocol": "mnemosyne:v1.7",
            "asset_identity": {
                "file_name": file_name,
                "asset_cid": asset_cid
            },
            "governance_binding": {
                "policy_hash": self.policy_hash,
                "psi_evaluation": psi_result
            },
            "cryptographic_proofs": {
                "cv1_digest": self.canonicalize_cv1(cv1_mock_payload),
                "render_merkle_root": render_merkle_root,
                "environment_envelope_hash": "sha256:5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f"
            }
        }

# === TEST VECTOR EXECUTION ===
if __name__ == "__main__":
    gate = MnemosyneGate(policy_version_hash="sha256:9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e")
    
    print("[*] Initializing Mnemosyne Fail-Closed Gate...")
    
    # Simulate Invariant Testing (e.g., I_1: Geometry Check, I_2: Texture Check, I_3: IP Filter)
    # Change any True to False to see the Fail-Closed system reject the asset.
    invariants_passed = [True, True, True] 
    
    try:
        sidecar = gate.mint_attestation(
            file_name="hero_mesh_lod0.fbx",
            asset_cid="sha256:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
            invariants=invariants_passed,
            render_merkle_root="sha256:1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b"
        )
        print("\n[+] PASS: Psi Theorem = 1. Attestation Minted Successfully.")
        print(json.dumps(sidecar, indent=2))
    except ValueError as e:
        print(f"\n[-] {e}")
