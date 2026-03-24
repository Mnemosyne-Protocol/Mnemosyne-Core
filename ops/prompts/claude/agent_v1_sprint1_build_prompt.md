# Agent v1 Sprint 1 Build Prompt
**Status:** Active  
**Scope:** Commander + Archivist only  
**Mode:** Fail-Closed

Read `CLAUDE.md` first.

## Context

- Mnemosyne is a Verification Protocol, not a generator.
- The agent layer is internal-only and exists to accelerate evidence retrieval, pilot packaging, outreach drafting, approval routing, and operational continuity.
- Cardinal rule: **NO EMAIL WITHOUT ONAY**.
- Default mode: **fail-closed**.
- We are implementing **v1 only**.
- We are **not** building autonomy, outbound sending, or product logic changes.

## Source-of-Truth Rules

1. Source of truth for the agent layer = `docs/agent_system/v1/`
2. If any older doc, PDF, brief, or summary conflicts with `docs/agent_system/v1/`, `docs/agent_system/v1/` wins.
3. Do not invent missing files, states, or workflows.
4. Do not widen scope beyond Sprint 1.
5. If `agent_contracts_v1.md` §9 lists fewer than 6 memory classes, treat `agent_architecture_v1.md` §7 as authoritative — the 6-class model applies.
6. `telemetry/audits/audit_log.jsonl` MUST start empty. Do not pre-populate with template entries to avoid false positives in self-tests.
7. If `ops/runbooks/commander_archivist_sprint1_runbook.md` already exists, DO NOT overwrite it. Read its constraints and obey them exactly.
## Phase Name

**AGENT SYSTEM V1 — SPRINT 1**

## Goal

Repository scaffolding + Commander/Archivist skeleton only.

## Strict Scope

- normalize folder structure
- normalize agent-system docs placement
- minimally update `CLAUDE.md`
- scaffold Commander only
- scaffold Archivist only
- define schema stubs
- define memory scaffolding
- define telemetry/audit scaffolding
- define minimal runbooks/prompts
- define local self-tests

## Out of Scope

- Outreach runtime
- Pilot Ops runtime
- Gmail send
- Telegram send
- Git push automation
- delivery automation
- Gate logic changes
- taxonomy/quarantine/schema mutation
- UE5 code changes
- vector DB / embeddings / RAG
- speculative runtime complexity

---

## Task 1 — Normalize Directory Structure

Ensure these directories exist:

```text
docs/agent_system/v1/
ops/agents/commander/
ops/agents/archivist/
ops/schemas/
ops/prompts/claude/
ops/runbooks/
memory/operator/
memory/session/
memory/tasks/
memory/artifacts/
memory/lineage/
memory/approvals/
memory/relationships/
memory/procedures/
telemetry/audits/
telemetry/workflows/
telemetry/dashboards/
```

Do not create Outreach or Pilot Ops implementation folders unless they are empty placeholders and clearly marked inactive.

---

## Task 2 — Normalize Documentation Placement

Ensure these files exist under `docs/agent_system/v1/`:

- `mnemosyne_agent_system_v1_index.md`
- `mnemosyne_agent_system_v1_executive_summary.md`
- `agent_architecture_v1.md`
- `agent_contracts_v1.md`
- `agent_workflows_v1.md`
- `agent_memory_model_v1.md`
- `agent_telemetry_and_eval_v1.md`
- `archivist_write_permissions_addendum_v1.md`

### Rules

- preserve content fidelity
- do not rewrite docs unnecessarily
- do not duplicate files if not needed
- if files already exist in the correct path, leave them in place

---

## Task 3 — Update `CLAUDE.md` Minimally

Do **not** bloat `CLAUDE.md`.

Only ensure `CLAUDE.md` clearly points to:

- `docs/agent_system/v1/` as source of truth
- the read order for agent-related work
- the Sprint 1 runtime boundary:
  - Commander + Archivist only
  - no Outreach runtime
  - no Pilot Ops runtime
  - no autonomous sending
- Sprint 1 schema path:
  - `ops/schemas/`
- Sprint 1 additional constraints:
  - schema-valid audit events, not stub logging
  - inactive capabilities explicitly marked inert

If this is already present and correct, do not duplicate it.

---

## Task 4 — Commander Skeleton

Create a minimal Commander skeleton under:

```text
ops/agents/commander/
```

### Required Files

- `README.md`
- `commander.py`
- `models.py`
- `self_test.py`

### Commander Responsibilities in Sprint 1

- intake operator intent
- create task envelopes
- route to Archivist only
- produce approval request stubs
- produce status summary stubs
- fail closed on invalid intent
- fail closed on missing approval state

### Commander Must Not

- send external email
- push to git
- delete files
- mutate protocol logic
- implement Outreach behavior
- implement Pilot Ops behavior

### Implementation Rules

- keep it simple
- deterministic, file-backed, local-first
- dataclass or pydantic-style models acceptable
- no external network dependency
- no framework lock-in
- no async complexity unless absolutely necessary

---

## Task 5 — Archivist Skeleton

Create a minimal Archivist skeleton under:

```text
ops/agents/archivist/
```

### Required Files

- `README.md`
- `archivist.py`
- `models.py`
- `self_test.py`

### Archivist Responsibilities in Sprint 1

- load and inspect artifact references
- validate that referenced files exist
- build a minimal evidence summary
- build a minimal lineage record
- refuse unsupported claims if no artifact refs exist
- emit claim validation outputs that include exact evidence, not just verdicts

### Archivist Must Not

