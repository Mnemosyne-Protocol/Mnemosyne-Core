# Mnemosyne Agent Contracts v1
**Status:** Draft v1  
**Scope:** Contract layer for the Mnemosyne internal 4-agent system  
**Parent Spec:** `agent_architecture_v1.md`  
**Mode:** Fail-Closed / Human-in-the-Loop First

---

## 1. Purpose

This document defines the formal contracts for the Mnemosyne internal agent layer.

It standardizes:

- task envelopes
- audit events
- approval states
- memory classes
- tool permissions
- guardrails
- escalation behavior

This is a **contract document**, not a workflow document.

Workflows belong in:

- `agent_workflows_v1.md`

Architecture principles belong in:

- `agent_architecture_v1.md`

---

## 2. Agent Registry

The v1 agent set is fixed.

### 2.1 Allowed Agents

| Agent ID | Role |
|---------|------|
| `commander` | orchestration and approval gateway |
| `archivist` | evidence retrieval, artifact lineage, factual validation |
| `outreach` | draft creation for external communication |
| `pilot_ops` | package preparation, checksum/manifest, delivery readiness |

### 2.2 Forbidden in v1

No other agent IDs are valid in v1.

Examples of invalid IDs:
- `seller`
- `closer`
- `compliance`
- `researcher`
- `strategist`

Adding any new agent requires a version bump.

---

## 3. Global Contract Rules

1. **No-send by default**
2. **No-delete by default**
3. **No-push by default**
4. **No-policy-edit by default**
5. **No unsupported external claim**
6. **No silent execution**
7. **Ambiguity resolves to BLOCKED or ESCALATED**
8. **All meaningful actions write audit events**
9. **All external-facing outputs require evidence linkage**
10. **Artifacts outrank free-form summaries**

---

## 4. Task Envelope Contract

Agents communicate through task envelopes.

A task envelope is the minimum valid unit of work between agents.

### 4.1 Required Fields

```json
{
  "task_id": "uuid",
  "from_agent": "commander",
  "to_agent": "archivist",
  "intent": "collect_evidence",
  "payload_ref": [],
  "required_output": "evidence_summary_v1",
  "approval_state": "not_required",
  "priority": "normal",
  "timestamp_utc": "2026-03-22T00:00:00Z"
}
```

### 4.2 Field Definitions

| Field | Type | Required | Notes |
|------|------|----------|------|
| `task_id` | string | yes | UUID or equivalent unique ID |
| `from_agent` | string | yes | must be one of the allowed agent IDs |
| `to_agent` | string | yes | must be one of the allowed agent IDs |
| `intent` | string | yes | machine-readable task purpose |
| `payload_ref` | array[string] | yes | artifact paths, IDs, or references |
| `required_output` | string | yes | expected output type |
| `approval_state` | string | yes | one of the valid approval states |
| `priority` | string | yes | `low`, `normal`, `high`, `urgent` |
| `timestamp_utc` | string | yes | ISO-8601 UTC timestamp |

### 4.3 Optional Fields

```json
{
  "operator_context": {
    "account": "Epic Games",
    "objective": "pilot_demo_followup"
  },
  "constraints": [
    "no_send",
    "evidence_required"
  ],
  "deadline_utc": "2026-03-23T12:00:00Z",
  "notes": "Use only proven Phase 9 artifacts"
}
```

### 4.4 Validation Rules

A task envelope is invalid if:
- `task_id` is missing
- `from_agent` or `to_agent` is not in the agent registry
- `intent` is empty
- `required_output` is empty
- `approval_state` is invalid
- `timestamp_utc` is missing or malformed

Invalid envelopes must be rejected.

---

## 5. Intent Registry v1

Only the following intents are valid in v1.

### 5.1 Core Intents

| Intent | Sender | Receiver | Purpose |
|-------|--------|----------|---------|
| `collect_evidence` | `commander` | `archivist` | gather supporting artifacts |
| `validate_claims` | `commander` | `archivist` | check whether a claim is supported |
| `draft_outreach` | `commander` | `outreach` | generate external draft |
| `prepare_package` | `commander` | `pilot_ops` | create package export |
| `validate_package` | `commander` | `archivist` | verify package completeness |
| `request_approval` | `commander` | `commander` | generate operator approval checkpoint |
| `summarize_status` | `commander` | `commander` | produce status summary |
| `collect_delivery_readiness` | `commander` | `pilot_ops` | package readiness check |
| `collect_lineage` | `commander` | `archivist` | map artifact lineage |
| `redraft_message` | `commander` | `outreach` | update or refine draft |

