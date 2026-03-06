# Mnemosyne v3 — Technical Whitepaper

```
Document:     Mnemosyne Layer-0 Protocol — Formal Technical Specification
Version:      3.0.0
Date:         2026-03-06
Author:       Kerem Salman
License:      CC BY 4.0
DOI:          10.5281/zenodo.18869318 (v2.0 base)
Status:       NORMATIVE
```

---

## Abstract

Generative AI systems produce content probabilistically. Enterprise applications — AAA gaming IP, global ad-tech networks, film VFX — require deterministic identity preservation. "Similar" is legally insufficient. This paper formalizes the Mnemosyne v3 Protocol: a zero-trust, fail-closed verification layer that sits downstream of any generative model and enforces cryptographically provable compliance through the Ψ (Psi) Theorem, the KS (Knowledge Seed) domain separation standard, and a three-tier governance codex. We present the complete formal specification, the economic model ("Rework-Hour Arbitrage"), and the implementation architecture across four runtimes (Rust, Python, TypeScript, JavaScript).

---

## 1. Introduction: The Cost of Probabilistic Chaos

### 1.1 The Contextual Fragmentation Problem

Generative models are stateless between inference calls. Frame N has no memory of Frame N-1. This architectural reality produces a specific failure mode: **Contextual Fragmentation** — the silent, automatic, progressive drift of generated assets away from their canonical specification.

In a 120-frame User Acquisition (UA) sequence for a gaming IP, a 5% morphological drift in a character's armor constitutes a critical IP violation. Prompt steering provides an illusion of control; it does not provide a mathematical guarantee. The studio discovers the drift during Human-in-the-Loop QA, burns artist hours on rework, collapses the production schedule, and erases the ROI of the generative pipeline.

### 1.2 The Mnemosyne Thesis

We do not attempt to improve generation. We verify it. Mnemosyne operates as a **Layer-0 Deterministic Governance Protocol** — a cryptographic toll booth positioned between the generative model and the production pipeline. The model generates. The Gate verifies. The frame either receives a signed Evidence Pack or it does not exist.

---

## 2. The Ψ (Psi) Theorem

### 2.1 Formal Definition

Let `x` be a canonicalized asset payload and let `I = {I₁, I₂, ..., Iₙ}` be the active invariant set defined by the governance policy. The Mnemosyne verification function is:

```
ψ(x) = ⋀ᵢ₌₁ⁿ Iᵢ(x)
```

Where each `Iᵢ: X → {0, 1}` is a Boolean predicate that evaluates a specific metric of `x` against a threshold. The conjunction operator (`⋀`) ensures that `ψ = 1` if and only if **every** invariant passes. A single failure collapses the result to `ψ = 0`.

### 2.2 Properties

**Totality.** `ψ` is defined for every valid canonical payload. Invalid payloads (malformed images, corrupted bytes) fail canonicalization, which maps to `ψ = 0` with error code `A-CAN-001`.

**Determinism.** For a fixed invariant set `I` and a fixed payload `x`, `ψ(x)` always returns the same value. This is enforced by Fixed6 arithmetic (Section 3) — no IEEE 754 floats influence the decision.

**Zero short-circuit.** The implementation evaluates ALL invariants even after the first failure. The complete violation vector is collected and returned. This is an engineering constraint, not a mathematical one: studios need the full diagnostic report to fix the frame in a single rework pass.

**Fail-closed default.** If the evaluation function cannot execute (out of memory, cryptographic failure, FFI error), the result is `ψ = 0`. The frame is never released without a verified positive verdict.

### 2.3 Invariant Taxonomy

Invariants are classified by governance tier:

| Tier | Name | Violation Consequence |
|------|------|----------------------|
| A | Immutable Core | Always `REJECT_FATAL`. Cannot be overridden. |
| B | Threshold | `REJECT_RECOVERABLE` for 1-2 violations. Escalates to `REJECT_FATAL` if 3+ Tier B violations co-occur (cascade rule). |
| C | Contextual | `REJECT_RECOVERABLE`. Modifiable via human quorum. |

