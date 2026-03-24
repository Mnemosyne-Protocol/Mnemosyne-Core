# Mnemosyne Agent Memory Model v1
**Status:** Draft v1  
**Scope:** Memory, state, lineage, and approval history for the Mnemosyne internal agent system  
**Parent Specs:**  
- `agent_architecture_v1.md`
- `agent_contracts_v1.md`
- `agent_workflows_v1.md`  
**Primary Operator:** Kerem Salman (KS)  
**Mode:** Fail-Closed / Artifact-First / Human-in-the-Loop First

---

## 1. Purpose

This document defines how memory is represented, stored, validated, and used inside the Mnemosyne internal 4-agent system.

It standardizes:

- memory classes
- operator state
- task state
- artifact lineage
- approval history
- relationship memory
- procedural memory
- memory write rules
- memory read rules
- retention and invalidation logic

The goal is simple:

**increase continuity without weakening discipline**

Mnemosyne memory is not meant to create illusionary intelligence.  
It is meant to create:

- continuity
- traceability
- auditability
- operational speed
- explicit trust boundaries

---

## 2. Core Position

Memory in Mnemosyne is **not** “whatever the agent remembers.”

Memory is a controlled system of recorded facts, validated artifacts, operator-approved state, and procedural references.

The model is designed around 4 requirements:

1. **Artifact truth outranks agent summary**
2. **Operator-approved state outranks inferred state**
3. **Lineage outranks convenience**
4. **Ambiguity resolves to unknown, not assumed**

---

## 3. Memory Design Principles

### 3.1 Fail-Closed Memory

If a memory entry is incomplete, stale, ambiguous, or unsupported:
- do not upgrade it to truth
- mark it as uncertain, stale, or blocked

### 3.2 State is Not Evidence

A remembered status such as “Epic package ready” is not evidence.  
The underlying package manifest, checksum file, and validation result are evidence.

### 3.3 Memory Must Be Inspectable

No memory entry should exist only inside an agent’s hidden reasoning.  
All important memory must be serializable and reviewable.

### 3.4 Explicit Provenance

Every durable memory item should answer:
- who created it
- when it was created
- what artifacts support it
- whether KS approved it
- what supersedes it

### 3.5 Memory Should Reduce Rework

The model exists to prevent repeated rediscovery of:
- what Phase 9 proved
- what Riot needs
- what Epic has seen
- what package version was sent
- what claims are safe to repeat

---

## 4. Memory Classes

Mnemosyne v1 uses 6 memory classes.

1. **Operator Memory**
2. **Session Memory**
3. **Task Memory**
4. **Artifact Memory**
5. **Relationship Memory**
6. **Procedural Memory**

No other memory class exists in v1.

---

## 5. Operator Memory

### 5.1 Definition

Operator Memory stores stable, operator-approved facts about KS that materially affect agent behavior.

This is not a biography.  
It is an operating profile.

### 5.2 Includes

- preferred name / operator identity
- approval authority
- communication preferences
- default tone preferences
- target account priorities
- fail-closed boundaries
- strategic constraints

### 5.3 Does Not Include

- emotional inference
- speculative preferences
- transient mood
- unconfirmed assumptions
- medical/personal sensitive data unless explicitly needed and approved

### 5.4 Example

```json
{
  "operator_id": "ks",
  "display_name": "Kerem Salman",
  "approval_authority": true,
  "default_mode": "fail_closed",
  "external_send_requires_onay": true,
  "preferred_outreach_tone": "precise_confident_non_hyped",
  "priority_accounts": [
    "Epic Games",
    "Riot Games",
    "investor_tier_1"
  ],
  "updated_at_utc": "2026-03-22T00:00:00Z"
}
```

### 5.5 Write Rule

Operator Memory may only be written or updated by:
- explicit operator instruction
- explicit operator-confirmed preference

### 5.6 Read Rule

All agents may read relevant operator memory.  
No agent may silently reinterpret it.

---

