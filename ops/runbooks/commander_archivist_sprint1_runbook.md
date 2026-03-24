# Commander + Archivist — Sprint 1 Runbook
**Status:** Active
**Scope:** Sprint 1 runtime (Commander + Archivist only)
**Mode:** Fail-Closed / HITL

Sprint 1 audit requirement: Commander and Archivist audit events must conform
to the full `agent_contracts_v1.md §8` schema from the first test run.
Partial or stub audit logging does not satisfy Sprint 1 audit coverage.

Gmail Draft capability is architecturally present but remains
`INERT_UNTIL_OUTREACH_RUNTIME` in Sprint 1.

---

## Running Self-Tests

```bash
cd /Volumes/MNEMOSYNE-GATE/Vault/repos/Mnemosyne-Core
python -m ops.agents.commander.self_test
python -m ops.agents.archivist.self_test
```

Both test suites must pass (0 failures) before claiming Sprint 1 readiness.

---

## Commander: Standard Intake Flow

1. Operator provides intent + artifact refs.
2. Commander validates intent against Sprint 1 scope.
3. If valid: task envelope created, persisted to `memory/tasks/`, audit event written.
4. If invalid: blocked result returned, audit event written. No side effects.
5. Commander routes task to Archivist (Sprint 1: only archivist).
6. Archivist returns evidence summary or escalation.
7. Commander produces approval stub if operator review is needed.

## Archivist: Evidence Flow

1. Archivist receives task envelope from Commander.
2. Validates each `payload_ref` path against disk.
3. Builds evidence summary (all found), or escalates (any missing).
4. For claim validation: requires `artifact_ref` + `evidence_excerpt` + `lineage_ref` for `supported`.
5. All actions write audit events to `telemetry/audits/audit_log.jsonl`.

---

## Hard Rules (Non-Negotiable)

- No email send by any agent.
- No git push by any agent.
- No file deletion by any agent.
- No Gate / taxonomy / schema mutation.
- No unsupported claim in external-facing output.
- No delivery state without operator confirmation.
- Fail closed on ambiguity.

---

## Active vs Inert Capabilities

| Capability | State |
|-----------|-------|
| Commander → Archivist routing | ACTIVE |
| Gmail Draft | `INERT_UNTIL_OUTREACH_RUNTIME` |
| Commander → Outreach routing | Not active in Sprint 1 |
| Commander → Pilot Ops routing | Not active in Sprint 1 |
| Telegram approval path | Deferred (not yet reliable) |
| Autonomous email send | NEVER without ONAY |

---

## Audit Log Location

```
telemetry/audits/audit_log.jsonl
```

Each line = one schema-valid JSON audit event per `ops/schemas/audit_event.schema.json`.