The cascade rule exists because multiple simultaneous small drifts compose into an aggregate drift that cannot be repaired by targeted editing.

### 2.4 Built-in Invariant Set

| ID | Tier | Metric | Direction | Default Threshold |
|----|------|--------|-----------|-------------------|
| `GIL.DEPTH_ENVELOPE.01` | B | L2 norm of depth map vs. reference | ≤ | 0.001500 |
| `GIL.MASK_IOU.01` | B | Intersection-over-Union of foreground mask | ≥ | 0.997000 |
| `GIL.EMBEDDING_COSINE.01` | B | CLIP/DINOv2 cosine similarity | ≥ | 0.999800 |
| `GIL.EMISSIVE_BUDGET.01` | B | Mean luminance (emissive proxy) | ≤ | 0.720000 |
| `CORE.PROVENANCE.01` | A | Model identity hash match | = | (policy-defined) |
| `CORE.CANONICAL.01` | A | RFC 8785 serialization success | = | (boolean) |

---

## 3. Fixed6 Deterministic Arithmetic

### 3.1 Representation

All numeric values that cross the verification decision boundary are represented as `Fixed6`: a signed 64-bit integer with 6 implicit decimal places.

```
Value 0.720000  →  Stored as 720_000 (i64)
Value 0.999800  →  Stored as 999_800 (i64)
Value 1.000000  →  Stored as 1_000_000 (i64)
```

The scale factor is `10⁶ = 1,000,000`. This representation eliminates IEEE 754 rounding divergence across platforms, compilers, and optimization levels.

### 3.2 Arithmetic Operations

Multiplication uses `i128` intermediates to prevent overflow:

```
a ×₆ b = (a × b) / SCALE     computed as: (i128(a) × i128(b)) / i128(SCALE)
a ÷₆ b = (a × SCALE) / b     computed as: (i128(a) × i128(SCALE)) / i128(b)
```

All operations are checked. Overflow returns `None`, which the Gate maps to `REJECT_FATAL`.

### 3.3 The Float Extinction Boundary

IEEE 754 floats exist in exactly two places:

1. **Python CV extractors** — produce float64 metrics from image analysis.
2. **Compile-time constants** — `Fixed6::from_float_const()` is evaluated at compile time for human-readable threshold definitions.

At the PyO3 FFI boundary, floats are quantized via `round(value × 10⁶)` and transmitted as `i64`. From that point forward, no floating-point operation ever occurs in the decision path. The Rust Gate operates exclusively on `Fixed6`.

---

## 4. The KS (Knowledge Seed) Standard

### 4.1 Purpose

The Knowledge Seed is a cryptographic domain separator applied to every SHA-256 operation in the Mnemosyne Protocol.

```
H_KS(data) = SHA-256(KS_SEED ‖ data)

Where KS_SEED = "MNEMOSYNE-KS-V3" (15 bytes, ASCII, public)
```

### 4.2 Security Properties

**Domain separation.** For any byte string `d`: `H_KS(d) ≠ SHA-256(d)`. This prevents a hash computed by any other protocol from being accepted as a valid Mnemosyne proof.

**Cross-protocol collision resistance.** Even if an attacker finds `d₁ ≠ d₂` such that `SHA-256(d₁) = SHA-256(d₂)` (a SHA-256 collision), it does not follow that `H_KS(d₁) = H_KS(d₂)`, because the KS prefix shifts the internal hasher state before the data is consumed.

**Namespace binding.** Evidence Packs, Merkle trees, Ledger events, and policy hashes are all computed with `H_KS`. A proof from one Mnemosyne deployment is verifiable by any other deployment that knows the (public) KS seed.

### 4.3 Application Points

| Component | Hash Function Used | KS Applied |
|-----------|-------------------|------------|
| Canonical payload hash | `sha256_bytes()` | Yes |
| Merkle internal nodes | `sha256_pair()` | Yes |
| Ledger event hash | `LedgerEvent::compute_hash()` | Yes |
| Policy signing hash | `canonicalize_json()` | Yes |
| Evidence Pack binding | All fields | Yes |
| Third-party file checksums | `sha256_bytes_raw()` | No (explicitly unsalted) |

