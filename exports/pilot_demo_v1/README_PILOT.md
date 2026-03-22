# Mnemosyne Protocol — Pilot Demo Package
**Version:** pilot_demo_v1
**Protocol:** Mnemosyne v3.0.0 · DOI: 10.5281/zenodo.18884426
**Source Phase:** Phase 9 (FAZ 9D.3 — Live UE5 Editor Execution)

---

## What this package contains

Two recorded sessions against a live Mnemosyne Gate API, run from inside
Unreal Engine 5 via Python delegate binding. Each session submitted three
synthetic frames for evaluation. No results were simulated or fabricated —
the Gate is a running service; the verdicts are its live output.

---

## 01_PASS_SCENARIO — What an approved render looks like

Three frames were submitted. All three passed every Gate invariant (ψ = 1).
The Gate issued `Mnemosyne_Certified_Passport.json`.

Key files:
- `scene_manifest_v1.json` — the scene record: project, level, frame list,
  per-frame KS-SHA256 hashes, operator identity, pipeline source.
- `Mnemosyne_Certified_Passport.json` — the certification artifact.
  Contains: session ID, frame count, Merkle root over frame hashes,
  gate version, policy pack version, and a signature over the passport body.
  This file is what downstream systems check to confirm a render was cleared.
- `pass_run_summary.json` — full session record: per-frame verdicts, latencies,
  ledger record IDs, taxonomy version, loopback compliance flag.

What this proves: when all invariants pass, the Gate produces a verifiable,
auditable certification artifact with a deterministic Merkle root. No passport
is issued until every frame clears. One frame failure would have blocked the
entire session.

---

## 02_FAIL_SCENARIO — What a blocked render looks like

Three frames were submitted. Frame 1 was intentionally submitted with
invalid attestation (non-KS hash mode, invalid signature format, FAIL
source invariants, emissive budget over threshold).

The Gate stopped at frame 1. No certification was issued. No passport file
exists in this folder — by design.

Key files:
- `fail_run_summary.json` — full session record, including the exact
  violations detected on the rejected frame.
- `rejection_evidence.json` — extracted summary: abort reason, quarantine ID,
  per-invariant violation list.
- `scene_manifest_v1.json` — the scene record for this session.

What this proves: the Gate is fail-closed. A single non-compliant frame
stops the pipeline immediately. No partial certification is possible.
The quarantine ID is issued by the Gate and logged for audit.

---

## What `Mnemosyne_Certified_Passport.json` is

It is a session-scoped certification record. It does not "approve" content
aesthetically. It certifies that every frame in a render session passed all
cryptographic and policy invariants at the time of submission:
- KS-salted SHA-256 hashes matched
- Ed25519 attestation signature was valid
- Source invariants (mesh topology, frame integrity, ROI hashes) all passed
- Emissive budget did not exceed the Fixed6 threshold
- Policy mode was correctly declared

The Merkle root in the passport binds all frame hashes together. If any frame
is later swapped or altered, the root will not match.

---

## Why fail-closed matters in a production pipeline

The common failure mode in AI-assisted pipelines is silent acceptance: a
non-compliant asset passes downstream because no system was authoritative
enough to block it. Mnemosyne's default posture is REJECT. An asset moves
forward only on an explicit APPROVED verdict from the Gate — not on
absence of rejection.

In a studio context: if a vendor delivers a batch where one asset has been
altered after signing, or where the source model is undeclared, that asset
is quarantined before it enters your pipeline. The rest of the batch is
unaffected. No human review required for the block — only for the quarantine
disposition.

---

## What is NOT being claimed

- This package does not contain production renders. Frames are deterministic
  synthetic test bytes that exercise the full Gate submission code path.
- The passport signature uses a KS-HMAC fallback because the `cryptography`
  library was not installed in this environment. In a production deployment,
  the signature would be a proper Ed25519 signature over the passport body.
  The Gate evaluation logic, fail-closed behavior, and artifact structure are
  identical regardless.
- This is a protocol proof, not a finished product integration. Phase 10 is
  the packaging phase. Real pipeline integration is scoped to Phase 11+.

---

*Mnemosyne Labs — Istanbul*
*Contact: ks@mnemosynelabs.ai*
