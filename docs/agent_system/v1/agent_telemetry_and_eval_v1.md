# Mnemosyne Agent Telemetry and Evaluation v1
**Status:** Draft v1  
**Scope:** Metrics, audit visibility, evaluation, override tracking, delivery quality, and escalation health for the Mnemosyne internal 4-agent system  
**Parent Specs:**  
- `agent_architecture_v1.md`
- `agent_contracts_v1.md`
- `agent_workflows_v1.md`
- `agent_memory_model_v1.md`  
**Mode:** Fail-Closed / Artifact-First / Human-in-the-Loop First

---

## 1. Purpose

This document defines how the Mnemosyne internal 4-agent system is observed, measured, and evaluated.

It standardizes:

- telemetry categories
- audit dashboard dimensions
- workflow metrics
- override metrics
- draft quality metrics
- package quality metrics
- escalation health metrics
- evaluation cadences
- minimum alert thresholds
- interpretation rules

The goal is not generic analytics.

The goal is:

- trustable operations
- measurable quality
- visible failure modes
- fast diagnosis
- disciplined improvement

---

## 2. Core Position

Mnemosyne agents are not evaluated by “sounding smart.”

They are evaluated by whether they:

- route correctly
- preserve evidence integrity
- reduce operator effort without increasing risk
- stop when they should stop
- package correctly
- avoid unsupported claims
- surface ambiguity instead of hiding it

Telemetry exists to answer one question:

**Is the agent layer accelerating operations without weakening Mnemosyne discipline?**

---

## 3. Evaluation Principles

### 3.1 Fail-Closed Metrics

A blocked action is not automatically bad.  
A silent unsafe action is always bad.

### 3.2 Quality Over Volume

More drafts, more packages, or more messages do not indicate success by themselves.  
Correctness and reviewability matter more than throughput.

### 3.3 Artifact-Backed Evaluation

Metrics should be traceable to:
- audit logs
- approval records
- package manifests
- claim validation records
- workflow state changes

### 3.4 Operator Friction Is a Signal

Excessive operator overrides or repeated corrections indicate system weakness.

### 3.5 Escalation Is Healthy When Earned

A system that never escalates may be overconfident.  
A system that escalates everything may be unusable.

---

## 4. Telemetry Categories

Mnemosyne v1 telemetry is divided into 7 categories:

1. **Workflow Throughput**
2. **Quality and Correctness**
3. **Operator Friction**
4. **Claim Discipline**
5. **Packaging Integrity**
6. **Escalation Health**
7. **System Audit Coverage**

---

## 5. Telemetry Event Model

Every meaningful workflow action should be observable through structured telemetry events.

### 5.1 Minimal Telemetry Event

```json
{
  "event_id": "uuid",
  "timestamp_utc": "2026-03-22T00:00:00Z",
  "agent": "outreach",
  "workflow_id": "wf_outreach_epic_v1",
  "task_id": "task_outreach_epic_001",
  "event_type": "draft_generated",
  "status": "success",
  "duration_ms": 1840,
  "artifact_refs": [
    "drafts/epic_intro_v1.md"
  ],
  "approval_state": "ready_for_review",
  "notes": "Evidence-linked draft generated"
}
```

### 5.2 Required Fields

| Field | Type | Required |
|------|------|----------|
| `event_id` | string | yes |
| `timestamp_utc` | string | yes |
| `agent` | string | yes |
| `workflow_id` | string | yes |
| `task_id` | string | yes |
| `event_type` | string | yes |
| `status` | string | yes |
| `duration_ms` | number | no but strongly recommended |
| `artifact_refs` | array[string] | no |
| `approval_state` | string | yes |

---

## 6. Workflow Throughput Metrics

These metrics measure operational speed, but are always secondary to correctness.

### 6.1 Workflow Completion Rate

Definition:
- number of workflows reaching `completed` or `delivered`
- divided by total workflows opened in the time window

Formula:

```text
workflow_completion_rate = completed_or_delivered / total_opened
```

### 6.2 Median Workflow Time

Definition:
- median elapsed time from `initiated` to `completed` or `blocked`

Tracked by workflow type:
- evidence retrieval
- outreach draft
- package preparation
- delivery readiness

### 6.3 Queue Depth

