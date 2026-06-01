# Agent v1 Sprint 2 Build Prompt
**Status:** Draft  
**Scope:** Commander + Archivist runtime workflows only  
**Mode:** Fail-Closed

Read `CLAUDE.md` first.

## Context

Sprint 1 is accepted.

Commander and Archivist skeletons, shared schemas, memory scaffolding, telemetry scaffolding, and inert permission enforcement are already in place.

We are now entering **Sprint 2**.

## Sprint 2 Objective

Build the first real internal workflow layer between `commander` and `archivist`.

Sprint 2 must prove that the agent layer can execute narrow, real, file-backed work with:

- valid task envelopes
- artifact-backed evidence retrieval
- claim validation
- lineage output
- memory writes
- audit traceability
- replayable local runs

## Source of Truth

Use:

- `CLAUDE.md`
- `docs/agent_system/v1/agent_architecture_v1.md`
- `docs/agent_system/v1/agent_contracts_v1.md`
- `docs/agent_system/v1/agent_workflows_v1.md`
- `docs/agent_system/v1/agent_memory_model_v1.md`
- `docs/agent_system/v1/agent_telemetry_and_eval_v1.md`
- `docs/agent_system/v1/archivist_write_permissions_addendum_v1.md`

If any older doc, PDF, brief, or summary conflicts with `docs/agent_system/v1/`, `docs/agent_system/v1/` wins.

## Hard Scope Boundary

Active runtime scope in Sprint 2:
- `commander`
- `archivist`

Still inactive:
- `outreach`
- `pilot_ops`

Still forbidden:
- external send
- git push
- delete capability
- protocol-core mutation
- delivery automation
- autonomous approval
- vector DB / embeddings / RAG
- speculative orchestration layers

## Sprint 2 Work to Implement

### Task 1 — Commander real intake flow
Upgrade Commander from skeleton to working intake logic for Sprint 2.

Commander must be able to:
- accept a narrow operator request
- validate whether it is in Sprint 2 scope
- produce a valid task envelope
- reject invalid or ambiguous requests
- route only to Archivist

Valid Sprint 2 intents:
- `collect_evidence`
- `validate_claims`
- `collect_lineage`
- `summarize_status`

Do not activate `draft_outreach`, `prepare_package`, or any delivery path.

---

### Task 2 — Archivist real artifact workflow
Upgrade Archivist from skeleton to working artifact-processing logic.

Archivist must be able to:
- inspect real file refs
- confirm existence
- build `evidence_summary_v1`
- build `claim_validation_v1`
- build `artifact_lineage_v1`
- block missing or unsupported claims
- escalate broken lineage or ambiguous evidence

No PDF OCR. No speculative parsing. File-backed only.

---

### Task 3 — Real memory writes
Implement real writes for the active Sprint 2 memory classes:

- `memory/session/`
- `memory/tasks/`
- `memory/artifacts/`
- `memory/lineage/`
- `memory/approvals/` *(only as referenced state, not approval authority)*

Rules:
- Session Memory write owner remains strictly `commander`
- Archivist may write only within its documented write boundary
- Relationship Memory remains stub-only
- Procedural Memory remains stub-only
- Operator Memory is readable but not silently mutable

---

### Task 4 — Replayable local workflow harness
Create a local harness that runs at least two real workflows end-to-end:

1. **Supported claim path**
   - Commander creates task
   - Archivist inspects real artifact refs
   - claim validation returns `supported`
   - memory writes occur
   - audit events are emitted

2. **Blocked / insufficient evidence path**
   - Commander creates task
   - Archivist inspects refs
   - validation returns `unsupported`, `unclear`, or `blocked`
   - escalation is written if appropriate
   - memory writes occur
   - audit events are emitted

This harness must be replayable locally without network access.

---

### Task 5 — Audit chain hardening
Every meaningful action in Sprint 2 must still emit a schema-valid audit event.

Audit must cover:
- intake accepted
- intake blocked
- task envelope created
- artifact refs checked
- evidence summary created
- claim validation created
- lineage record created
- escalation created
- memory write performed
- workflow summary emitted

Stub logging does not count.

---

### Task 6 — Workflow summaries
Create a minimal workflow summary artifact for each test run.

Suggested output path:
- `telemetry/workflows/run_<id>_summary.json`

This summary must include:
- run ID
- task ID(s)
- intent
- artifacts inspected
- validation result
- lineage result
- memory writes performed
- audit event count
- final workflow state

---

### Task 7 — Self-tests
Expand self-tests so Sprint 2 can prove real behavior.

Minimum required proof:
- valid task envelope generation
- invalid task rejection
- evidence summary from real file refs
- claim validation from real file refs
- blocked claim path
- lineage output creation
- session memory write by commander
- task/artifact/lineage memory writes
- audit event generation across both success and blocked paths
- replayable local workflow run without network access

## Required Files to Create or Update

Expected touched areas:

- `ops/agents/commander/`
- `ops/agents/archivist/`
- `memory/session/`
- `memory/tasks/`
- `memory/artifacts/`
- `memory/lineage/`
- `telemetry/audits/`
- `telemetry/workflows/`
- `ops/runbooks/`
- `ops/prompts/claude/`

Do not create Outreach runtime code.
Do not create Pilot Ops runtime code.

## Sprint 2 Exit Criteria

### ec1_commander_real_intake
Commander can accept valid Sprint 2 requests and create valid task envelopes.

### ec2_commander_fail_closed
Commander blocks invalid, ambiguous, or out-of-scope requests.

### ec3_archivist_real_evidence
Archivist can inspect real artifact refs and produce a real evidence summary.

### ec4_claim_validation_real
Archivist can produce schema-valid claim validation outputs from real file refs.

### ec5_lineage_real
Archivist can produce a real lineage output or escalate when lineage is incomplete.

### ec6_memory_writes_real
Real writes occur to active memory classes in scope.

### ec7_audit_chain_real
Every meaningful action emits schema-valid audit events.

### ec8_replayable_success_path
A supported-claim path runs locally end-to-end.

### ec9_replayable_blocked_path
A blocked or insufficient-evidence path runs locally end-to-end.

### ec10_scope_preserved
No Outreach runtime, no Pilot Ops runtime, no send capability, no protocol-core mutation.

## Output Rules

- Keep the sprint narrow
- Prefer deterministic file-backed implementation
- Reuse Sprint 1 scaffolding
- Fail closed on ambiguity
- Do not overbuild abstractions
- Do not simulate success without real file refs
- Do not claim production readiness

## Required Final Output Format

# Sprint 2 Result

## 1. Exit Criteria Status
Report PASS / FAIL / PARTIAL for:
- ec1_commander_real_intake
- ec2_commander_fail_closed
- ec3_archivist_real_evidence
- ec4_claim_validation_real
- ec5_lineage_real
- ec6_memory_writes_real
- ec7_audit_chain_real
- ec8_replayable_success_path
- ec9_replayable_blocked_path
- ec10_scope_preserved

## 2. Files Created or Updated
List exact paths only.

## 3. Workflow Proof
List:
- success-path proof artifacts
- blocked-path proof artifacts

## 4. Blockers
List only real blockers.

## 5. Scope Check
Explicitly confirm:
- no Outreach runtime
- no Pilot Ops runtime
- no sending
- no delivery automation
- no protocol-core mutation

## Commit Signature

```text
feat(agent-v1-sprint2): implement commander-archivist real workflows with memory writes and replayable audit-backed runs
```