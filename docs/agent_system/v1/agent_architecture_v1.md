# Mnemosyne Agent Architecture v1
**Status:** Draft v1  
**Scope:** Internal operating layer for evidence, outreach, and pilot delivery  
**Parent System:** Mnemosyne Protocol  
**Owner:** Kerem Salman  
**Mode:** Fail-Closed / Human-in-the-Loop First

---

## 1. Purpose

Mnemosyne Agent Architecture v1 defines a **controlled internal agent layer** around the Mnemosyne Protocol.

This layer does **not** replace the core product.

The core product remains:

- Gate
- Passport
- Quarantine
- Evidence Pack
- Fail-Closed Admission Logic

The agent layer exists to accelerate:

- evidence retrieval
- pilot packaging
- outreach drafting
- approval workflows
- operator visibility
- artifact lineage

This architecture is intentionally narrow.

It is **not** an autonomous company.
It is a **controlled operating system for evidence, outreach, and pilot delivery**.

---

## 2. Core Principles

### 2.1 Fail-Closed by Default
No external-facing action proceeds unless explicitly allowed.

Default state:

- no-send
- no-delete
- no-push
- no-policy-edit
- no-claim-without-evidence

### 2.2 Human-in-the-Loop First
The system drafts, routes, verifies, and packages.
The human operator approves, rejects, escalates, or overrides.

### 2.3 Artifact-First Operation
Agents do not primarily exchange free-form opinions.
They exchange:

- task envelopes
- artifact references
- evidence summaries
- approval states
- audit records

### 2.4 Least Privilege
Each agent gets only the minimum tools and data required for its role.

### 2.5 Evidence Before Expression
No external claim should be produced unless it can be tied to a concrete artifact or validated repository state.

### 2.6 No Core Product Mutation
This agent layer does not autonomously modify:

- Gate logic
- taxonomy
- quarantine schema
- signing rules
- scene manifest contract
- UE5 executor contract

Those remain operator-controlled.

---

## 3. System Boundary

### 3.1 In Scope
- internal orchestration
- evidence retrieval
- artifact lineage
- outreach draft generation
- pilot package creation
- delivery readiness checks
- approval routing
- audit logging

### 3.2 Out of Scope
- autonomous email sending
- autonomous code merge/push
- autonomous GitHub release
- autonomous policy changes
- autonomous legal/compliance decisions
- RLHF/self-modifying Gate behavior
- broad multi-agent experimentation

---

## 4. Agent Set v1

Mnemosyne v1 uses **4 agents**:

1. **Commander Agent**
2. **Archivist Agent**
3. **Outreach Agent**
4. **Pilot Ops Agent**

This is the maximum allowed set for v1.

No fifth agent is introduced without explicit operator approval.

---

## 5. Agent Specifications

---

### 5.1 Commander Agent

#### Role
Primary orchestration and approval gateway.

#### Responsibilities
- receive operator intent
- classify the task
- route work to the correct agent
- collect intermediate outputs
- request operator approval through Telegram or equivalent channel
- summarize status
- stop unsafe or ambiguous execution

#### Allowed Actions
- task creation
- task routing
- draft review requests
- approval state transitions
- status summaries
- read-only artifact inspection

#### Forbidden Actions
- send external email
- publish posts
- push code
- delete artifacts
- mutate Gate/policy/taxonomy
- mark a package as sent

#### Inputs
- operator commands
- session state
- outputs from Archivist / Outreach / Pilot Ops

#### Outputs
- task envelopes
- approval requests
- consolidated summaries
- escalation notices

#### Fail-Closed Rule
If approval state is missing, invalid, or ambiguous:
- do not continue
- escalate to operator

---

### 5.2 Archivist Agent

#### Role
Evidence retrieval, artifact lineage, repository memory, and factual validation.

#### Responsibilities
- retrieve benchmark reports
- retrieve phase closure docs
- locate PASS/FAIL artifacts
- map commit -> report -> export package relationships
- validate which claims are supported
- answer “what proves this?” questions

#### Allowed Actions
- read repository files
- read docs
- read reports
- compute checksums
- build artifact indexes
- build lineage maps

#### Forbidden Actions
- rewrite source code
- generate outreach copy independently
- send external messages
- label unsupported claims as verified
- modify core protocol contracts

#### Inputs
- task requests from Commander
- repo contents
- evidence artifacts
- reports
- manifests
- passports
- benchmark outputs

#### Outputs
- evidence summaries
- artifact manifests
- lineage records
- claim support checks
- readiness notes

#### Fail-Closed Rule
If provenance is unclear or artifact source is not verifiable:
- mark as unverified
- do not promote to evidence

---

### 5.3 Outreach Agent

