# Mnemosyne Agent Workflows v1
**Status:** Draft v1  
**Scope:** Operational workflows for the Mnemosyne internal 4-agent system  
**Parent Specs:**  
- `agent_architecture_v1.md`
- `agent_contracts_v1.md`  
**Mode:** Fail-Closed / Human-in-the-Loop First

---

## 1. Purpose

This document defines the operational workflows for the Mnemosyne internal 4-agent system.

It describes how agents should work together in practice for:

- evidence retrieval
- outreach drafting
- pilot package creation
- delivery readiness
- approval routing
- exception handling

This is a **workflow document**, not a contract document.

Contracts belong in:

- `agent_contracts_v1.md`

Architecture principles belong in:

- `agent_architecture_v1.md`

---

## 2. Agent Set

Mnemosyne v1 uses the following 4 agents:

1. **Commander**
2. **Archivist**
3. **Outreach**
4. **Pilot Ops**

No other agent participates in v1 workflows.

---

## 3. Global Workflow Rules

These rules apply to all workflows.

### 3.1 Fail-Closed Defaults
If a required input is missing, invalid, or ambiguous:
- stop the workflow
- mark it `blocked` or `escalated`
- do not improvise

### 3.2 Human-in-the-Loop Rule
Any action that could create an external consequence requires operator approval.

Examples:
- sending email
- delivering a pilot package
- claiming a capability externally
- changing account state to "delivered"

### 3.3 Evidence Before Expression
No external-facing draft may include a technical claim unless Archivist has tied it to supporting artifacts.

### 3.4 Artifact-First Rule
Workflow outputs must reference artifacts, not only summaries.

### 3.5 Audit Rule
Each major workflow step should create a corresponding audit event.

---

## 4. Workflow State Model

All workflows move through the same high-level state model.

### 4.1 Workflow States
- `initiated`
- `collecting_inputs`
- `processing`
- `ready_for_review`
- `approved`
- `rejected`
- `blocked`
- `escalated`
- `completed`
- `delivered`

### 4.2 State Semantics
- `initiated`: workflow has been opened
- `collecting_inputs`: required artifacts or context are being gathered
- `processing`: assigned agent is actively producing output
- `ready_for_review`: output is complete and waiting for operator review
- `approved`: operator approved the result
- `rejected`: operator rejected the result
- `blocked`: workflow cannot proceed due to a missing prerequisite
- `escalated`: ambiguity or risk requires operator judgment
- `completed`: internal work is finished
- `delivered`: external handoff confirmed by operator

---

## 5. Standard Workflow Template

Every workflow should be described using this structure:

1. **Trigger**
2. **Objective**
3. **Inputs**
4. **Agent Sequence**
5. **Outputs**
6. **Approval Gate**
7. **Failure Modes**
8. **Completion Condition**

---

## 6. Workflow A — Evidence Retrieval

### 6.1 Trigger
Operator or Commander asks:
- “What proves this?”
- “Which artifacts support this claim?”
- “Which commits/reports prove the current UE5 Gate path?”

### 6.2 Objective
Produce a clean evidence summary tied to specific artifacts and lineage.

### 6.3 Inputs
- target claim or question
- relevant phase name, artifact name, or repo area
- optional audience context

### 6.4 Agent Sequence
1. **Commander**
   - creates `collect_evidence` task
   - routes to Archivist

2. **Archivist**
   - scans docs, reports, manifests, benchmark outputs
   - maps claim -> artifacts
   - marks support status
   - builds evidence summary

3. **Commander**
   - receives evidence summary
   - decides whether to:
     - stop
     - request claim validation
     - pass evidence to Outreach
     - pass evidence to Pilot Ops

### 6.5 Outputs
- `evidence_summary_v1`
- optional `artifact_lineage_v1`
- optional `claim_validation_v1`

### 6.6 Approval Gate
No approval required for internal evidence retrieval.

### 6.7 Failure Modes
- missing report
- conflicting artifact lineage
- unsupported claim
- outdated artifact version

### 6.8 Completion Condition
Evidence summary exists and is traceable to concrete artifacts.

---

## 7. Workflow B — Claim Validation

### 7.1 Trigger
A technical claim is proposed for:
- email draft
- README
- investor update
- technical summary
- pilot package note