Definition:
- number of workflows currently in:
  - `ready_for_review`
  - `blocked`
  - `escalated`

This is a leading indicator of operator load.

---

## 7. Quality and Correctness Metrics

These are the most important metrics.

### 7.1 Evidence Retrieval Precision

Definition:
- percent of evidence summaries that correctly map claims to real supporting artifacts

Formula:

```text
evidence_precision = correct_evidence_mappings / total_evidence_mappings_reviewed
```

### 7.2 Artifact Lineage Completeness

Definition:
- percent of exported packages or proof claims with a complete lineage chain:
  - phase
  - commit
  - report
  - artifact
  - package

### 7.3 Claim Support Accuracy

Definition:
- percent of claims labeled `supported` that remain supported after operator review

### 7.4 False Confidence Rate

Definition:
- rate at which the system marked something as ready, supported, or valid when it should not have

Formula:

```text
false_confidence_rate = false_ready_or_false_supported_items / total_reviewed_items
```

Target:
- as close to zero as possible

---

## 8. Operator Friction Metrics

Operator friction is a first-class quality signal.

### 8.1 Override Rate

Definition:
- percent of outputs requiring meaningful operator correction before use

Formula:

```text
override_rate = corrected_outputs / reviewed_outputs
```

Interpretation:
- low rate: system is aligned
- high rate: drafts/packages are too noisy or misframed

### 8.2 Rejection Rate

Definition:
- percent of outputs explicitly rejected by operator

Tracked separately for:
- outreach drafts
- package readiness summaries
- relationship updates

### 8.3 Review Latency

Definition:
- time between `ready_for_review` and operator decision

This helps distinguish:
- system bottleneck
- operator bottleneck
- unclear output

### 8.4 Escalation Resolution Time

Definition:
- time between `escalated` and operator decision

---

## 9. Draft Quality Metrics

These apply primarily to Outreach.

### 9.1 Draft Acceptance Rate

Definition:
- percent of drafts approved without material changes

Formula:

```text
draft_acceptance_rate = drafts_approved_without_material_changes / total_drafts_reviewed
```

### 9.2 Draft Revision Rate

Definition:
- percent of drafts requiring at least one revision cycle

### 9.3 Unsupported Claim Incidence

Definition:
- number of external-facing draft statements flagged as unsupported or unclear

Tracked per draft and over time.

### 9.4 Audience Fit Score

Qualitative metric recorded by operator after review.

Allowed values:
- `strong_fit`
- `acceptable`
- `too_technical`
- `too_generic`
- `too_hyped`
- `misaligned`

---

## 10. Package Quality Metrics

These apply primarily to Pilot Ops + Archivist.

### 10.1 Package Correctness Rate

Definition:
- percent of packages that pass readiness validation without defect

Formula:

```text
package_correctness_rate = packages_passing_validation / total_packages_built
```

### 10.2 Missing Artifact Rate

Definition:
- percent of packages blocked because required artifacts were missing

### 10.3 Checksum Coverage

Definition:
- percent of files in package covered by checksum manifest

Formula:

```text
checksum_coverage = files_hashed / total_files_in_package
```

Target:
- 100%

### 10.4 README Consistency Rate

Definition:
- percent of package README claims that match package evidence after Archivist validation

### 10.5 Redaction Safety Rate

Definition:
- percent of external packages that pass redaction checks with no internal-only leakage

Examples of leakage:
- local absolute paths
- usernames
- internal repo structure
- secret triage details

---

## 11. Escalation Health Metrics

Escalation is a controlled feature, not a failure by default.

### 11.1 Escalation Rate

Definition:
- percent of workflows that escalate

Formula:

```text
escalation_rate = escalated_workflows / total_workflows
```

Interpretation:
- very low may indicate overconfidence
- very high may indicate weak contracts or poor routing

### 11.2 Valid Escalation Rate

Definition:
- percent of escalations the operator agrees were necessary

### 11.3 Avoidable Escalation Rate

Definition:
- escalations caused by missing obvious context, poor state handling, or missing contract lookup

### 11.4 Silent Failure Rate

Definition:
- workflows that should have escalated but did not

This is a critical metric.

Target:
- zero

---

## 12. System Audit Coverage Metrics

These ensure visibility.

### 12.1 Audit Coverage Ratio

