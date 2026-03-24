# Agent v1 Sprint 1 Fast Acceptance Prompt
**Status:** Active  
**Mode:** Review Only / Fast Pass

Read `CLAUDE.md` first.

## Review Mode

This is a **REVIEW-ONLY** pass.

- No implementation
- No rewrites unless a real blocker is found
- No scope widening

## Task

Audit the current Agent v1 Sprint 1 output quickly against Sprint 1 scope only.

## Check Only These

- repo structure
- docs placement under `docs/agent_system/v1/`
- minimal `CLAUDE.md` Agent System section
- Commander skeleton exists and is narrow
- Archivist skeleton exists and is narrow
- schema stubs exist under `ops/schemas/`
- memory scaffolding exists
- telemetry/audit stubs exist
- self-tests pass
- audit events are real schema-valid JSON, not stub logging
- inert permissions are enforced
- scope preserved:
  - no Outreach/Pilot Ops implementation
  - no send/push/delete capability
  - no protocol-core changes

---

## Output Format

Output **exactly**:

# Sprint 1 Fast Acceptance

## Verdict

- ACCEPT
- ACCEPT WITH FIXES
- REJECT

## Exit Criteria

For each, mark **PASS / FAIL / PARTIAL** with one short reason:

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

## Blockers

List only true blockers.

## Hidden Risk Check

State whether any of these exist:

- send capability
- push capability
- delete capability
- protocol mutation
- speculative overengineering
- fake audit coverage
- inactive capability surface not marked inert

## Next Action

Choose one:

- proceed to Sprint 2
- fix blockers first

## Final Line

Print this exact line at the end:

```text
Sprint 1 status: [ACCEPT / ACCEPT WITH FIXES / REJECT]
```