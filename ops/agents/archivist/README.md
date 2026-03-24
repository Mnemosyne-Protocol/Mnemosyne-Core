# Archivist Agent — Sprint 1
**Status:** Active
**Scope:** Sprint 1 (Commander + Archivist only)
**Mode:** Fail-Closed / Artifact-First
**Source of truth:** `docs/agent_system/v1/agent_contracts_v1.md`

---

## Role

Evidence retrieval, artifact lineage, and factual validation.

## Sprint 1 Responsibilities

- Validate that referenced artifact paths exist on disk
- Build evidence summaries from real artifact refs
- Validate claims (artifact-first, conservative)
- Build lineage records
- Escalate on missing, ambiguous, or unverifiable evidence
- Emit schema-valid audit events for every meaningful action
- Fail closed on any provenance gap

## Must Not

- Rewrite source code
- Draft outreach
- Send messages
- Upgrade uncertain evidence to supported
- Use embeddings / vector DB / RAG
- Mutate Gate, taxonomy, or policy

## Files

| File | Purpose |
|------|---------|
| `archivist.py` | Archivist implementation |
| `models.py` | Evidence/lineage/escalation models |
| `self_test.py` | Self-contained test suite (no network required) |

## Running Self-Tests

```bash
cd /Volumes/MNEMOSYNE-GATE/Vault/repos/Mnemosyne-Core
python -m ops.agents.archivist.self_test
```

## Claim Validation Rule

A claim is `supported` only when:
- `artifact_ref` file exists on disk
- `evidence_excerpt` is provided
- `lineage_ref` is provided

Any missing element → `unsupported`, `partially_supported`, or `insufficient_evidence`.
Never upgrade a claim by inference.