### 5.2 Invalid Intent Behavior

Unknown intents:
- must not be executed
- must be logged
- must be escalated to operator

---

## 6. Output Type Registry v1

### 6.1 Valid Output Types

| Output Type | Producer |
|------------|----------|
| `evidence_summary_v1` | `archivist` |
| `claim_validation_v1` | `archivist` |
| `artifact_lineage_v1` | `archivist` |
| `outreach_draft_v1` | `outreach` |
| `followup_draft_v1` | `outreach` |
| `package_export_v1` | `pilot_ops` |
| `package_readiness_v1` | `pilot_ops` |
| `approval_request_v1` | `commander` |
| `status_summary_v1` | `commander` |

Outputs outside this registry are invalid in v1.

---

## 7. Approval State Machine

Approval is a first-class contract.

### 7.1 Valid States

| State | Meaning |
|------|---------|
| `not_required` | no operator approval needed for this internal step |
| `draft` | work exists but is not ready for review |
| `ready_for_review` | waiting for operator review |
| `approved` | explicitly approved by operator |
| `rejected` | explicitly rejected by operator |
| `blocked` | cannot continue due to rule or missing prerequisite |
| `escalated` | ambiguous or unsafe; operator decision required |
| `delivered` | externally sent/used, operator-confirmed only |

### 7.2 Transition Rules

Allowed transitions:
- `draft -> ready_for_review`
- `ready_for_review -> approved`
- `ready_for_review -> rejected`
- `draft -> blocked`
- `draft -> escalated`
- `ready_for_review -> escalated`
- `approved -> delivered` **only by operator-confirmed action**
- `blocked -> ready_for_review` **only after blocker resolution**
- `escalated -> ready_for_review` **only after operator instruction**

### 7.3 Invalid Transitions

Examples:
- `draft -> delivered`
- `draft -> approved` without review
- `approved -> sent` (not a valid state)
- `blocked -> delivered`

Invalid transitions must fail closed.

### 7.4 Delivery Transition Ownership

The transition from `approved` to `delivered` is owned by `commander`.

This transition is valid only if all of the following are true:

1. the object was previously in `approved`
2. operator delivery confirmation exists
3. the delivered object/version is explicitly identified
4. a delivery audit event is written

### 7.5 Operator Delivery Confirmation Rule

`approved` does not mean `sent`.

A record may move to `delivered` only when the operator has explicitly confirmed delivery.

Minimum confirmation conditions:

- the target account is known
- the delivered object is version-specific
- the delivery channel is known
- the delivery timestamp is recorded

### 7.6 Minimum Delivery Audit Event

At minimum, a valid delivery transition must produce an audit record containing:

- `event_id`
- `timestamp_utc`
- `agent = commander`
- `action = delivered`
- `task_id`
- `object_ref`
- `target_account`
- `approval_state = delivered`
- `status = success`

### 7.7 Fail-Closed Delivery Rule

If operator confirmation is missing, ambiguous, stale, or not tied to the exact object/version, the transition must remain blocked.

No agent may infer delivery from:
- elapsed time
- lack of objection
- prior approval of a different version
- presence of a draft in a send-capable system

---

## 8. Audit Event Contract

Every meaningful action must generate an audit event.

### 8.1 Required Schema

```json
{
  "event_id": "uuid",
  "timestamp_utc": "2026-03-22T00:00:00Z",
  "agent": "pilot_ops",
  "action": "package_created",
  "task_id": "uuid",
  "inputs": [
    "bench/out/faz9d3_pass_run.json",
    "bench/out/faz9d3_fail_run.json"
  ],
  "outputs": [
    "exports/pilot_demo_v1/README_PILOT.md",
    "exports/pilot_demo_v1/03_METADATA/EXPORT_MANIFEST.json"
  ],
  "approval_state": "not_required",
  "status": "success"
}
```

### 8.2 Required Fields