### 7.2 Objective
Determine whether the claim is:
- supported
- partially supported
- unsupported
- unclear

### 7.3 Inputs
- claim text
- candidate supporting artifacts

### 7.4 Agent Sequence
1. **Commander**
   - creates `validate_claims` task
   - routes to Archivist

2. **Archivist**
   - checks claim against:
     - reports
     - logs
     - manifests
     - closure docs
   - assigns validation status

3. **Commander**
   - returns result to requesting workflow

### 7.5 Outputs
- `claim_validation_v1`

### 7.6 Approval Gate
No approval required for validation itself.

### 7.7 Failure Modes
- claim overstates evidence
- evidence exists but is partial
- evidence is outdated
- claim cannot be tied to artifact

### 7.8 Completion Condition
Claim has a clear support state.

---

## 8. Workflow C — Outreach Draft Creation

### 8.1 Trigger
Operator or Commander requests a draft for:
- Riot
- Epic
- Ubisoft
- investor
- strategic partner
- studio lead

### 8.2 Objective
Produce an evidence-led outreach draft tailored to the target audience.

### 8.3 Inputs
- target account
- target role
- objective
- evidence summary
- operator tone preference
- optional delivery package

### 8.4 Agent Sequence
1. **Commander**
   - creates `draft_outreach` task
   - requests evidence from Archivist if not already available

2. **Archivist**
   - returns supporting evidence summary
   - flags unsupported claims if any

3. **Commander**
   - routes draft request to Outreach

4. **Outreach**
   - creates:
     - email draft
     - subject line
     - optional follow-up sequence
   - references only validated claims

5. **Commander**
   - presents draft to operator
   - requests approval

### 8.5 Outputs
- `outreach_draft_v1`
- optional `followup_draft_v1`

### 8.6 Approval Gate
Required.

Draft cannot move forward without operator approval.

### 8.7 Failure Modes
- no evidence provided
- unsupported claim
- wrong audience framing
- missing attachment recommendation

### 8.8 Completion Condition
Draft is either:
- `approved`
- `rejected`
- `blocked`

No send occurs in this workflow.

---

## 9. Workflow D — Outreach Redraft

### 9.1 Trigger
Operator says:
- “make it shorter”
- “too technical”
- “less investor language”
- “more direct”
- “Riot version, not Epic version”

### 9.2 Objective
Revise an existing draft without losing evidence grounding.

### 9.3 Inputs
- previous draft
- operator revision request
- original evidence summary

### 9.4 Agent Sequence
1. **Commander**
   - creates `redraft_message` task

2. **Outreach**
   - revises draft
   - preserves evidence linkage

3. **Commander**
   - returns revised draft for review

### 9.5 Outputs
- updated `outreach_draft_v1`

### 9.6 Approval Gate
Required for final use.

### 9.7 Failure Modes
- revision removes evidence-backed clarity
- revision introduces unsupported claim
- version confusion between drafts

### 9.8 Completion Condition
Updated draft reaches `ready_for_review` or `approved`.

---

## 10. Workflow E — Pilot Package Preparation

### 10.1 Trigger
Operator requests:
- pilot evidence package
- Riot package
- Epic package
- investor demo package
- lead-facing export pack

### 10.2 Objective
Create a clean, reproducible package with PASS/FAIL evidence and supporting documentation.

### 10.3 Inputs
- package target
- package version
- relevant PASS/FAIL artifacts
- README requirements
- export path rules

### 10.4 Agent Sequence
1. **Commander**
   - creates `prepare_package` task
   - routes evidence collection request to Archivist

2. **Archivist**
   - selects correct artifacts
   - returns package evidence set

3. **Commander**
   - routes package build request to Pilot Ops

4. **Pilot Ops**
   - creates export structure
   - copies approved artifacts
   - writes README, manifest, checksums
   - writes package readiness report

5. **Archivist**
   - optionally validates package completeness

6. **Commander**
   - presents package readiness summary
   - requests operator approval

### 10.5 Outputs
- `package_export_v1`
- `package_readiness_v1`
- package directory
- README
- manifest
- checksums

### 10.6 Approval Gate
Required before external delivery.