- rewrite source code
- draft outreach
- send messages
- upgrade uncertain evidence to truth
- introduce embeddings/vector DB/RAG
- parse PDFs unless already trivially available as plain text inputs

### Implementation Rules

- keep it file-centric
- deterministic path validation first
- artifact summary only
- no overbuilt retrieval layer

---

## Task 6 — Shared Schemas and State Stubs

Create or normalize minimal schema files under:

```text
ops/schemas/
```

### Required Files

- `ops/schemas/task_envelope.schema.json`
- `ops/schemas/audit_event.schema.json`
- `ops/schemas/claim_validation.schema.json`
- `ops/schemas/package_readiness.schema.json`
- `ops/schemas/escalation.schema.json`

### Create Initial Memory/State Files

- `memory/operator/operator_profile_v1.json`
- `memory/session/active_session.json`
- `memory/tasks/.gitkeep`
- `memory/artifacts/.gitkeep`
- `memory/lineage/.gitkeep`
- `memory/approvals/.gitkeep`
- `memory/relationships/.gitkeep`
- `memory/procedures/.gitkeep`

### Rules

- use `docs/agent_system/v1/` contracts as reference
- do not invent new states unless absolutely necessary
- if a new field is unavoidable, explain it explicitly in output notes

---

## Task 7 — Audit and Telemetry Scaffolding

Create minimal telemetry scaffolding:

- `telemetry/audits/README.md`
- `telemetry/workflows/README.md`
- `telemetry/dashboards/README.md`
- `telemetry/audits/audit_log.jsonl`
- `telemetry/workflows/workflow_metrics_template.json`
- `telemetry/dashboards/weekly_summary_template.json`

### Important

“Audit scaffolding” does **not** mean stub logging.

From Run #1, every meaningful Commander and Archivist action must emit a valid JSON audit record conforming to the audit event contract.

This includes:

- task creation
- task rejection/blocking
- validation completion
- evidence summary creation
- lineage record creation
- escalation
- approval request stubs
- status summary generation

A print statement or informal log line does **not** count as audit coverage.

### Rules

- templates/stubs only for telemetry summaries
- no dashboards
- no UI
- no external services
- no fake completeness

---

## Task 8 — Runbooks and Prompts

Create:

- `ops/runbooks/commander_archivist_sprint1_runbook.md`
- `ops/prompts/claude/commander_intake_prompt.md`
- `ops/prompts/claude/archivist_evidence_prompt.md`

### Rules

- short
- operational
- not essay-like
- aligned with Sprint 1 only

---

## Task 9 — Inert Permissions

Any permission surface that is architecturally present but not active in Sprint 1 must be explicitly marked inert in code.

### Minimum Requirement

- Commander Gmail Draft capability must be flagged `INERT_UNTIL_OUTREACH_RUNTIME`

No inactive capability may be silently usable in Sprint 1.

---

## Task 10 — Self-Tests

Every code artifact must include a self-test that runs locally without external dependencies.

### Minimum Required Proof

- Commander can create a valid `collect_evidence` task envelope
- Commander blocks invalid or unknown intents
- Archivist validates existing file refs
- Archivist blocks missing artifact refs
- Commander and Archivist emit schema-valid audit events locally
- inactive capability surfaces are explicitly inert
- all self-tests run without network access

---

## Sprint 1 Exit Criteria

### ec1_repo_structure_ready
- required folder structure exists

### ec2_docs_placed
- agent system docs are in `docs/agent_system/v1/`

### ec3_claude_context_updated
- `CLAUDE.md` contains correct and minimal Agent System V1 references

### ec4_commander_skeleton_ready
- commander files exist and self-test passes

### ec5_archivist_skeleton_ready
- archivist files exist and self-test passes

### ec6_schema_stubs_ready
- required schema files exist under `ops/schemas/`

### ec7_memory_scaffolding_ready
- required memory paths/files exist

### ec8_scope_preserved
- no Outreach runtime
- no Pilot Ops runtime
- no send capability
- no Gate logic changes
- no speculative overengineering

### ec9_audit_contract_real
- Commander and Archivist emit schema-valid audit events for meaningful actions from Run #1
- stub prints/log lines do not satisfy this criterion

### ec10_inert_permissions_enforced
- architecturally present but inactive capability surfaces are explicitly marked inert
- Commander Gmail Draft is flagged `INERT_UNTIL_OUTREACH_RUNTIME`

---

## Output Rules

- Keep the sprint narrow.
- Prefer deterministic file-backed scaffolding over frameworks.
- Prefer readable code over clever code.
- Reuse existing files when correct.
- Fail closed on ambiguity.
- Report blockers explicitly.
- Do not claim runtime readiness beyond Commander + Archivist skeleton status.

## Required Final Output Format

# Sprint 1 Result

## 1. Exit Criteria Status

Report PASS / FAIL / PARTIAL for:

- ec1_repo_structure_ready
- ec2_docs_placed
- ec3_claude_context_updated
- ec4_commander_skeleton_ready
- ec5_archivist_skeleton_ready
- ec6_schema_stubs_ready
- ec7_memory_scaffolding_ready
- ec8_scope_preserved
- ec9_audit_contract_real
- ec10_inert_permissions_enforced

## 2. Files Created or Updated

List exact paths only.

## 3. Blockers

List only real blockers.

## 4. Scope Check

Explicitly confirm:

- no Outreach runtime
- no Pilot Ops runtime
- no sending
- no protocol-core mutation

## Commit Signature

```text
feat(agent-v1-sprint1): scaffold docs, repo layout, and commander+archivist skeleton
```