| Field | Type | Required |
|------|------|----------|
| `event_id` | string | yes |
| `timestamp_utc` | string | yes |
| `agent` | string | yes |
| `action` | string | yes |
| `task_id` | string | yes |
| `inputs` | array[string] | yes |
| `outputs` | array[string] | yes |
| `approval_state` | string | yes |
| `status` | string | yes |

### 8.3 Optional Fields

```json
{
  "notes": "Package blocked: missing SHA256SUMS.txt",
  "error_code": "missing_checksum_file",
  "operator_ref": "telegram_msg_12345"
}
```

### 8.4 Valid Status Values

- `success`
- `failure`
- `blocked`
- `escalated`
- `rejected`

---

## 9. Memory Contracts

Memory is divided into **6 classes** in v1.

The authoritative v1 memory classes are:

1. **Operator Memory**
2. **Session Memory**
3. **Task Memory**
4. **Artifact Memory**
5. **Relationship Memory**
6. **Procedural Memory**

No other memory class exists in v1.

### 9.1 Operator Memory

Stable, operator-approved facts that materially affect agent behavior.

Examples:
- operator identity
- approval authority
- communication preferences
- default tone preferences
- target account priorities
- fail-closed boundaries
- strategic constraints

Rules:
- must be explicitly operator-approved
- must not be inferred from weak signals
- must not be silently overwritten by session state
- changes require explicit operator instruction or explicit operator-confirmed preference

### 9.2 Session Memory

Short-lived operational state for the current working session.

Examples:
- active task IDs
- pending review items
- current draft status
- current package request
- unresolved blockers
- unresolved escalations
- current phase state

Rules:
- write owner is strictly `commander`
- may be overwritten by newer session state
- must not be treated as durable evidence
- must not replace artifact lineage

### 9.3 Task Memory

Task-linked workflow continuity for specific units of work.

Examples:
- task envelopes
- task lineage
- task status transitions
- assigned agent
- required outputs
- retry state
- escalation state

Rules:
- must remain tied to specific task IDs
- must be version-aware where applicable
- must not be used as a substitute for approval state
- must preserve workflow traceability

### 9.4 Artifact Memory

Long-lived evidence memory.

Examples:
- benchmark reports
- phase closure notes
- export manifests
- passports
- quarantine evidence
- packaging reports

Rules:
- must reference real file paths or object IDs
- must be version-aware
- must support lineage tracing

### 9.5 Relationship Memory *(Stub in Sprint 1)*

Account-level operating memory.

Examples:
- `Epic Games -> technical evaluation package sent`
- `Riot -> prefers concise technical framing`
- `Investor X -> asked for moat vs workflow differentiation`

Rules:
- must not contain unsupported personal assumptions
- must not invent relationship state
- changes require operator confirmation when high-impact
- Sprint 1 allows scaffolding only; no active write path required

### 9.6 Procedural Memory *(Stub in Sprint 1)*

Operational SOP memory.

Examples:
- pilot package checklist
- send approval checklist
- phase closure checklist
- secret triage SOP
- evidence validation SOP

Rules:
- procedural memory is version-controlled
- informal notes do not override formal SOPs
- Sprint 1 allows static references and scaffolding only; no live procedural runtime required

---

## 10. Tool Permission Contract

### 10.1 Commander

| Tool Class | Permission |
|-----------|------------|
| repo read | allow |
| repo write | deny |
| Gmail draft | limited allow |
| Gmail send | deny |
| Telegram notify | allow |
| packaging scripts | deny |
| git push | deny |
| delete files | deny |

### 10.2 Archivist

| Tool Class | Permission |
|-----------|------------|
| repo read | allow |
| docs read | allow |
| evidence parse | allow |
| package validation | allow |
| repo write | limited metadata only |
| Gmail draft | deny |
| Gmail send | deny |
| git push | deny |
| delete files | deny |

### 10.3 Outreach

| Tool Class | Permission |
|-----------|------------|
| repo read | limited |
| evidence references | allow |
| Gmail draft | allow |
| Gmail send | deny |
| Telegram send | deny |
| package generation | deny |
| git push | deny |
| delete files | deny |

### 10.4 Pilot Ops