### 10.7 Failure Modes
- missing PASS artifact
- missing FAIL artifact
- missing checksum file
- incomplete README
- leaked internal metadata
- incorrect package versioning

### 10.8 Completion Condition
Package is either:
- `ready_for_review`
- `approved`
- `blocked`

---

## 11. Workflow F — Package Validation

### 11.1 Trigger
Package has been created and must be validated before delivery.

### 11.2 Objective
Verify package completeness, correctness, and evidence coverage.

### 11.3 Inputs
- package path
- manifest
- checksum file
- expected contents list

### 11.4 Agent Sequence
1. **Commander**
   - creates `validate_package` task
   - routes to Archivist

2. **Archivist**
   - checks:
     - required files present
     - claims match artifacts
     - package structure correct
     - README is consistent with evidence
   - returns validation result

3. **Commander**
   - presents validation result to operator

### 11.5 Outputs
- package validation note
- updated readiness status

### 11.6 Approval Gate
Required if package is to be sent externally.

### 11.7 Failure Modes
- mismatch between README and evidence
- missing PASS/FAIL symmetry
- leaked internal paths
- checksum mismatch

### 11.8 Completion Condition
Package is either:
- `approved`
- `blocked`
- `escalated`

---

## 12. Workflow G — Delivery Readiness Review

### 12.1 Trigger
Operator asks:
- “Is this package send-ready?”
- “Can this go to Epic?”
- “Is this investor-safe?”

### 12.2 Objective
Produce a final send/no-send internal readiness decision.

### 12.3 Inputs
- validated package
- audience target
- latest claim validation
- operator constraints

### 12.4 Agent Sequence
1. **Commander**
   - creates `collect_delivery_readiness` task
   - routes to Pilot Ops and optionally Archivist

2. **Pilot Ops**
   - confirms package integrity and paths

3. **Archivist**
   - confirms evidence support and no unsupported claims

4. **Commander**
   - assembles readiness summary
   - asks for operator decision

### 12.5 Outputs
- delivery readiness summary

### 12.6 Approval Gate
Mandatory.

### 12.7 Failure Modes
- package complete but claims not clean
- claims clean but package incomplete
- target-specific redactions missing

### 12.8 Completion Condition
Operator explicitly decides:
- `approved`
- `rejected`
- `blocked`

---

## 13. Workflow H — External Delivery

### 13.1 Trigger
Operator explicitly approves delivery.

### 13.2 Objective
Record the fact that a package or draft has moved outside the internal system.

### 13.3 Inputs
- approved package or approved draft
- target account
- operator confirmation

### 13.4 Agent Sequence
1. **Commander**
   - records approved object
   - records target
   - records operator confirmation

2. **Commander**
   - marks state as `delivered`

### 13.5 Outputs
- delivery record
- audit event

### 13.6 Approval Gate
Already satisfied by operator.

### 13.7 Failure Modes
- missing explicit operator confirmation
- uncertainty whether delivery actually happened

### 13.8 Completion Condition
A delivery record exists with operator confirmation.

> Note: v1 does not require automated send capability.  
> Delivery may be manual and still be recorded correctly.

---

## 14. Workflow I — Status Summary

### 14.1 Trigger
Operator asks:
- “Where are we?”
- “What is blocked?”
- “What is ready?”
- “What was the last good artifact?”

### 14.2 Objective
Provide a concise operational summary.

### 14.3 Inputs
- current tasks
- approval states
- package states
- draft states
- escalation records

### 14.4 Agent Sequence
1. **Commander**
   - creates `summarize_status` task
   - queries internal state and recent outputs

2. **Commander**
   - emits summary

### 14.5 Outputs
- `status_summary_v1`

### 14.6 Approval Gate
Not required.

### 14.7 Failure Modes
- stale session state
- unresolved escalations omitted
- incorrect readiness state

### 14.8 Completion Condition
Summary is visible and current.

---

## 15. Workflow J — Exception Handling / Escalation

### 15.1 Trigger
Any workflow detects:
- ambiguity
- unsupported claim
- invalid artifact lineage
- missing approval
- missing package file
- invalid contract state
- unknown tool output

### 15.2 Objective
Stop unsafe continuation and transfer decision authority to operator.

### 15.3 Inputs
- original task
- failure reason
- relevant artifacts

