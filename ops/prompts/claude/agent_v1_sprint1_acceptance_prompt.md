# Agent v1 Sprint 1 Acceptance Prompt
**Status:** Active  
**Mode:** Review Only

Read `CLAUDE.md` first.

## Review Mode

This is a **REVIEW-ONLY** pass.

- Do not implement new features.
- Do not rewrite code unless you find a concrete acceptance blocker.
- Do not widen scope.

## Task

Audit the current Agent v1 Sprint 1 output against the agreed Sprint 1 scope and acceptance criteria.

## Source of Truth

- `docs/agent_system/v1/agent_architecture_v1.md`
- `docs/agent_system/v1/agent_contracts_v1.md`
- `docs/agent_system/v1/agent_workflows_v1.md`
- `docs/agent_system/v1/agent_memory_model_v1.md`
- `docs/agent_system/v1/agent_telemetry_and_eval_v1.md`
- `docs/agent_system/v1/archivist_write_permissions_addendum_v1.md`
- `CLAUDE.md`
- the Sprint 1 review checklist already prepared by KS

## Review Scope

Audit only the following:

- repo structure
- docs placement
- minimal `CLAUDE.md` integration
- Commander skeleton
- Archivist skeleton
- schema stubs under `ops/schemas/`
- memory scaffolding
- telemetry/audit scaffolding
- runbooks/prompts
- self-tests
- scope preservation
- git hygiene
- audit contract reality
- inert permissions enforcement

## Required Behavior

1. Inspect what exists now.
2. Compare it to Sprint 1 expectations only.
3. Fail closed on ambiguity.
4. Do not praise vaguely. Be specific.
5. Separate findings into:
   - PASS
   - FAIL
   - NEEDS FIX BEFORE ACCEPT
   - OUT OF SCOPE BUT PRESENT
6. Identify any hidden autonomy risk:
   - send capability
   - push capability
   - deletion capability
   - protocol mutation
   - speculative overengineering
7. Check whether Commander and Archivist are narrow, deterministic, and file-backed.
8. Check whether any invalid future-phase work was introduced.
9. Check whether audit events are real schema-valid JSON outputs from Run #1, not stub logs.
10. Check whether architecturally present but inactive capability surfaces are explicitly inert.

---

## Output Format

Produce **exactly** these sections:

# Sprint 1 Acceptance Audit

## 1. Verdict

Choose one:

- ACCEPT
- ACCEPT WITH FIXES
- REJECT

## 2. Exit Criteria Status

Evaluate each:

- `ec1_repo_structure_ready`
- `ec2_docs_placed`
- `ec3_claude_context_updated`
- `ec4_commander_skeleton_ready`
- `ec5_archivist_skeleton_ready`
- `ec6_schema_stubs_ready`
- `ec7_memory_scaffolding_ready`
- `ec8_scope_preserved`
- `ec9_audit_contract_real`
- `ec10_inert_permissions_enforced`

For each criterion, mark:

- PASS
- FAIL
- PARTIAL

And give **one concrete reason**.

## 3. Concrete Findings

Group findings into:

- PASS findings
- FAIL findings
- risky findings
- unnecessary additions

## 4. Required Fixes Before Acceptance

List only **blocking fixes**.

Be:
- explicit
- minimal

## 5. Non-Blocking Improvements

List only small cleanup suggestions.

- No redesign
- No scope expansion

## 6. Final Recommendation

State the exact next action:

- merge and continue to Sprint 2
- fix blockers first
- rollback specific files

---

## Important Constraints

- no new features
- no agent expansion beyond Commander + Archivist
- no Outreach implementation
- no Pilot Ops implementation
- no external sending
- no protocol-core changes

## Final Line

At the end, print this exact one-line summary:

```text
Sprint 1 status: [ACCEPT / ACCEPT WITH FIXES / REJECT]
```