Definition:
- percent of meaningful actions that produced audit events

Formula:

```text
audit_coverage_ratio = logged_actions / meaningful_actions
```

Target:
- near 100%

### 12.2 Unattributed Output Rate

Definition:
- outputs that exist without a linked task, workflow, or audit event

Target:
- zero

### 12.3 Artifact Without Lineage Rate

Definition:
- exported or cited artifacts lacking lineage records

Target:
- zero

---

## 13. Dashboard Model v1

The v1 dashboard should expose 5 operational views.

### 13.1 Workflow Overview

Shows:
- active workflows
- blocked workflows
- escalated workflows
- median completion time
- review queue depth

### 13.2 Quality View

Shows:
- evidence precision
- claim support accuracy
- false confidence rate
- package correctness rate

### 13.3 Operator Friction View

Shows:
- override rate
- rejection rate
- review latency
- escalation resolution time

### 13.4 Delivery View

Shows:
- draft acceptance rate
- package readiness count
- delivered count
- target account pipeline

### 13.5 Risk View

Shows:
- unsupported claim incidence
- redaction failures
- silent failure rate
- audit coverage gaps

---

## 14. Recommended Dashboard Schema

```json
{
  "window_start_utc": "2026-03-22T00:00:00Z",
  "window_end_utc": "2026-03-29T00:00:00Z",
  "workflow": {
    "opened": 12,
    "completed": 9,
    "blocked": 2,
    "escalated": 1,
    "median_completion_minutes": 27
  },
  "quality": {
    "evidence_precision": 0.94,
    "claim_support_accuracy": 0.96,
    "false_confidence_rate": 0.00,
    "package_correctness_rate": 0.89
  },
  "operator_friction": {
    "override_rate": 0.22,
    "draft_acceptance_rate": 0.61,
    "median_review_minutes": 18
  },
  "risk": {
    "unsupported_claim_incidence": 1,
    "silent_failure_rate": 0.00,
    "audit_coverage_ratio": 0.98
  }
}
```

---

## 15. Evaluation Cadence

### 15.1 Per-Workflow Evaluation

Every completed workflow should record:
- duration
- final state
- whether escalation occurred
- whether operator correction occurred

### 15.2 Daily Review

Review:
- blocked items
- escalations
- new packages
- external draft readiness

### 15.3 Weekly Review

Review:
- draft acceptance
- override rate
- package correctness
- evidence precision
- audit coverage

### 15.4 Phase-End Review

At phase closure, review:
- what workflows improved speed
- what workflows created friction
- whether guardrails held
- whether any false confidence incidents occurred

---

## 16. Thresholds and Alerts

The following thresholds are recommended for v1.

### 16.1 Critical Alerts

Trigger immediate review if:
- `silent_failure_rate > 0`
- `audit_coverage_ratio < 0.95`
- `false_confidence_rate > 0`
- `artifact_without_lineage_rate > 0`

### 16.2 Warning Alerts

Trigger inspection if:
- `override_rate > 0.35`
- `draft_acceptance_rate < 0.40`
- `package_correctness_rate < 0.80`
- `valid_escalation_rate < 0.70`

### 16.3 Informational Alerts

Track but do not immediately treat as failure:
- escalation rate rising moderately
- review latency increasing due to operator load
- increased draft revisions for new account types

---

## 17. Agent-Specific Scorecards

### 17.1 Commander Scorecard

Track:
- routing accuracy
- blocked-vs-should-block accuracy
- escalation correctness
- status summary usefulness

**Good Outcome**  
Commander routes efficiently and escalates only when needed.

**Bad Outcome**  
Commander overroutes, hides blockers, or advances ambiguous tasks.

### 17.2 Archivist Scorecard

Track:
- evidence precision
- lineage completeness
- unsupported claim prevention
- validation turnaround time

**Good Outcome**  
Archivist acts as a factual stabilizer.

**Bad Outcome**  
Archivist selects stale or incomplete evidence.

### 17.3 Outreach Scorecard

Track:
- draft acceptance rate
- revision rate
- unsupported claim incidence
- audience fit score

**Good Outcome**  
Drafts are concise, evidence-led, and accepted with minimal edits.

**Bad Outcome**  
Drafts are noisy, overhyped, or require heavy operator rewrite.

