# The Mnemosyne Engineering Standard
*Systems Over Syntax: Our Constitutional Baseline for Enterprise AI.*

At Mnemosyne Labs, we believe that as the cost of writing code drops to zero, the value of rigorous engineering architecture skyrockets. Foundational models generate text; engineers build systems. We do not deploy "working demos"—we deploy fault-tolerant, stateful protocols.

## 1. The "1989 Baseline" (Data Integrity & State)
Before AI, software had to survive strict constraints. We maintain this discipline:
- **State & Idempotency:** All agentic workflows are strictly idempotent. 
- **Transaction Boundaries:** Memory states are treated as strict database transactions. Rollbacks are instantaneous and deterministic.
- **Inverse Context Flow (ICF):** Data sovereignty is absolute. Context is redacted and verified locally *before* it ever reaches an external API.

## 2. AI-Specific Reliability 
- **Prompt Versioning:** Prompts are treated as production code. No prompt changes without passing regression evaluations against the Golden Data Set.
- **Shadow Verification:** Output verification is not an afterthought. Agents are paired with verifiers (via CLIP/Embedding distance checks) to gatekeep continuity before rendering.
- **Graceful Degradation:** If an external LLM/Vision model fails, the system must degrade predictably, not crash silently.

## 3. The 70-Point Threshold
A prototype scores 30 points. Enterprise-ready software scores 70+. We do not ship to production unless the protocol passes strict observability, rollback, and concurrency tests. The Mnemosyne Protocol is built to withstand the "friction of the real world."
