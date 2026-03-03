## // PROTOCOL FAQ & CORE SPECIFICATION

> **"My goal is to solve AI's memory problem and turn generative systems into a beneficial, mathematically governed assistant for humanity."**
> — KS | The Architect

### 1. ARCHITECTURE & GOVERNANCE

**WHAT IS THE MNEMOSYNE PROTOCOL?**
Mnemosyne is a **Zero-Trust, deterministic orchestration and governance layer** that evaluates generated artifacts with explicit invariants, canonicalizes constraint representations, and emits **tamper-evident proofs** for accepted outputs.

**WHERE DOES MNEMOSYNE SIT IN THE STACK?**
It sits **between** generators (models/tools) and downstream production. Generators propose artifacts; Mnemosyne **verifies** them, blocks non-compliant outputs (fail-closed), and attaches proofs to compliant ones.

**WHAT IS THE CORE MATHEMATICAL RULE BEHIND FAIL-CLOSED GOVERNANCE?**
Mnemosyne evaluates every generated asset with the **ψ (Psi) theorem**: `ψ = ∧ I_i(x)`. Each invariant `I_i` must pass. If any invariant fails, ψ collapses to **0** and the output is **REJECTED**.

### 2. CRYPTOGRAPHY & DETERMINISM

**WHY DO YOU USE RFC 8785 CANONICALIZATION?**
Because JSON serialization can differ across implementations. Canonicalization ensures the **same logical object** produces the **same canonical string**, enabling stable hashing, integrity proofs, and reproducible verification.

**WHAT IS CV1 (CANONICALIZED CONSTRAINT VECTORS)?**
CV1 is a deterministic constraint representation where continuous values are stored as fixed-point strings (not raw floats). This reduces cross-platform mismatches and makes constraint evaluation reproducible across nodes.

**WHAT IS THE TECHNICAL LINK BETWEEN MERKLE TREES AND ZERO-TRUST?**

Zero-Trust requires continuous verification. **Merkle Trees** provide **hash-based integrity** and **membership proofs** for sequences. Any unauthorized change modifies the root hash, making tampering detectable. 

**WHAT IS AN ATTESTATION SIDECAR FILE?**
A compact cryptographic 'passport' produced when an artifact passes the gate. It binds the artifact identity, policy hash, canonical digests, constraint digest, and integrity proofs so provenance can be verified later.

### 3. SECURITY & DATA SOVEREIGNTY

**HOW DOES THE INVERSE CONTEXT FLOW (ICF) ARCHITECTURE HELP WITH SECURITY?**

```mermaid
graph LR
    subgraph Untrusted_Zone [Untrusted Zone - Cloud]
        A[AI Reasoning Engine<br>Models / Tools]
    end

    subgraph Sovereign_Zone [Trusted Sovereign Zone - Local]
        B[(Local Memory & IP<br>Sensitive Context)]
        C{Fail-Closed<br>Verification Gate}
        D[Verified Output +<br>Tamper-Evident Proof]
    end

    A -- "Inverse Context Flow<br>(Pulls logic to local)" --> B
    B -- "Candidate Artifact" --> C
    C -- "Pass (ψ = 1)" --> D
    C -. "Fail (ψ = 0)<br>Rollback" .-> B

    style Untrusted_Zone fill:#1a1a1a,stroke:#ff3333,stroke-width:2px,color:#fff
    style Sovereign_Zone fill:#1a1a1a,stroke:#73f442,stroke-width:2px,color:#fff
    style A fill:#2d2d2d,stroke:#ff3333,color:#fff
    style B fill:#2d2d2d,stroke:#73f442,color:#fff
    style C fill:#2d2d2d,stroke:#73f442,color:#fff
    style D fill:#2d2d2d,stroke:#73f442,color:#fff
  ```  

ICF is a **local-first** pattern: keep sensitive memory (assets, constraints, policies) under operator control; minimize what must leave the environment; prefer exchanging **proofs** over exporting raw IP.

**HOW DO YOU PROTECT CONFIDENTIAL PROJECTS AND IP?**
By keeping policies, constraint vectors, and attestations under your control; minimizing external exposure; and enabling verification via cryptographic proofs rather than sending raw confidential assets outside the trust boundary.