#### Role
Draft external-facing communication for studios, partners, and investors.

#### Responsibilities
- generate outreach drafts
- tailor message by audience
- suggest subject lines
- recommend which evidence package to attach
- maintain follow-up draft sequences

#### Allowed Actions
- create draft emails
- update draft emails
- create internal message variants
- suggest account-specific positioning

#### Forbidden Actions
- send email
- send LinkedIn message
- send Telegram/WhatsApp outreach
- publish posts
- make unsupported technical claims

#### Inputs
- audience profile
- evidence summary from Archivist
- operator tone preferences
- account status

#### Outputs
- outreach draft
- short follow-up sequence
- attachment recommendation
- audience-specific positioning note

#### Fail-Closed Rule
No draft becomes sendable unless:
- evidence is attached or linked
- operator approval is granted
- unsupported claims are removed

---

### 5.4 Pilot Ops Agent

#### Role
Prepare, validate, and package pilot/demo artifacts for delivery.

#### Responsibilities
- package PASS/FAIL scenarios
- create delivery-ready export structure
- generate README_PILOT
- generate export manifest
- generate checksums
- validate package completeness

#### Allowed Actions
- run packaging scripts
- create export directories
- copy approved artifacts
- generate checksums
- generate package metadata

#### Forbidden Actions
- modify Gate logic
- alter benchmark evidence
- alter taxonomy/schema
- mark package as delivered
- upload/send externally without approval

#### Inputs
- evidence list from Archivist
- operator packaging request
- package target profile

#### Outputs
- export package
- README_PILOT
- EXPORT_MANIFEST
- SHA256SUMS
- delivery-readiness report

#### Fail-Closed Rule
If any required artifact is missing or checksum generation fails:
- package status remains NOT READY
- export is blocked

---

## 6. Inter-Agent Communication Model

Agents communicate using **task envelopes**, not open-ended chat.

### 6.1 Task Envelope Schema

```json
{
  "task_id": "uuid",
  "from_agent": "commander",
  "to_agent": "archivist",
  "intent": "collect_evidence",
  "payload_ref": [
    "docs/faz9d4_report.md",
    "bench/out/faz9d4_report.json"
  ],
  "required_output": "evidence_summary_v1",
  "approval_state": "not_required",
  "timestamp_utc": "2026-03-22T00:00:00Z"
}
```

### 6.2 Communication Rules

- all cross-agent requests must have a `task_id`
- all outputs must identify their source artifacts
- free-form messages without task linkage are invalid
- missing `approval_state` means blocked by default

---

## 7. Memory Model v1

Mnemosyne v1 uses **6 memory classes**.

The authoritative memory model for v1 is:

1. **Operator Memory**
2. **Session Memory**
3. **Task Memory**
4. **Artifact Memory**
5. **Relationship Memory**
6. **Procedural Memory**

No other memory class exists in v1.

### 7.1 Operator Memory

Stable, operator-approved facts about KS that materially affect agent behavior.

Contains:
- operator identity
- approval authority
- communication preferences
- default tone preferences
- target account priorities
- fail-closed boundaries
- strategic constraints

Retention:
- persistent
- operator-controlled
- updated only by explicit operator instruction or explicit operator-confirmed preference

### 7.2 Session Memory

Short-lived operational state for the current working session.

Contains:
- active tasks
- pending approvals
- draft state
- current package target
- open issues
- unresolved escalations
- current phase state

Retention:
- short
- resettable
- operational only

### 7.3 Task Memory

Task-linked state and workflow continuity for specific units of work.

Contains:
- task envelopes
- task lineage
- task status transitions
- assigned agent
- required outputs
- retry/escalation state

Retention:
- medium-lived
- version-aware
- tied to task lifecycle

### 7.4 Artifact Memory

Long-lived store of produced evidence and lineage.

Contains:
- benchmark reports
- phase closure notes
- manifests
- passports
- export packages
- quarantine summaries
- report references

Retention:
- long-lived
- versioned
- auditable

### 7.5 Relationship Memory *(Stub in Sprint 1)*

Account-level operating context.

Contains:
- account name
- role
- priority
- last contact status
- preferred proof angle
- previous deck/package sent

Retention:
- persistent
- editable only with operator approval

Sprint 1 rule:
- schema/path scaffolding allowed
- no active write path required
- no silent inference of relationship state

### 7.6 Procedural Memory *(Stub in Sprint 1)*

Operational checklists and SOPs.

Contains:
- pilot packaging checklist
- send-approval checklist
- secret triage checklist
- artifact readiness checklist
- phase closure rules

Retention:
- version-controlled
- treated as operational contract

Sprint 1 rule:
- static references and runbooks allowed
- no live procedural memory runtime required
- no procedural write automation required

---