### 4.4 Cross-Runtime Consistency

The KS seed is defined identically in Rust, Python, and TypeScript. The `mnemosynectl doctor` command includes a domain separation test that verifies `H_KS(d) ≠ SHA-256(d)` at startup.

---

## 5. Evidence Pack and Merkle Attestation

### 5.1 Structure

Every frame that achieves `ψ = 1` receives an Evidence Pack:

```json
{
  "canonical_hash":    "H_KS(canonical_bytes)",
  "policy_hash":       "H_KS(policy_bytes)",
  "merkle_root":       "H_KS(H_KS(policy ‖ render) ‖ context)",
  "timestamp":         "ISO 8601 (deterministic, NTP-synchronized)",
  "signature":         "Ed25519(signing_key, canonical_bytes)",
  "verifying_key":     "Ed25519 public key"
}
```

### 5.2 Merkle Tree

The Evidence Pack binds three leaves into a root:

```
         H_KS(left ‖ context)     ← Merkle Root
        /                    \
  H_KS(policy ‖ render)    context_hash
  /                 \
policy_hash    canonical_hash
```

Any third party with the root hash can verify that a specific frame was verified under a specific policy.

### 5.3 PNG Metadata Embedding

On SEALED verdict, the Evidence Pack is embedded into the output PNG as `mnemosyne:`-prefixed tEXt chunks (ISO/IEC 15948). The image becomes a self-contained cryptographic passport.

---

## 6. Append-Only Hash-Chained Ledger

### 6.1 Event Structure

Every Gate decision is recorded as a `LedgerEvent`:

```
event_hash = H_KS(seq ‖ timestamp ‖ prev_hash ‖ tenant_id ‖ project_id ‖ kind ‖ rework_cost)
```

Each event stores `prev_hash`, the hash of the preceding event. The genesis event uses `0x00...00`. This forms a hash chain: deletion or modification of any event breaks the chain and is immediately detectable.

### 6.2 Integrity Verification

```
verify_chain():
  for each event in ledger:
    assert event.prev_hash == hash(preceding_event)
    assert event.event_hash == recompute_hash(event)
    assert event.seq == previous_seq + 1
```

The `mnemosynectl ledger audit` command executes this verification. Exit code 0 means the chain is intact. Exit code 4 means tampering was detected.

---

## 7. The Rework-Hour Arbitrage Model

### 7.1 Economic Thesis

The Mnemosyne revenue model is predicated on a measurable arbitrage:

```
Rework_Cost_Without = rejected_frames × avg_hours_per_fix × hourly_rate
Rework_Cost_With    = platform_cost
Savings             = Rework_Cost_Without - Rework_Cost_With
```

The studio pays a fraction of the savings. The rest is pure client ROI. The Ledger provides cryptographic proof of every rejected frame that would have reached — and failed — human QA.

### 7.2 Pricing Structure

| Component | Formula |
|-----------|---------|
| Base Platform Fee | Fixed monthly SaaS fee |
| Success Share | `min(savings × share_pct, cap)` |
| Total | `base_fee + success_share` |

All arithmetic uses Fixed6. The client can independently audit every line item by replaying the Ledger and verifying the Merkle chain.

### 7.3 Benchmark (v2.0, Published)

| Metric | Without Mnemosyne | With Mnemosyne |
|--------|-------------------|----------------|
| Artist hours per sequence | 15 hrs | 2 hrs |
| Rework cost per sequence | $1,500 | $200 |
| Delivery time | 3–4 days | 1 day |
| Cost reduction | — | **85%** |

---

## 8. Reject Taxonomy

### 8.1 Binary Classification

Every rejection is classified into exactly one of:

| Class | Meaning | Exit Code (CLI) |
|-------|---------|-----------------|
| `REJECT_FATAL` | Frame cannot be salvaged. Regenerate from scratch. | 2 |
| `REJECT_RECOVERABLE` | Frame is close. Targeted adjustment can fix it. | 3 |

### 8.2 Classification Rules

