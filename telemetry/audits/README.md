# Telemetry — Audits
**Status:** Active (Sprint 1)
**Mode:** Append-only JSONL

All Commander and Archivist actions write schema-valid audit events to `audit_log.jsonl`.

## Schema

Each line is a JSON object conforming to `ops/schemas/audit_event.schema.json`.

Required fields: `event_id`, `timestamp_utc`, `agent`, `action`, `task_id`,
`inputs`, `outputs`, `approval_state`, `status`.

## Audit Coverage Rule

Stub log lines do not satisfy audit coverage.
Every meaningful action must produce a full schema-valid event from Run #1.

Covered actions include:
- task creation
- task rejection/blocking
- validation completion
- evidence summary creation
- lineage record creation
- escalation
- approval request stubs
- status summary generation