### 15.4 Agent Sequence
1. **Current agent**
   - writes escalation record
   - stops work

2. **Commander**
   - summarizes the issue
   - routes to operator for decision

### 15.5 Outputs
- escalation record
- blocked task state
- operator action request

### 15.6 Approval Gate
Mandatory for resumption.

### 15.7 Failure Modes
- continuing after ambiguity
- silent fallback
- fabricated resolution

### 15.8 Completion Condition
Operator chooses:
- resolve and continue
- reject
- defer
- terminate workflow

---

## 16. Workflow K — Relationship Update

### 16.1 Trigger
A meaningful external interaction occurs.

Examples:
- package sent
- reply received
- audience preference learned
- contact moved priority

### 16.2 Objective
Update relationship memory safely.

### 16.3 Inputs
- account name
- event
- operator note or observed evidence

### 16.4 Agent Sequence
1. **Commander**
   - captures update request

2. **Archivist** or **Commander**
   - writes relationship update

3. **Commander**
   - confirms current state

### 16.5 Outputs
- updated relationship memory entry

### 16.6 Approval Gate
Required for high-impact changes.

### 16.7 Failure Modes
- inferred state written as fact
- duplicate account identity
- unsupported preference recorded

### 16.8 Completion Condition
Relationship memory reflects operator-confirmed state.

---

## 17. Workflow L — Phase Closure Support

### 17.1 Trigger
A protocol or implementation phase is ending.

### 17.2 Objective
Capture closure notes, supporting artifacts, and stable reference points.

### 17.3 Inputs
- phase report
- benchmark outputs
- closure summary
- commit references

### 17.4 Agent Sequence
1. **Commander**
   - opens closure request

2. **Archivist**
   - collects closure evidence
   - confirms supporting artifacts

3. **Pilot Ops** (optional)
   - packages closure evidence if needed

4. **Commander**
   - requests operator approval for closure note

### 17.5 Outputs
- closure note
- closure evidence set

### 17.6 Approval Gate
Required.

### 17.7 Failure Modes
- missing benchmark proof
- missing commit linkage
- closure note overstates result

### 17.8 Completion Condition
Closure note is saved with artifact references.

---

## 18. Standard Operator Checkpoints

The operator should expect approval requests at these points:

### 18.1 Outreach
- before any external-facing draft is used

### 18.2 Packaging
- before any package is marked send-ready

### 18.3 Delivery
- before any package/draft is marked delivered

### 18.4 Claim Escalation
- whenever a claim is only partially supported or unclear

### 18.5 Relationship Change
- when a high-impact account state changes

---

## 19. Readiness and Block Conditions

### 19.1 A Draft Is Ready Only If
- evidence exists
- unsupported claims removed
- audience is identified
- operator can review it

### 19.2 A Package Is Ready Only If
- PASS evidence exists
- FAIL evidence exists
- README exists
- EXPORT_MANIFEST exists
- SHA256SUMS exists
- no sensitive internal leakage remains
- validation did not fail

### 19.3 A Workflow Is Blocked If
- approval missing
- required artifact missing
- contract invalid
- claim unsupported
- target ambiguous
- package integrity fails

---

## 20. Recommended File Outputs by Workflow

| Workflow | Typical Outputs |
|---------|------------------|
| Evidence Retrieval | `evidence_summary_v1`, lineage note |
| Claim Validation | `claim_validation_v1` |
| Outreach Draft | email draft, subject line, follow-up note |
| Pilot Packaging | export folder, README, manifest, checksums |
| Package Validation | package validation note |
| Delivery Readiness | readiness summary |
| External Delivery | delivery record |
| Status Summary | current-state summary |
| Escalation | escalation record |
| Phase Closure | closure note + evidence refs |

---

## 21. v1 Operating Discipline

Mnemosyne v1 workflows are optimized for:

- speed with control
- clarity with evidence
- packaging with traceability
- drafting with approval
- execution without hidden trust

They are **not** optimized for full autonomy.

That is intentional.

---

## 22. Final Position

Mnemosyne Agent Workflows v1 are designed to preserve protocol discipline while accelerating execution.

They assume:

- explicit evidence
- explicit approval
- explicit package readiness
- explicit escalation
- explicit delivery state

The system should move quickly.

But it should never move implicitly.
