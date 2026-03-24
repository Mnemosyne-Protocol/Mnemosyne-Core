# Mnemosyne Agent Runtime Schemas — Sprint 1
**Status:** Active  
**Scope:** Shared runtime schemas for the Mnemosyne Agent System v1  
**Mode:** Fail-Closed / Sprint 1

---

## Purpose

This directory contains the shared JSON schemas used by the Sprint 1 runtime layer of the Mnemosyne internal agent system.

These schemas support:

- Commander ↔ Archivist task exchange
- claim validation
- audit logging
- readiness checks
- escalation records

This directory is an implementation layer.

It does **not** replace the constitutional source of truth under:

`docs/agent_system/v1/`

If any runtime schema conflicts with the constitutional docs, the constitutional docs win.

---

## Files

### `task_envelope.schema.json`
Defines the task envelope exchanged between agents.

Used for:
- task creation
- routing
- intent declaration
- output expectations
- retry / correlation / approval metadata

Primary role:
- structured A2A communication
- fail-closed task passing

---

### `claim_validation.schema.json`
Defines the validation record returned primarily by Archivist.

Used for:
- claim support checks
- evidence linkage
- artifact-backed validation
- blocked / insufficient-evidence outcomes

Primary role:
- prevent unsupported claims
- ensure every supported claim has explicit evidence

---

### `audit_event.schema.json`
Defines the required audit event format for meaningful runtime actions.

Used for:
- task creation
- task blocking
- validation completion
- evidence summary generation
- lineage creation
- escalation
- status summary generation

Primary role:
- traceability from Run #1
- no stub logging
- schema-valid audit coverage

---

### `package_readiness.schema.json`
Defines the readiness record for package/export validation.

Used for:
- README presence
- checksum presence
- manifest presence
- evidence completeness
- blocked / ready-for-review state

Primary role:
- fail-closed package readiness checks

Sprint 1 note:
- schema may exist before Pilot Ops runtime becomes active

---

### `escalation.schema.json`
Defines the escalation record for blocked or ambiguous situations.

Used for:
- evidence ambiguity
- missing artifacts
- invalid task state
- broken lineage
- unresolved validation conflicts

Primary role:
- explicit escalation instead of silent failure

---

## Sprint 1 Runtime Rule

In Sprint 1, the active runtime focus is:

- `commander`
- `archivist`

This means:

- `task_envelope.schema.json` is active
- `claim_validation.schema.json` is active
- `audit_event.schema.json` is active

The following may exist as schemas/stubs without full runtime usage yet:

- `package_readiness.schema.json`
- `escalation.schema.json`

---

## Implementation Notes

- Shared runtime schemas live under `ops/schemas/`
- This is an implementation-path choice only
- It does not override `docs/agent_system/v1/` as source of truth
- Any inactive capability must remain inert until its runtime phase is active

Example:
- Commander Gmail Draft surface = `INERT_UNTIL_OUTREACH_RUNTIME`

---

## Final Position

These schemas are here to keep the Sprint 1 runtime narrow, explicit, and auditable.

They exist to prevent:
- loose task passing
- unsupported claim drift
- fake audit coverage
- silent ambiguity
- fail-open runtime behavior

**Constitution defines the rules.  
Schemas define the executable contract.**