1. Any Tier A violation → `FATAL`.
2. Any violation declared `FATAL` by the rule author → `FATAL`.
3. If 3+ Tier B `RECOVERABLE` violations co-occur → `FATAL` (cascade).
4. Otherwise → `RECOVERABLE`.

### 8.3 Error Code Schema

Format: `{TIER}-{DOMAIN}-{SEQ}` (e.g., `B-GEO-101`).

Domains: `PROV` (provenance), `GEO` (geometry), `CLR` (color), `EMB` (embedding), `EMI` (emissive), `BRD` (brand), `CTX` (context), `CAN` (canonical).

---

## 9. Access Control Tiers

The documentation and operational surface is segmented by role:

### Tier: VIEWER

**Audience:** Studio executives, project managers, finance.

**Access:** ROI Dashboard (read-only), billing summaries, accept-rate trends, cost-savings reports. No access to policy internals, signing keys, or ledger events.

**Key actions:** Interpret the ROI report. Validate that cost savings match the invoice. Present to stakeholders.

### Tier: AUDITOR

**Audience:** QA engineers, compliance officers, external auditors.

**Access:** Everything in VIEWER, plus: Ledger event browser, chain integrity verification (`mnemosynectl ledger audit`), Evidence Pack inspection, violation reports with full diagnostic data, CLI audit commands.

**Key actions:** Verify the hash chain. Spot-check individual frame verdicts. Confirm that Evidence Pack signatures match the policy. Generate audit reports for SOC 2 / ISO 27001.

### Tier: ARCHITECT

**Audience:** CTOs, security engineers, integration leads.

**Access:** Everything in AUDITOR, plus: Policy authoring (`.mnm` DSL), policy signing (`mnemosynectl policy sign`), Ed25519 key management, KS seed rotation (Enterprise), HSM configuration (Enterprise), threshold tuning, invariant development, Gateway configuration, multi-tenant setup.

**Key actions:** Author governance policies. Sign and deploy them. Configure the Gate's invariant thresholds. Manage the cryptographic key lifecycle. Integrate HSMs for hardware-bound signing. Design the verification pipeline for new projects.

---

## 10. Implementation Notes

### 10.1 Runtime Selection

| Runtime | Responsibility | Justification |
|---------|---------------|---------------|
| Rust | Gate engine, crypto, arithmetic | No GC. Memory safety. Bit-reproducible Fixed6 math. |
| Python | CV feature extraction | The ML ecosystem (PyTorch, ONNX, OpenCV) is Python-native. |
| TypeScript | API gateway, billing | SDK consumers are overwhelmingly TypeScript shops. |
| JavaScript | ComfyUI frontend | ComfyUI's extension system is browser-based JS. |

### 10.2 Trust Boundaries

```
Python (untrusted) ──▸ Fixed6 quantization ──▸ PyO3 FFI ──▸ Rust (trusted)
                      ^^^^^^^^^^^^^^^^^^^^
                      THE FLOAT EXTINCTION BOUNDARY
                      IEEE 754 dies here. i64 begins.
```

### 10.3 Build

```bash
# Rust core + CLI
cargo build --release

# Python extension (via maturin)
maturin develop --release

# Gateway
cd gateway && npm install && npm run build

# ComfyUI extension
cp -r comfyui-mnemosyne/ $COMFYUI_PATH/custom_nodes/
```

---

## References

1. Salman, M.K. (2026). *Mnemosyne Application Layer (v2.0): Deterministic IP Fidelity for Gaming & Ad-Tech.* Zenodo. https://doi.org/10.5281/zenodo.18869318
2. Rundgren, A. (2017). *JSON Canonicalization Scheme (JCS).* RFC 8785.
3. Bernstein, D.J. et al. (2012). *High-speed high-security signatures.* Ed25519.
4. Merkle, R. (1988). *A Digital Signature Based on a Conventional Encryption Function.* CRYPTO '87.

---

*This document is the normative technical specification for Mnemosyne v3. All implementations must conform to the definitions, properties, and constraints stated herein.*

*"Complexity is our moat. Determinism is our product. Proof is our deliverable."*