## 6. Session Memory

### 6.1 Definition

Session Memory stores short-lived state for the current working session.

It answers:
- what is active right now
- what is waiting for review
- what is blocked
- what was the last output in this session

### 6.2 Includes

- active workflow IDs
- current package target
- draft currently under review
- unresolved escalations
- last known working path
- current phase state

### 6.3 Example

```json
{
  "session_id": "sess_2026_03_22_01",
  "active_phase": "faz10",
  "active_workflows": [
    "pilot_package_epic_v1"
  ],
  "pending_approvals": [
    "draft_epic_intro_v2"
  ],
  "blocked_items": [],
  "last_artifact_ref": "exports/pilot_demo_v1/README_PILOT.md",
  "updated_at_utc": "2026-03-22T00:00:00Z"
}
```

### 6.4 Write Rule

In v1, Session Memory writes are owned by `commander`.

Other agents may influence Session Memory only indirectly through valid task outputs that `commander` accepts and records.

There is no independent system-level writer in v1.

### Session Memory Ownership
- **Write Owner:** STRICTLY `commander`.
- No separate runtime process or orchestration script is permitted to write to Session Memory.
- Commander acts as the sole orchestrator for Session Memory in v1.
- Every write to Session Memory MUST produce a complete, traceable audit event conforming to §8.

### 6.5 Write Sources Allowed in v1

`commander` may update Session Memory only from:

- valid task state transitions
- explicit operator instruction
- accepted agent outputs
- explicit escalation outcomes
- explicit approval outcomes

### 6.6 Write Sources Forbidden in v1

Session Memory must not be updated from:

- hidden internal reasoning
- ambiguous workflow assumptions
- speculative status inference
- unverified artifact existence
- passive elapsed time
- “system transition” language without a concrete owner

### 6.7 Read Rule

All agents may read Session Memory when relevant to active work.

Read access does not grant write authority.

### 6.8 Retention Rule

Session Memory is ephemeral.

It may be:
- reset after workflow completion
- archived after phase closure
- superseded by newer session state

But it must never replace durable Artifact Memory, Task Memory, or Approval History.

---

## 7. Task Memory

### 7.1 Definition

Task Memory stores durable state about a specific unit of work.

It answers:
- what was requested
- who handled it
- what was produced
- what state it ended in

### 7.2 Includes

- task envelope
- task state transitions
- assigned agent
- produced outputs
- approval status
- escalation events
- final disposition

### 7.3 Example

```json
{
  "task_id": "task_pkg_epic_001",
  "intent": "prepare_package",
  "from_agent": "commander",
  "to_agent": "pilot_ops",
  "state": "ready_for_review",
  "outputs": [
    "exports/pilot_demo_v1/03_METADATA/EXPORT_MANIFEST.json"
  ],
  "approval_state": "ready_for_review",
  "escalations": [],
  "updated_at_utc": "2026-03-22T00:00:00Z"
}
```

### 7.4 Write Rule

Task Memory is system-generated through task execution.

### 7.5 Read Rule

All agents may read task memory relevant to their assigned work.

### 7.6 Retention Rule

Task Memory is durable and auditable.

---

## 8. Artifact Memory

### 8.1 Definition

Artifact Memory stores durable references to evidence-bearing outputs.

This is the most important memory class in Mnemosyne.

It answers:
- what exists
- what it proves
- where it came from
- what version it belongs to
- what superseded it

### 8.2 Includes

- benchmark reports
- phase closure notes
- PASS/FAIL run outputs
- passports
- manifests
- README files
- package exports
- checksum files
- lineage notes

### 8.3 Example

```json
{
  "artifact_id": "faz9d4_report_v1",
  "artifact_type": "phase_report",
  "path": "docs/faz9d4_report.md",
  "source_phase": "faz9d4",
  "validation_state": "verified",
  "claims_supported": [
    "delegate binding verified in live UE5 editor",
    "pass passport produced",
    "fail-closed behavior verified"
  ],
  "superseded_by": null,
  "created_at_utc": "2026-03-22T00:00:00Z"
}
```