## 8. Tool Permissions Matrix

| Agent | Repo Read | Repo Write | Gmail Draft | Gmail Send | Telegram | Packaging Scripts | Git Push | Delete Artifacts |
|------|-----------|------------|-------------|------------|----------|-------------------|----------|------------------|
| Commander | Yes | No | Limited | No | Yes | No | No | No |
| Archivist | Yes | Limited metadata only | No | No | No | Optional read-only support | No | No |
| Outreach | Limited | No | Yes | No | No | No | No | No |
| Pilot Ops | Read package scope | Limited export/write | No | No | No | Yes | No | No |

### Global Rules

- no email send without explicit operator approval
- no git push without explicit operator approval
- no deletion by default
- no secret access unless specifically required and operator-approved

---

## 9. Approval State Machine

### States

- DRAFT
- READY_FOR_REVIEW
- APPROVED
- REJECTED
- BLOCKED
- ESCALATED
- DELIVERED (operator-confirmed only)

### Rules

- all external communication starts at `DRAFT`
- only Commander can request transition to `READY_FOR_REVIEW`
- only operator can move an item to `APPROVED`
- no agent may self-mark anything as `DELIVERED`
- ambiguous state transitions resolve to `BLOCKED`

---

## 10. Audit Logging

Every meaningful agent action writes an audit event.

### 10.1 Audit Event Schema

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

### 10.2 Audit Rules

- no silent execution
- all failures log reason
- all blocked actions log reason
- all external draft generation logs evidence source

---

## 11. Guardrails

### 11.1 Hard Guardrails

- no-send by default
- no-delete by default
- no-push by default
- no-policy-edit by default
- no unsupported claims
- no unlogged external draft generation

### 11.2 Claim Validation Rule

Any technical claim sent externally must have:
- source artifact(s)
- commit/report reference
- verification state from Archivist

### 11.3 Escalation Rule

Any ambiguity in:
- source artifact
- approval state
- contact identity
- package completeness
- tool output validity

must escalate to operator.

No improvisation.

---

## 12. Standard Workflows

### 12.1 Outreach Draft Workflow

1. Commander receives target request
2. Archivist gathers evidence
3. Outreach drafts message
4. Commander requests approval
5. operator approves/rejects
6. approved draft may be copied into send channel manually or via approved send path

### 12.2 Pilot Demo Packaging Workflow

1. Commander requests package
2. Archivist identifies correct artifacts
3. Pilot Ops builds package
4. Archivist validates package evidence coverage
5. Commander presents delivery-ready summary
6. operator approves delivery

### 12.3 Investor Evidence Workflow

1. Commander requests proof summary
2. Archivist retrieves phase evidence
3. Outreach drafts concise note
4. Commander routes for approval
5. operator decides send/no-send

---

## 13. Success Metrics

### 13.1 Commander

- routing accuracy
- approval latency
- escalation correctness

### 13.2 Archivist

- evidence retrieval precision
- unsupported claim prevention rate
- lineage completeness

### 13.3 Outreach

- draft acceptance rate
- operator edit rate
- unsupported-claim incidence

### 13.4 Pilot Ops

- package completeness rate
- checksum success rate
- delivery-readiness accuracy

### 13.5 Global

- operator override frequency
- blocked unsafe action count
- false-ready package count
- audit coverage ratio

---

## 14. Implementation Roadmap v1

### Phase A — Contracts First

Define:
- task envelope schema
- audit schema
- approval state machine
- memory categories

### Phase B — Commander + Archivist

Stand up the orchestration and evidence layers first.

### Phase C — Outreach Draft-Only

Allow draft generation only.  
No send capability.

### Phase D — Pilot Ops

Allow package creation and readiness validation.

### Phase E — Telemetry

Add audit dashboards and approval analytics.

---

## 15. Non-Goals for v1

The following are explicitly out of scope:

- autonomous outbound sales
- autonomous investor communication
- autonomous GitHub operations
- multi-DCC automation
- self-improving Gate logic
- RLHF-driven protocol mutation
- broad autonomous multi-agent research

---

## 16. Final Position

Mnemosyne Agent Architecture v1 is not a replacement for the Mnemosyne Protocol.

It is an internal, controlled agent layer that strengthens:

- evidence flow
- packaging discipline
- outreach quality
- approval control
- operational speed

Its job is not to make decisions on trust.

Its job is to ensure that trust remains explicit, reviewable, and fail-closed.

---

## 17. v1 Summary

### Agent Set

- Commander
- Archivist
- Outreach
- Pilot Ops

### Operating Mode

- fail-closed
- artifact-first
- HITL-first
- least privilege
- evidence before expression

### North Star

- accelerate Mnemosyne operations without weakening Mnemosyne discipline
