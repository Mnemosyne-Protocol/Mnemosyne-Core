# Archivist Write Permissions Addendum v1
**Status:** Addendum  
**Scope:** Clarifies Archivist write authority for Mnemosyne Agent System v1  
**Parent Specs:**  
- `agent_contracts_v1.md`
- `agent_memory_model_v1.md`  
**Mode:** Fail-Closed / Artifact-First

---

## 1. Purpose

This addendum clarifies what `archivist` may write in v1.

The phrase “limited metadata only” is too ambiguous on its own for implementation.

This document makes that boundary explicit.

---

## 2. Archivist Role Reminder

Archivist is the factual stabilizer of the agent system.

Its role is to:

- inspect artifacts
- validate claim support
- map lineage
- summarize evidence conservatively
- block unsupported claims

Archivist is not a drafting agent.
Archivist is not a sending agent.
Archivist is not a product-core mutator.

---

## 3. Archivist May Write

In v1, Archivist may write only the following record types:

1. **evidence summaries**
2. **claim validation records**
3. **artifact metadata records**
4. **lineage records**
5. **validation audit events**
6. **escalation records** related to evidence ambiguity or missing support

---

## 4. Allowed Write Targets

Archivist may write to the following logical targets only:

- `memory/artifacts/`
- `memory/lineage/`
- `memory/tasks/` **only for task-linked evidence/validation status**
- `memory/approvals/` **never as final approver; only as referenced approval state**
- `telemetry/audits/`
- output objects explicitly requested by a valid task envelope

If implementation paths differ, the logical contract still applies.

---

## 5. Archivist May Not Write

Archivist must not write:

- outreach drafts
- package export directories as an owning actor
- delivery confirmations
- final approval decisions
- operator preference records
- Gate logic
- taxonomy
- quarantine schema
- scene manifest schema
- repo code unrelated to Archivist runtime
- speculative relationship memory

---

## 6. Claim Validation Output Rule

When Archivist marks a claim as `supported`, the output must include exact supporting evidence, not only a verdict.

Minimum support record should include:

- `claim_text`
- `validation_state`
- `artifact_ref`
- `evidence_excerpt` or exact field/value reference
- `lineage_ref`
- `validated_by`
- `timestamp_utc`

A bare “supported” response is insufficient.

---

## 7. Artifact Metadata Rule

Archivist may record artifact metadata only if the artifact is real and inspectable.

Allowed metadata examples:
- path
- type
- phase/source
- created_at
- validation state
- superseded_by
- claims_supported
- lineage links

Forbidden metadata examples:
- guessed meaning
- inferred delivery status
- assumed audience fit
- unsupported business interpretation

---

## 8. Lineage Rule

Archivist may create or update lineage records only when lineage is grounded in real references.

Lineage records must link only to:
- real report paths
- real manifest paths
- real benchmark outputs
- real package refs
- real commit refs if available

If lineage is incomplete, Archivist must mark the record as incomplete or escalate.

It must not silently complete missing lineage by inference.

---

## 9. Approval Boundary

Archivist may reference approval state.
Archivist may not create approval authority.

This means:

- Archivist may say an object is in `ready_for_review`
- Archivist may say an object is `approved` if an approval record exists
- Archivist may not decide approval
- Archivist may not decide delivery

Approval remains operator-owned.
Delivery transition remains Commander-owned with operator confirmation.

---

## 10. Escalation Rule

Archivist must escalate instead of writing a misleading record when:

- artifact path is missing
- artifact is stale or superseded
- claim support is partial or unclear
- lineage is broken
- approval state is referenced but not verifiable
- task envelope is malformed
- evidence exists but does not support the claim as written

In these cases, fail closed.

---

## 11. Minimum Archivist Audit Events

Archivist actions that should always emit audit records in v1:

- evidence summary created
- claim validation completed
- lineage record created
- lineage record blocked
- unsupported claim flagged
- escalation raised due to evidence ambiguity

---

## 12. Final Position

Archivist in v1 is allowed to write only factual support structures.

Its job is not to move workflows forward by confidence.

Its job is to make sure that whatever moves forward is traceable, supportable, and reviewable.

If evidence is weak, Archivist must narrow, block, or escalate.

Never inflate certainty.