### 8.4 Write Rule

Artifact Memory may only reference:
- real files
- real reports
- real manifests
- real outputs

No imaginary artifact records.

### 8.5 Read Rule

All agents may read Artifact Memory.  
Archivist is the primary steward.

### 8.6 Retention Rule

Artifact Memory is long-lived.  
It should not be dropped casually.

---

## 9. Relationship Memory

### 9.1 Definition

Relationship Memory stores account-specific operating state.

It answers:
- who the target is
- what has already been sent
- what angle matters to them
- what stage the relationship is in

### 9.2 Includes

- account name
- contact role
- last meaningful interaction
- package sent
- deck sent
- preferred framing
- current status
- next recommended step

### 9.3 Example

```json
{
  "account_id": "epic_games",
  "display_name": "Epic Games",
  "segment": "platform_partner",
  "last_touch": "pilot_demo_package_prepared",
  "assets_seen": [
    "pilot_demo_v1"
  ],
  "preferred_proof_angle": "real_ue5_live_editor_gate_path",
  "status": "no_send_yet",
  "next_step": "operator_review_outreach_draft",
  "updated_at_utc": "2026-03-22T00:00:00Z"
}
```

### 9.4 Write Rule

Relationship Memory may be updated only when:
- a real interaction occurred
- operator confirmed a change
- a real delivery happened
- a real reply was received

### 9.5 Read Rule

Commander and Outreach may read it freely.  
Archivist may reference it when assembling account-specific evidence.

### 9.6 Retention Rule

Persistent.  
Never infer contact history from guesswork.

---

## 10. Procedural Memory

### 10.1 Definition

Procedural Memory stores SOPs, checklists, and repeatable operational methods.

It answers:
- how do we run this safely
- what is required before send
- what closes a phase
- what blocks delivery

### 10.2 Includes

- pilot packaging SOP
- send approval checklist
- phase closure checklist
- secret leak triage checklist
- UE verification checklist
- delivery readiness checklist

### 10.3 Example

```json
{
  "procedure_id": "pilot_delivery_checklist_v1",
  "type": "checklist",
  "source_doc": "agent_workflows_v1.md",
  "summary": "Minimum checks before package can be marked ready for review",
  "current_version": "v1",
  "updated_at_utc": "2026-03-22T00:00:00Z"
}
```

### 10.4 Write Rule

Procedural Memory must be version-controlled.  
Ad hoc chat instructions do not override formal procedures unless explicitly promoted.

### 10.5 Read Rule

All agents may use procedural memory when applicable.

### 10.6 Retention Rule

Long-lived.  
Old procedures may be superseded, not silently overwritten.

---

## 11. State Model

Mnemosyne memory also carries cross-cutting state objects.

These are not separate memory classes, but required state dimensions.

### 11.1 Approval State

Tracks whether the operator approved an action or artifact.

Valid values:
- `not_required`
- `draft`
- `ready_for_review`
- `approved`
- `rejected`
- `blocked`
- `escalated`
- `delivered`

### 11.2 Validation State

Tracks whether a claim, artifact, or package has been validated.

Valid values:
- `verified`
- `partially_verified`
- `unverified`
- `unsupported`
- `blocked`

### 11.3 Freshness State

Tracks whether the memory is still current enough to use.

Valid values:
- `current`
- `stale`
- `superseded`
- `archived`

### 11.4 Trust State

Tracks whether the memory item is safe to act upon.

Valid values:
- `trusted`
- `limited_trust`
- `operator_only`
- `blocked`

---

## 12. Memory Record Contract

All durable memory records should follow a common contract.

### 12.1 Required Fields