| Tool Class | Permission |
|-----------|------------|
| package scripts | allow |
| export directory write | allow |
| checksum generation | allow |
| repo read | allow |
| repo code write | deny |
| Gmail send | deny |
| git push | deny |
| delete files | deny |

---

## 11. Claim Validation Contract

No external-facing claim may be treated as valid unless it passes claim validation.

### 11.1 Minimal Claim Validation Record

```json
{
  "claim_id": "uuid",
  "claim_text": "Mnemosyne runs inside a live Unreal Editor workflow and enforces fail-closed certification.",
  "supporting_artifacts": [
    "docs/faz9d4_report.md",
    "bench/out/faz9d4_report.json"
  ],
  "validation_state": "supported",
  "validated_by": "archivist",
  "timestamp_utc": "2026-03-22T00:00:00Z"
}
```

### 11.2 Validation States

- `supported`
- `partially_supported`
- `unsupported`
- `unclear`
- `blocked`

### 11.3 Rule

Only claims in `supported` or explicitly operator-approved `partially_supported` state may appear in external-facing drafts.

---

## 12. Packaging Readiness Contract

A package may be marked ready only if all required files and metadata are present.

### 12.1 Minimal Readiness Schema

```json
{
  "package_id": "pilot_demo_v1",
  "required_files_present": true,
  "checksums_present": true,
  "manifest_present": true,
  "readme_present": true,
  "evidence_complete": true,
  "ready_state": "ready_for_review"
}
```

### 12.2 Fail-Closed Rule

Missing any of the following keeps package status blocked:
- README
- export manifest
- checksums
- required PASS evidence
- required FAIL evidence

No package is marked ready by inference.

---

## 13. Escalation Contract

Escalation is mandatory in the following situations:
- unknown intent
- invalid approval state
- missing evidence for external claim
- missing package artifact
- ambiguous contact identity
- conflicting artifact lineage
- invalid audit event
- tool output contradicts artifact record

### 13.1 Escalation Record

```json
{
  "escalation_id": "uuid",
  "task_id": "uuid",
  "agent": "archivist",
  "reason": "artifact_lineage_unclear",
  "details": "PASS report references a package not present in export directory",
  "timestamp_utc": "2026-03-22T00:00:00Z",
  "status": "open"
}
```

---

## 14. Hard Guardrails

These are non-bypassable in v1 unless operator explicitly changes the contract.

1. No email send by any agent
2. No Git push by any agent
3. No file deletion by any agent
4. No Gate or taxonomy mutation by any agent
5. No unsupported claim in external-facing output
6. No package marked ready without readiness contract
7. No delivery state without operator confirmation
8. No hidden retries on blocked actions
9. No silent downgrade from blocked to draft

---

## 15. File Naming Conventions

Suggested contract artifact names:
- `task_envelopes/*.json`
- `audit_logs/*.jsonl`
- `claim_validations/*.json`
- `package_readiness/*.json`
- `escalations/*.json`
- `memory/operator/*.json`
- `memory/session/*.json`
- `memory/tasks/*.json`
- `memory/artifacts/*.json`
- `memory/relationships/*.json`
- `memory/procedures/*.json`

This naming convention is recommended but not mandatory in v1.

---

## 16. Versioning Rules

### 16.1 Contract Version

This document is `v1`.

### 16.2 Backward Compatibility

Any change to:
- agent registry
- task envelope required fields
- approval states
- audit required fields
- hard guardrails

requires a version bump.

### 16.3 Patch-Level Changes

Small clarifications that do not alter behavior may be added without major version change.

---

## 17. Compliance Check for v1

A valid v1 implementation must satisfy all of the following:
- 4-agent registry only
- task envelope validation present
- approval state machine enforced
- audit event generation enforced
- tool permissions defined and respected
- 6-class memory contract aligned
- claim validation required for external-facing statements
- package readiness fail-closed
- escalation path implemented

---

## 18. Final Position

Mnemosyne Agent Contracts v1 exists to prevent ambiguity.

It defines:
- who may do what
- what must be logged
- what must be approved
- what counts as evidence
- what remains blocked by default

The goal is not autonomy for its own sake.

The goal is to preserve Mnemosyne discipline while increasing operational speed.

**Trust must remain explicit, reviewable, and fail-closed.**