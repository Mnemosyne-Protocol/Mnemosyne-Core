# Mnemosyne Agent System v1 — Index
**Status:** Draft v1  
**Scope:** Entry point and navigation file for the Mnemosyne internal agent system  
**Mode:** Fail-Closed / Artifact-First / Human-in-the-Loop First

---

## 1. Purpose

This document is the top-level index for the Mnemosyne Agent System v1.

It exists to make the agent layer easy to navigate, review, and maintain.

Use this file to answer:

- what the Mnemosyne agent layer is
- which documents define it
- where architecture ends and execution begins
- where contracts, workflows, memory, and telemetry are defined
- what should be read first by an operator, architect, or implementation agent

This is an index document, not a full specification.

---

## 2. System Position

Mnemosyne Agent System v1 is an **internal operating layer** around the Mnemosyne Protocol.

It does **not** replace the core product.

The core product remains:

- Gate
- Passport
- Quarantine
- Evidence Pack
- Fail-Closed Admission Logic

The agent system exists to accelerate:

- evidence retrieval
- outreach drafting
- pilot package preparation
- approval routing
- delivery readiness
- operational continuity

Its purpose is controlled acceleration, not unrestricted autonomy.

---

## 3. Reading Order

Recommended reading order:

1. `agent_architecture_v1.md`
2. `agent_contracts_v1.md`
3. `agent_workflows_v1.md`
4. `agent_memory_model_v1.md`
5. `agent_telemetry_and_eval_v1.md`

This order moves from:
- strategic design
- to formal contracts
- to operational workflows
- to continuity/state
- to measurement and evaluation

---

## 4. Document Map

### 4.1 `agent_architecture_v1.md`

**What it is:**  
The top-level design document for the Mnemosyne internal 4-agent system.

**What it defines:**
- why the agent layer exists
- the 4-agent structure
- fail-closed design principles
- role boundaries
- tool permission philosophy
- system-level guardrails

**Read this when:**
- defining the system for the first time
- explaining the architecture to a collaborator
- checking whether a proposed change violates the original design intent

**In one sentence:**  
This is the strategic blueprint.

---

### 4.2 `agent_contracts_v1.md`

**What it is:**  
The formal contract/specification layer for the agent system.

**What it defines:**
- allowed agent IDs
- task envelope schema
- approval state machine
- audit event schema
- memory class contracts
- tool permissions
- escalation rules
- hard guardrails

**Read this when:**
- implementing agent behavior
- validating whether an action is allowed
- checking if a workflow step is valid
- defining structured agent-to-agent communication

**In one sentence:**  
This is the rules engine in document form.

---

### 4.3 `agent_workflows_v1.md`

**What it is:**  
The operational runbook for how the 4 agents collaborate in practice.

**What it defines:**
- evidence retrieval workflow
- claim validation workflow
- outreach draft workflow
- package preparation workflow
- package validation workflow
- delivery readiness workflow
- escalation workflow
- phase closure support workflow

**Read this when:**
- running the system operationally
- implementing or reviewing actual task sequences
- understanding where approval gates occur
- debugging why a workflow stopped or escalated

**In one sentence:**  
This is the execution playbook.

---

### 4.4 `agent_memory_model_v1.md`

**What it is:**  
The continuity and state model for the Mnemosyne agent system.

**What it defines:**
- operator memory
- session memory
- task memory
- artifact memory
- relationship memory
- procedural memory
- lineage model
- approval history
- freshness and invalidation rules

**Read this when:**
- deciding what the system should remember
- designing continuity between sessions
- checking whether a remembered state is trustworthy
- tracing what was approved, sent, or superseded

**In one sentence:**  
This is the controlled continuity layer.

---

### 4.5 `agent_telemetry_and_eval_v1.md`

**What it is:**  
The measurement, dashboard, and evaluation framework for the agent system.

**What it defines:**
- throughput metrics
- quality metrics
- override rate
- draft acceptance
- package correctness
- escalation health
- audit coverage
- dashboard views
- thresholds and alerting logic

**Read this when:**
- evaluating whether the system is improving
- measuring friction and correctness
- diagnosing hidden risk
- deciding whether the agent layer is helping or harming operations

**In one sentence:**  
This is the discipline and health dashboard.

---

## 5. System Summary

Mnemosyne Agent System v1 is built around 4 internal agents:

- **Commander** — orchestration and approval gateway
- **Archivist** — evidence retrieval and factual validation
- **Outreach** — external draft generation
- **Pilot Ops** — package preparation and delivery readiness

The system is designed to be:

- fail-closed
- artifact-first
- least-privilege
- human-in-the-loop
- auditable
- evidence-led

It is intentionally narrow.

It does not aim to be a general autonomous company system.

---

## 6. Operator View (KS)

For KS, the system should answer five practical questions clearly:

1. **What is true?**  
   Answered through artifacts, validation, and lineage.

2. **What is ready?**  
   Answered through package readiness and workflow state.

3. **What is blocked?**  
   Answered through escalation and fail-closed workflow behavior.

4. **What was approved or delivered?**  
   Answered through approval history and relationship memory.

5. **What is improving or degrading?**  
   Answered through telemetry and evaluation.

If the system cannot answer those five questions cleanly, it is not mature enough.

---

## 7. Implementation Boundaries

The v1 system is explicitly **not** allowed to do the following autonomously:

- send email without operator approval
- push code without operator approval
- delete artifacts by default
- mutate Gate logic
- mutate taxonomy/schema/contracts
- invent unsupported claims
- silently resolve ambiguity

Any proposed extension beyond those boundaries should be treated as a versioned change.

---

## 8. Suggested File Layout

Recommended layout:

```text
docs/
  agent_system/
    v1/
      mnemosyne_agent_system_v1_index.md
      mnemosyne_agent_system_v1_executive_summary.md
      agent_architecture_v1.md
      agent_contracts_v1.md
      agent_workflows_v1.md
      agent_memory_model_v1.md
      agent_telemetry_and_eval_v1.md
```

Optional adjacent folders:

```text
/ops/
/memory/
/telemetry/
/task_envelopes/
/audit_logs/
/drafts/
/exports/
```

The index should remain at the top of the `docs/agent_system/v1/` stack.

---

## 9. Recommended Usage

### For KS

Read:
- this index
- `agent_architecture_v1.md`
- `agent_workflows_v1.md`

### For implementation work

Read:
- `agent_contracts_v1.md`
- `agent_workflows_v1.md`
- `agent_memory_model_v1.md`

### For operational review

Read:
- `agent_workflows_v1.md`
- `agent_telemetry_and_eval_v1.md`

### For debugging trust issues

Read:
- `agent_contracts_v1.md`
- `agent_memory_model_v1.md`
- `agent_telemetry_and_eval_v1.md`

---

## 10. Versioning Guidance

This index is for **v1** only.

If any of the following change materially, v2 should be considered:

- new agent added
- send permissions expanded
- memory classes changed
- approval state machine changed
- external delivery becomes semi-automated
- workflows move beyond pilot/evidence/outreach scope

---

## 11. Final Position

Mnemosyne Agent System v1 is a controlled operating layer designed to increase speed without weakening trust.

Its function is not to create artificial confidence.

Its function is to keep the following explicit at all times:

- evidence
- approval
- readiness
- lineage
- escalation
- responsibility

Use this index as the entry point.

Then go to the specific document that governs the question at hand.

**Architecture defines intent.  
Contracts define limits.  
Workflows define action.  
Memory defines continuity.  
Telemetry defines discipline.**