```json
{
  "memory_id": "uuid",
  "memory_class": "artifact_memory",
  "title": "FAZ 9D.4 live verification report",
  "state": {
    "approval_state": "not_required",
    "validation_state": "verified",
    "freshness_state": "current",
    "trust_state": "trusted"
  },
  "created_at_utc": "2026-03-22T00:00:00Z",
  "updated_at_utc": "2026-03-22T00:00:00Z",
  "created_by": "archivist",
  "operator_confirmed": false,
  "source_refs": [
    "docs/faz9d4_report.md",
    "bench/out/faz9d4_report.json"
  ]
}
```

### 12.2 Required Contract Rules

A durable memory item is invalid if:
- `memory_id` missing
- `memory_class` invalid
- `state` missing
- `created_at_utc` missing
- `created_by` missing
- `source_refs` missing for anything evidence-bearing

---

## 13. Lineage Model

### 13.1 Definition

Lineage is the chain that connects:
- phase
- commit
- report
- artifact
- package
- external use

Mnemosyne must be able to answer:

**“What exactly supports this claim, and where did it come from?”**

### 13.2 Lineage Chain Example

```json
{
  "lineage_id": "lin_faz9d4_epic_pkg_v1",
  "root_phase": "faz9d4",
  "commit_refs": [
    "e40e402",
    "23ddfa8"
  ],
  "report_refs": [
    "docs/faz9d4_report.md",
    "bench/out/faz9d4_report.json"
  ],
  "artifact_refs": [
    "exports/pilot_demo_v1/01_PASS_SCENARIO/Mnemosyne_Certified_Passport.json",
    "exports/pilot_demo_v1/02_FAIL_SCENARIO/fail_run_summary.json"
  ],
  "package_refs": [
    "exports/pilot_demo_v1.zip"
  ],
  "external_refs": []
}
```

### 13.3 Lineage Rules

- every external-facing proof should have lineage
- if lineage is broken, claim usage must be blocked
- superseded artifacts must not silently remain primary evidence

---

## 14. Approval History Model

### 14.1 Definition

Approval History stores operator decisions over time.

It answers:
- what KS approved
- what KS rejected
- what was blocked
- what was sent
- what remained draft-only

### 14.2 Example

```json
{
  "approval_id": "appr_epic_draft_v1",
  "object_type": "outreach_draft",
  "object_ref": "drafts/epic_intro_v1.md",
  "decision": "approved",
  "decided_by": "ks",
  "decided_at_utc": "2026-03-22T00:00:00Z",
  "notes": "Use for Epic only, not investors"
}
```

### 14.3 Decision Values

- `approved`
- `rejected`
- `deferred`
- `blocked`
- `delivered_confirmed`

### 14.4 Rules

- no silent approval
- no inferred approval from inactivity
- approval applies only to the referenced object/version
- approval does not automatically roll forward to later variants

---

## 15. Memory Read Policy

### 15.1 Commander

May read:
- operator memory
- session memory
- task memory
- relationship memory
- procedural memory
- artifact summaries

May not reinterpret evidence as approved truth without Archivist or operator confirmation.

### 15.2 Archivist

May read:
- all artifact memory
- task memory
- procedural memory
- relationship memory when relevant

Primary role:
- truth maintenance
- evidence selection
- lineage verification

### 15.3 Outreach

May read:
- relationship memory
- approved evidence summaries
- operator preferences
- current task/session context

May not directly reinterpret raw artifacts beyond validated summaries.

### 15.4 Pilot Ops

May read:
- artifact memory
- procedural memory
- package-related relationship memory
- session context

May not use unverified artifacts in packaging.

---

## 16. Memory Write Policy

### 16.1 Commander

May write:
- session memory
- task state
- approval requests
- delivery records
- status summaries

### 16.2 Archivist

May write:
- artifact memory
- lineage records
- claim validation records
- evidence summaries

### 16.3 Outreach

May write:
- outreach drafts
- follow-up drafts
- draft status markers

### 16.4 Pilot Ops

May write:
- package readiness records
- export package metadata
- delivery prep notes

### 16.5 Operator-Only Writes

