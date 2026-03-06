[README.md](https://github.com/user-attachments/files/25785635/README.md)
<p align="center">
  <img src="assets/mnemosyne-sigil.svg" alt="Mnemosyne" width="64" />
</p>

<h1 align="center">Mnemosyne v3</h1>
<h3 align="center">The Layer-0 Protocol for Generative AI Governance</h3>

<p align="center">
  <strong>We don't guess. We prove.</strong>
</p>

<p align="center">
  <a href="https://doi.org/10.5281/zenodo.18869318"><img src="https://zenodo.org/badge/DOI/10.5281/zenodo.18869318.svg" alt="DOI" /></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT" /></a>
  <a href="https://creativecommons.org/licenses/by/4.0/"><img src="https://img.shields.io/badge/Spec-CC_BY_4.0-lightgrey.svg" alt="CC BY 4.0" /></a>
  <a href="#"><img src="https://img.shields.io/badge/KS_Standard-v3-cyan.svg" alt="KS Standard" /></a>
  <a href="#"><img src="https://img.shields.io/badge/Fail--Closed-Active-red.svg" alt="Fail-Closed" /></a>
</p>

<p align="center">
  <a href="#the-problem">Problem</a> ·
  <a href="#the-solution">Solution</a> ·
  <a href="#quickstart">Quickstart</a> ·
  <a href="#the-ecosystem">Ecosystem</a> ·
  <a href="#the-ks-standard">KS Standard</a> ·
  <a href="docs/WHITEPAPER.md">Whitepaper</a> ·
  <a href="docs/RBAC.md">Access Tiers</a> ·
  <a href="https://mnemosynelabs.ai">Website</a>
</p>

---

## The Problem

Generative AI creates brilliantly — then forgets what it created.

By frame 25, the sword is a staff. By frame 50, the armor has drifted 12% from the licensed 3D model. By frame 100, the character bible is a suggestion. This isn't a quality problem. It's an **IP sovereignty crisis** with a precise financial cost:

```
Studio budget for a 120-frame UA sequence:

  WITHOUT Mnemosyne:   15 artist-hours rework × $100/hr = $1,500  (per sequence)
  WITH Mnemosyne:       2 artist-hours rework × $100/hr =   $200  (per sequence)
                                                           ──────
  Rework-Hours Saved:   13 hours                     Savings: 85%
```

The industry calls this "Contextual Fragmentation." We call it the enemy. And we don't fight it with prompts. We fight it with mathematics.

---

## The Solution

Mnemosyne is a **Cryptographic Toll Booth** that sits downstream of any generative model. It does not generate pixels. It *verifies* them.

```
   AI Model ──▸ Generated Frame ──▸ ┌──────────────────┐
   (ComfyUI,                        │  MNEMOSYNE GATE  │
    Midjourney,                      │                  │
    SD, Flux,                        │  ψ = ⋀ Iᵢ(x)    │──▸ ψ=1? ──▸ SEALED ✓
    proprietary)                     │                  │         (Evidence Pack)
                                     │  Fail-Closed.    │
                                     │  Zero Trust.     │──▸ ψ=0? ──▸ REJECT ✗
                                     └──────────────────┘         (Full Diagnostics)
```

Every frame either receives a **cryptographically signed Evidence Pack** or is **deterministically rejected** with a full violation report. There is no "warning" state. There is no "soft fail." The gate is fail-closed.

### The Ψ Theorem

The core verification is a Boolean conjunction:

```
ψ(x) = ⋀ᵢ₌₁ⁿ Iᵢ(x)

Where:
  x  = the canonicalized frame payload
  Iᵢ = invariant i (depth, mask, embedding, emissive, color, provenance)
  ψ  = 1 if ALL invariants pass, 0 if ANY single invariant fails
```

One failure collapses the entire conjunction. No interpolation. No "close enough." Binary. Deterministic. Provable.

---

## Quickstart

```bash
# 1. Generate an Ed25519 signing keypair
$ mnemosynectl keygen -o mnemosyne.key
  ✓ Private key: mnemosyne.key (32 bytes, mode 0600)
  ✓ Public key:  a1b2c3d4...

# 2. Sign a governance policy
$ mnemosynectl policy sign -f rules/gameforge.json -k mnemosyne.key
  ✓ Canonical form: 847 bytes
  ✓ KS-salted SHA-256: ff9e9429751eea06...
  ✓ Ed25519 signature: 3a7f...9c2e
  ╔══════════════════════════════════════════╗
  ║  POLICY SEALED — Integrity locked        ║
  ╚══════════════════════════════════════════╝

# 3. Verify a frame against the policy
$ mnemosynectl gate verify \
    --asset frame_042.png \
    --policy gameforge.signed_policy \
    --key mnemosyne.key \
    --emissive-max 720000 \
    --mask-iou-min 997000
  ┌──────────────────────────────────────────┐
  │  ψ = 1  ·  VERDICT: SEALED              │
  └──────────────────────────────────────────┘
  Merkle Root:  ab3f...7e2a
  Signature:    3a7f...9c2e
  Elapsed:      2.41ms

# 4. Audit the ledger
$ mnemosynectl ledger audit -d ledger.json
  ✓ Chain valid: 1,247 events, 0 breaks

# 5. Check ROI
$ mnemosynectl billing roi -d ledger.json
  Hours Saved:   187.5 hrs
  Cost Avoided:  $18,750.00
  Net ROI:       4,200%
```

---

## The Ecosystem

Mnemosyne v3 is not a single tool. It is an integrated system across four runtimes:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────────────┐   │
│  │  🛡️ THE VAULT    │   │  👁️ THE EYES     │   │  🚪 THE GATEKEEPER      │   │
│  │  Rust Core       │   │  Python CV       │   │  TS/Node.js Gateway    │   │
│  │                  │   │                  │   │                         │   │
│  │  • Ψ Engine      │   │  • Depth maps    │   │  • mTLS + JWT auth     │   │
│  │  • Fixed6 math   │◀──│  • Segmentation  │──▶│  • Tenant isolation    │   │
│  │  • Ed25519 sign  │   │  • Embeddings    │   │  • Rate limiting       │   │
│  │  • Merkle trees  │   │  • Color / EMD   │   │  • Circuit breaker     │   │
│  │  • Hash chains   │   │  • Fixed6 quant  │   │  • Billing engine      │   │
│  └────────┬─────────┘   └─────────────────┘   └────────────┬────────────┘   │
│           │                                                  │               │
│  ┌────────▼─────────┐                            ┌──────────▼────────────┐   │
│  │  ⚒️ THE ASA       │                            │  📊 THE DASHBOARD     │   │
│  │  Rust CLI         │                            │  React Executive UI   │   │
│  │                   │                            │                       │   │
│  │  • mnemosynectl   │                            │  • ROI counters       │   │
│  │  • Policy signing │                            │  • Ledger explorer    │   │
│  │  • Local verify   │                            │  • KS audit panel     │   │
│  │  • Ledger audit   │                            │  • Quarantine mode    │   │
│  │  • ROI reporting  │                            │  • Billing summary    │   │
│  └──────────────────┘                            └───────────────────────┘   │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐   │
│  │  🏭 THE INGRESS — ComfyUI Custom Nodes                               │   │
│  │                                                                       │   │
│  │  MnemosyneGate ─▸ PolicyLoader ─▸ KeyLoader ─▸ EvidenceViewer        │   │
│  │  Drops into any workflow. REJECT = pipeline halt. No frame escapes.   │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Build Manifest

| Phase | Name | Runtime | Lines | Purpose |
|-------|------|---------|------:|---------|
| 1 | The Vault | Rust | 2,789 | Ψ engine, Fixed6, Ed25519, Merkle trees, Ledger |
| 2 | The Eyes | Python + PyO3 | 1,483 | CV extraction, Fixed6 quantization, FFI bridge |
| 3 | The Gatekeeper | TypeScript | 1,949 | API gateway, auth, billing, circuit breaker |
| 4 | The Asa | Rust | 2,098 | CLI: verify, sign, audit, ROI |
| 5 | The Ingress | Python + JS | 1,103 | ComfyUI nodes, PNG metadata sealing |
| 6 | The Dashboard | React | 985 | Executive ROI visualization, quarantine mode |
| — | Tests | Python | 396 | Integration suite, Fixed6 roundtrip, KS proofs |
| | **Total** | **4 languages** | **10,803** | |

---

## The KS Standard

Every SHA-256 hash in Mnemosyne v3 is computed as:

```
H(KS_SEED ‖ data)    where KS_SEED = "MNEMOSYNE-KS-V3" (15 bytes)
```

This is the **Knowledge Seed (KS) Entropy Layer** — a cryptographic domain separator that:

1. **Prevents cross-protocol collisions.** A Mnemosyne hash of data `d` will never equal a plain SHA-256 of `d`, or a hash from any other protocol.
2. **Binds every proof to the Mnemosyne namespace.** Evidence Packs, Merkle trees, Ledger chains — all are structurally unforgeable outside the protocol.
3. **Is public and deterministic.** The seed is not a secret. It is a namespace declaration.

**KS is the seed from which all deterministic proof grows.**

The seed is defined identically across all runtimes:

```rust
// Rust (gate.rs)
pub const KS_SEED: &[u8; 15] = b"MNEMOSYNE-KS-V3";
```
```python
# Python (preflight.py)
KS_SEED: bytes = b"MNEMOSYNE-KS-V3"
```
```typescript
// TypeScript (protocol.ts)
const KS_SEED = "MNEMOSYNE-KS-V3";
```

### Domain Separation Proof

```
Input:  {"allowed_colors":["#000000","#FFD700"],"emissive_budget":"0.720000"}

Raw SHA-256 (no KS):   8d3fd83061563864597b0a898cc2a67c1ca79281005b06aa08e7f73e9dbab2a8
KS-salted SHA-256:     ff9e9429751eea06...  (provably different)

The hashes diverge. Domain separation: confirmed.
```

---

## Architecture Principles

### Fail-Closed

If the Gate cannot make a decision, the frame is **blocked**. If the Gateway loses connection to the Core, it returns **503**. If the Dashboard loses its data feed, it enters **Quarantine Mode**. If the CLI cannot load `libgate`, it **aborts**. Nothing unverified ever passes through.

### Zero Trust

Python is an untrusted worker. It extracts numeric tensors. All comparison logic runs in Rust. Python never makes pass/fail decisions. The FFI boundary is the trust boundary. IEEE 754 floats die at the border — everything crosses as Fixed6 (i64, 6 decimal places).

### Deterministic Arithmetic

No floating-point operation ever influences a Gate verdict. All metrics are quantized to `Fixed6` before crossing the FFI boundary:

```
0.720000  →  720_000 (i64)
0.999800  →  999_800 (i64)
```

Multiplication uses `i128` intermediates. Division is checked. Overflow returns `None`, which maps to REJECT. The same input always produces the same output on every platform, every compiler, every optimization level.

### Three-Tier Governance

| Tier | Mutability | Violation → |
|------|-----------|-------------|
| **A** — Immutable Core | System halts if broken | Always FATAL |
| **B** — Threshold Invariants | Version increment only | FATAL if 3+ co-occur |
| **C** — Contextual Rules | Human quorum approval | RECOVERABLE |

---

## Open-Core Boundary

```
  ┌──────────────────────────────────────────────────────────────┐
  │  OPEN SOURCE (MIT)                                           │
  │                                                              │
  │  ✔ Full Ψ engine          ✔ CLI (mnemosynectl)              │
  │  ✔ Fixed6 arithmetic      ✔ ComfyUI nodes                  │
  │  ✔ Ed25519 signing        ✔ Python CV pipeline              │
  │  ✔ RFC 8785 / KS hashing  ✔ TypeScript SDK                 │
  │  ✔ Ledger (SQLite WAL)    ✔ Test vectors + benchmarks      │
  │  ✔ Verification DSL       ✔ Executive Dashboard            │
  ├──────────────────────────────────────────────────────────────┤
  │  ENTERPRISE (Commercial License)                             │
  │                                                              │
  │  ✦ HSM integration (PKCS#11 / CloudHSM / YubiHSM)          │
  │  ✦ S3 + DynamoDB Ledger backend                             │
  │  ✦ Multi-tenant VPC isolation                               │
  │  ✦ SSO/SAML + governance board UI                           │
  │  ✦ SLA-backed support + on-prem deployment                  │
  │  ✦ Billing engine (Success Share computation)                │
  └──────────────────────────────────────────────────────────────┘
```

The OSS core is **verification-complete**. Enterprise adds operational trust infrastructure.

---

## Pricing Model

We sell **Rework-Hours Avoided**, not "AI magic."

| Component | Description |
|-----------|-------------|
| Base Platform Fee | Monthly SaaS fee for Enterprise features |
| Success Share (Capped) | Percentage of verified rework-hours saved |
| Transparent Dashboard | Real-time visibility into fee calculation |

The Ledger is the single source of truth. Every dollar on the invoice maps to a hash-chained event the client can independently verify.

---

## Documentation Access Tiers

| Tier | Role | Access |
|------|------|--------|
| `VIEWER` | Studio executives, PMs | ROI Dashboard, billing summaries |
| `AUDITOR` | QA engineers, compliance | Ledger verification, CLI audit, chain proofs |
| `ARCHITECT` | CTOs, security engineers | Policy signing, KS rotation, HSM config, DSL authoring |

See [docs/RBAC.md](docs/RBAC.md) for the complete access control specification.

---

## Test Vector

Verify your installation against the canonical test vector:

```bash
echo -n '{"allowed_colors":["#000000","#FFD700"],"emissive_budget":"0.720000"}' | shasum -a 256
# Raw SHA-256: 8d3fd83061563864597b0a898cc2a67c1ca79281005b06aa08e7f73e9dbab2a8

mnemosynectl doctor
# [1/6] Fixed6 arithmetic.......... PASS
# [2/6] KS domain separation....... PASS
# [3/6] RFC 8785 test vector....... PASS
# [4/6] SHA-256 hashing............ PASS
# [5/6] Ed25519 sign/verify........ PASS
# [6/6] Ledger hash chain.......... PASS
# ✓ 6/6 tests passed. Fail-closed integrity: CONFIRMED
```

---

## Citation

```bibtex
@misc{salman2026mnemosyne,
  author       = {Salman, Mert Kerem},
  title        = {Mnemosyne Application Layer (v2.0): Deterministic IP Fidelity
                  for Gaming \& Ad-Tech},
  year         = {2026},
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.18869318},
  url          = {https://doi.org/10.5281/zenodo.18869318}
}
```

---

## License

Specification: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) · Code: [MIT](LICENSE)

---

<p align="center">
  <strong>Mnemosyne Labs</strong><br/>
  Layer-0 Deterministic Governance Protocol<br/><br/>
  <em>"Trust is a vulnerability. We require cryptographic proof."</em>
</p>