### 17.4 Pilot Ops Scorecard

Track:
- package correctness rate
- missing artifact rate
- checksum coverage
- redaction safety rate

**Good Outcome**  
Packages are reproducible, complete, and safe to review.

**Bad Outcome**  
Packages look complete but fail validation or leak internal detail.

---

## 18. Minimum Review Artifacts

Each evaluation cycle should be able to produce:
- workflow summary
- blocked workflow list
- escalation summary
- draft review summary
- package readiness summary
- unsupported claim report
- audit coverage report

These can be JSON, markdown, or dashboard snapshots.

---

## 19. Interpretation Rules

### 19.1 A Block Is Not Always a Failure

If a workflow blocked because a checksum file was missing, that is the system working correctly.

### 19.2 Low Throughput Is Not Automatically Bad

If throughput is lower because the system prevented bad drafts or incomplete packages, that is acceptable.

### 19.3 Fast Is Not Better If It Is Wrong

A rapid draft that introduces unsupported claims is worse than a slower, validated draft.

### 19.4 Operator Corrections Should Trend Down

The system should become easier to supervise over time, not noisier.

### 19.5 False Confidence Is the Worst Failure

The most dangerous failure mode is:
- presenting something as supported when it is not
- marking something ready when it is not
- avoiding escalation when escalation was required

---

## 20. Anti-Patterns

The following are explicitly disallowed evaluation patterns.

### 20.1 Vanity Throughput

Measuring success by:
- number of drafts generated
- number of files copied
- number of workflow steps completed

without correctness context

### 20.2 Hidden Human Labor

Declaring agent success while ignoring heavy operator rewrite, manual cleanup, or implicit corrections

### 20.3 Silent Blocker Suppression

Ignoring blocked actions to make dashboards look healthy

### 20.4 Unlabeled Manual Recovery

Treating manually fixed outputs as if the agent produced them cleanly

### 20.5 Cross-Workflow Metric Confusion

Comparing evidence retrieval speed directly against outreach approval rates without context

---

## 21. Storage Layout Recommendation

Recommended telemetry layout:

```text
telemetry/
  dashboards/
    weekly_summary_*.json
  workflows/
    workflow_metrics_*.json
  drafts/
    draft_review_metrics_*.json
  packages/
    package_quality_metrics_*.json
  escalations/
    escalation_metrics_*.json
  audits/
    audit_coverage_metrics_*.json
  alerts/
    alert_*.json
```

This layout is recommended, not mandatory.

---

## 22. Example Weekly Eval Record

```json
{
  "week_id": "2026-W12",
  "summary": {
    "workflows_opened": 14,
    "workflows_completed": 10,
    "workflows_blocked": 3,
    "workflows_escalated": 1
  },
  "quality": {
    "evidence_precision": 0.95,
    "claim_support_accuracy": 1.00,
    "false_confidence_rate": 0.00,
    "package_correctness_rate": 0.90
  },
  "operator_friction": {
    "override_rate": 0.18,
    "draft_acceptance_rate": 0.67,
    "median_review_minutes": 16
  },
  "risk": {
    "unsupported_claim_incidence": 0,
    "silent_failure_rate": 0.00,
    "audit_coverage_ratio": 0.99
  },
  "notes": [
    "Epic pilot package passed validation",
    "One outreach draft required tone reduction",
    "No false-ready package incidents"
  ]
}
```

---

## 23. v1 Success Criteria

The Mnemosyne agent layer is considered healthy in v1 if:
- false confidence remains at or near zero
- silent failure remains zero
- evidence precision remains high
- package correctness remains high
- override rate trends down over time
- audit coverage remains near complete
- escalation is used deliberately, not excessively
- operator trust increases, not decreases

---

## 24. Final Position

Mnemosyne Agent Telemetry and Evaluation v1 exists to make agent operations measurable without collapsing into vanity metrics.

It should tell KS, at any moment:
- what is working
- what is blocked
- what is noisy
- what is risky
- what is improving
- what should not be trusted yet

The goal is not impressive numbers.

The goal is:
- visible discipline
- measurable quality
- safe acceleration
- fail-closed operations

**If the numbers look good but trust went down, the system failed.  
If the numbers are modest but confidence, evidence quality, and control improved, the system is working.**