Only KS may directly confirm:
- approval history
- final delivery state
- operator preference changes
- high-impact relationship state changes

---

## 17. Freshness and Invalidation

### 17.1 Freshness Rules

A memory item becomes `stale` when:
- a newer package version supersedes it
- a later phase closure invalidates its status
- a linked artifact has changed
- target account context materially changed

### 17.2 Supersession Rules

A memory item becomes `superseded` when:
- a newer, validated replacement exists
- the old item should no longer be used as the primary reference

### 17.3 Invalid Memory

A memory item is invalid if:
- source refs are broken
- lineage is broken
- approval state conflicts with reality
- claimed status cannot be verified
- operator explicitly revokes it

Invalid memory must not be read as trusted.

---

## 18. Redaction and External Use

Not all memory is external-safe.

### 18.1 Internal-Only Memory

Examples:
- absolute local paths
- usernames
- internal repo structure
- toolchain quirks
- security triage details
- incomplete drafts

### 18.2 External-Safe Memory

Examples:
- validated package names
- approved proof statements
- public-facing README content
- approved account summaries

### 18.3 Rule

Before external use:
- memory must be validated
- memory must be redaction-safe
- operator must approve if needed

---

## 19. Storage Layout Recommendation

Recommended structure:

```text
memory/
  operator/
    operator_profile_v1.json
  session/
    active_session.json
  tasks/
    task_*.json
  artifacts/
    artifact_*.json
  lineage/
    lineage_*.json
  approvals/
    approval_*.json
  relationships/
    account_*.json
  procedures/
    procedure_*.json
  audits/
    audit_*.jsonl
```

This structure is recommended, not mandatory.

---

## 20. Example End-to-End Memory Path

### Scenario

KS wants an Epic pilot package.

### Memory Flow

1. **Operator Memory**
   - Epic is a priority account
   - send requires ONAY

2. **Session Memory**
   - active workflow: `pilot_package_epic_v1`

3. **Task Memory**
   - `prepare_package` task opened

4. **Artifact Memory**
   - FAZ 9D.4 report selected
   - pilot demo package artifacts selected

5. **Lineage**
   - package linked back to FAZ 9D.4 closure and commits

6. **Approval History**
   - package approved for Epic
   - outreach draft approved separately

7. **Relationship Memory**
   - Epic account status updated to `package_ready_no_send_yet`

This is the intended model:

**state + evidence + lineage + approval**

Not just “memory.”

---

## 21. v1 Anti-Patterns

These are explicitly forbidden patterns.

### 21.1 Summary Without Artifact

Agent says:
- “Epic package is ready”

but no readiness record exists.

Forbidden.

### 21.2 Inferred Approval

Agent assumes:
- “KS didn’t object, so this is approved.”

Forbidden.

### 21.3 Cross-Version Drift

Agent uses an old README with a new package and treats it as current.

Forbidden.

### 21.4 Unsupported Relationship Facts

Agent records:
- “Riot likes X”

without a real interaction or operator confirmation.

Forbidden.

### 21.5 Evidence Drift

Agent repeats a claim after the supporting artifact became stale or superseded.

Forbidden.

---

## 22. Minimum v1 Compliance Requirements

A valid Mnemosyne v1 memory implementation must support:
- operator memory
- session memory
- task memory
- artifact memory
- relationship memory
- procedural memory
- lineage records
- approval history
- freshness state
- invalidation rules

Without these, continuity will become informal and unsafe.

---

## 23. Final Position

Mnemosyne Agent Memory Model v1 is designed to preserve operational continuity without sacrificing explicit trust.

It exists so that KS and the agent layer can answer, at any time:
- what is true
- what is current
- what was approved
- what supports the claim
- what was sent
- what is blocked
- what has been superseded

The model is intentionally conservative.

It does not try to remember everything.

It tries to remember the right things in a way that remains:
- inspectable
- auditable
- versioned
- fail-closed

**Memory in Mnemosyne is not intuition.  
It is controlled continuity.**
