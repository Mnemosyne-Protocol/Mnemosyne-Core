# VERSIONING & ROADMAP

> **Mnemosyne is a fail-closed constitutional layer.** We do not silently adapt. We **version** every governance change. Policies are treated as signed, versioned artifacts so studios and enterprises can audit exactly **what rules were active**, **when**, and **why**.
> 
> *Investor signal: **controlled evolution**, not heuristic drift.*

---

## 📜 PROTOCOL RELEASE HISTORY

| Version | Date | Type | Summary | Reference |
| :--- | :--- | :--- | :--- | :--- |
| **spec-v1.7.1-draft** | 2026-02-28 | `SPEC PATCH` | Schema hardening + formatting fixes. Removed non-hex characters from payload samples. No semantic changes to the core protocol. | [X Post / Spec] |
| **spec-v1.7.0-draft** | 2026-02-27 | `SPEC` | Formal specification draft: ψ theorem, Merkle render proofs, CV1 canonicalization, attestation schemas. | - |
| **v1.6.0-beta** | 2026-02-23 | `BETA` | Benchmark suite + multi-agent ablation and standardized metrics (CHR, reject rate, latency proxy). | [Zenodo v1.6.1] |
| **v0.1.1-alpha** | 2026-02-22 | `ALPHA PATCH`| Orchestrator demo & executable artifacts demonstrating FAIL → REJECT → ROLLBACK → ACCEPT loop. | - |
| **v0.1.0-alpha** | 2026-02-22 | `ALPHA` | Initial public artifacts: continuity trace + minimal open-core scaffolding. | - |

*(Note: Every major update is published via Zenodo for archival credibility and backward-compatible additive changes.)*

---

## 🗺️ DIRECTIONAL ROADMAP

*Roadmap is directional and may change based on research findings, security requirements, and customer needs. We measure progress in governance maturity.*

### [ NEXT ] NEAR-TERM: Hardened Change Control + Trust Signals
- Signed release cadence (spec + implementation) with consistent changelog format.
- Policy bundle versioning: explicit policy hash + compatibility notes.
- Determinism Envelope manifest: pinned versions + environment hash surfaced in UI.

### [ SOON ] MID-TERM: Enterprise Operationalization
- Reject taxonomy standardization: reason codes + dashboards (reject rate, resamples/frame, latency proxy).
- Audit export pack: attestations + logs packaged for compliance workflows.
- CI/CD hooks: policy updates only via review + signed increment (no silent drift).

### [ LATER ] LONG-TERM: Generalization Beyond Media
- Extend Layer-0 governance primitives from continuity to broader enterprise GenAI workflows.
- Pluggable invariant agents (style, geometry, policy, factual constraints) with compositional ψ gating.
- Cross-studio interoperability: portable policy bundles + verifiable proofs across vendors.

---
*Standard Release Notes Template for Contributions:*
`VERSION: vX.Y.Z` | `TYPE: ALPHA/BETA/SPEC/PATCH` | `SCOPE: [1 Line]` | `BREAKING: Y/N` | `SECURITY: Y/N` | `PROOFS: [Hashes]` | `METRICS: [CHR, Reject Rate]`
