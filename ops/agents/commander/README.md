# Commander Agent — Sprint 1
**Status:** Active
**Scope:** Sprint 1 (Commander + Archivist only)
**Mode:** Fail-Closed / HITL-First
**Source of truth:** `docs/agent_system/v1/agent_contracts_v1.md`

---

## Role

Orchestration and approval gateway.

## Sprint 1 Responsibilities

- Intake operator intent
- Create and validate task envelopes
- Route to Archivist only
- Produce approval request stubs (no send)
- Produce status summary stubs
- Emit schema-valid audit events for every meaningful action
- Fail closed on invalid intent or missing approval state

## Must Not

- Send external email → `INERT_UNTIL_OUTREACH_RUNTIME`
- Push to git
- Delete files
- Route to `outreach` or `pilot_ops` (not active in Sprint 1)
- Mutate Gate, taxonomy, or policy

## Files

| File | Purpose |
|------|---------|
| `commander.py` | Commander implementation |
| `models.py` | TaskEnvelope, AuditEvent, registry constants |
| `self_test.py` | Self-contained test suite (no network required) |

## Running Self-Tests

```bash
cd /Volumes/MNEMOSYNE-GATE/Vault/repos/Mnemosyne-Core
python -m ops.agents.commander.self_test
```

## Inert Capabilities

| Capability | State |
|-----------|-------|
| Gmail Draft | `INERT_UNTIL_OUTREACH_RUNTIME` |
| Outreach routing | Not active until Sprint 2 |
| Pilot Ops routing | Not active until Sprint 2 |
