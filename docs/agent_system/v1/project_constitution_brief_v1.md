# Mnemosyne Agent System v1 — Project Constitution Brief
**Status:** Pre-Implementation Review Brief  
**Audience:** Claude.ai Project context  
**Author:** Kerem Salman (KS)  
**Mode:** Fail-Closed / Human-in-the-Loop First / Architecture Review Before Runtime

---

## 1. Purpose of This Brief

This document is the primary briefing note for the Claude.ai Project that will review, pressure-test, and refine the Mnemosyne Agent System v1 before implementation begins.

This is **not** the full specification.

This is the high-level framing document that explains:

- what Mnemosyne is
- why the internal 4-agent layer exists
- what the current implementation boundary is
- what is in scope now
- what is intentionally deferred
- how Claude should evaluate the system

The goal is simple:

**Review the architecture before building the runtime.**

---

## 2. What Mnemosyne Is

Mnemosyne is a **Verification Protocol**, not a generator.

Its core function is not to create media.  
Its core function is to:

- evaluate submitted artifacts
- enforce fail-closed admission
- issue certification only on explicit pass conditions
- preserve provenance, lineage, and auditability
- block unsafe or invalid assets before downstream entry

Core product concepts include:

- Gate
- Passport
- Quarantine
- Evidence Pack
- Fail-Closed Admission Logic

The internal agent system does **not** replace this core.

It exists around the protocol as an operating layer.

---

## 3. Why the Agent Layer Exists

As Mnemosyne moves from technical proof toward pilot execution, the main risk is no longer only protocol correctness.

The new risks are operational:

- the wrong evidence being surfaced
- unsupported claims leaking into outreach
- incomplete pilot packages being treated as ready
- continuity being lost between work sessions
- operator approval being bypassed implicitly
- future implementation scope expanding too early

The agent layer is intended to reduce those risks while increasing speed.

Its purpose is:

- evidence retrieval
- claim validation
- draft preparation
- package readiness
- approval routing
- controlled continuity

This system is being designed as an **internal operating layer**, not as an autonomous AI company shell.

---

## 4. The v1 Agent Set

Mnemosyne Agent System v1 uses exactly four agents:

1. **Commander**
2. **Archivist**
3. **Outreach**
4. **Pilot Ops**

### Commander
Owns orchestration, routing, approval checkpoints, and status summaries.

### Archivist
Owns evidence retrieval, artifact lineage, factual validation, and claim support checks.

### Outreach
Owns external draft preparation only.

### Pilot Ops
Owns package creation, export structure, manifest/checksum readiness, and delivery preparation.

These agents are intentionally narrow.

---

## 5. Design Philosophy

The system is built on five principles:

### Fail-Closed
Ambiguity should stop the workflow, not be smoothed over.

### Human-in-the-Loop
The system may draft, summarize, route, and validate.  
The operator approves.

### Artifact-First
Artifacts outrank summaries.

### Least Privilege
Each agent should have only the minimum necessary permissions.

### Evidence Before Expression
No external-facing claim should appear without support.

This system is **not** being optimized for autonomy.

It is being optimized for **controlled execution**.

---

## 6. Source of Truth

The source of truth for the agent system is:

`docs/agent_system/v1/`

This directory contains:

- `mnemosyne_agent_system_v1_index.md`
- `mnemosyne_agent_system_v1_executive_summary.md`
- `agent_architecture_v1.md`
- `agent_contracts_v1.md`
- `agent_workflows_v1.md`
- `agent_memory_model_v1.md`
- `agent_telemetry_and_eval_v1.md`

If any brief, chat summary, PDF, scratch note, or older version conflicts with those files:

**`docs/agent_system/v1/` wins.**

This brief is contextual.  
The docs are constitutional.

---

## 7. Current State

At this point:

- the constitutional document set is written
- the directory structure is being normalized
- the implementation sprint has not yet begun
- the immediate goal is to start Sprint 1 in a narrow, disciplined way

This means the system is currently at:

**Architecture complete enough for review, not yet runtime-complete**

---

## 8. Current Implementation Boundary

The first implementation sprint is intentionally narrow.

### Sprint 1 Scope
Only these should become real runtime/code scaffolding now:

- repo scaffolding
- Commander skeleton
- Archivist skeleton
- schema stubs
- memory scaffolding
- telemetry/audit scaffolding
- minimal runbooks/prompts
- local self-tests

### Explicitly Out of Scope for Sprint 1
- Outreach runtime
- Pilot Ops runtime
- autonomous sending
- Gmail send integration
- Telegram send integration
- delivery automation
- Gate logic mutation
- taxonomy/schema mutation
- UE5 runtime mutation
- vector DB / embeddings / RAG
- speculative runtime complexity

The rule is:

**Commander + Archivist first. Everything else later.**

---

## 9. Deferred / Parked Work

The following items are intentionally deferred to preserve focus:

- Telegram approval path integration
- Gmail MCP connection
- `canonical_scene_manifest.json` v1
- Ollama PoC
- ComfyUI PoC
- additional UE5 / DCC PoCs beyond the verified Gate path
- pilot outreach targets such as Riot and Ubisoft
- demo video packaging for pilot presentation

These are reminders, not active scope.

They should not be pulled into Sprint 1 unless explicitly requested.

---

## 10. What Claude.ai Should Do

In this Project, Claude.ai should act as:

- architecture reviewer
- contradiction finder
- scope guardian
- simplification partner
- risk identifier
- sequencing advisor

Claude.ai should **not** default into implementation mode unless explicitly asked.

The default review behavior should be:

1. read the constitutional docs
2. identify contradictions or redundancy
3. identify overengineering risk
4. identify missing contracts or weak boundaries
5. pressure-test Sprint 1 scope discipline
6. recommend the cleanest next move

---

## 11. What Claude.ai Should Not Do

Claude.ai should not:

- assume autonomy is desirable
- widen Sprint 1
- collapse constitutional docs into one giant prompt
- invent missing states or workflows
- override source-of-truth docs with summaries
- recommend runtime complexity without necessity
- suggest product-core mutation from the agent layer
- treat deferred work as active work

If something is unclear, the correct behavior is:

**ask for clarification or mark as blocked — not improvise.**

---

## 12. What I Want Reviewed First

Before implementation begins, I want Claude.ai to review these questions:

### A. Architectural Soundness
Does the 4-agent structure make sense as a v1 operating layer around Mnemosyne?

### B. Scope Discipline
Is Sprint 1 narrow enough, or is it still too broad?

### C. Contract Integrity
Are the contracts strong enough to prevent false confidence, silent scope drift, and unsupported communication?

### D. Memory Integrity
Is the memory model clean, inspectable, and conservative enough for KS-level operator control?

### E. Telemetry Integrity
Are the proposed evaluation metrics sufficient to tell whether the agent layer is helping or harming operations?

### F. Sequencing
Is Commander + Archivist the correct first runtime move, before Outreach and Pilot Ops?

---

## 13. Preferred Output From Claude.ai

When reviewing this architecture, I want Claude.ai to respond in this structure:

1. **Direct verdict**
   - sound / partially sound / risky

2. **Strongest parts**
   - what is already correct

3. **Weakest parts**
   - where ambiguity or overdesign exists

4. **Hidden risk**
   - where the system might drift or fail silently

5. **Sprint 1 correction**
   - what to remove, tighten, or sequence differently

6. **Final recommendation**
   - exact next step before coding

No vague praise.  
No generic “looks good.”  
I want a real pressure test.

---

## 14. Evaluation Standard

The architecture should be judged against one question:

**Does this system increase speed without weakening trust?**

If the answer is yes, it is useful.

If it introduces ambiguity, hidden autonomy, or false readiness, it has failed regardless of how sophisticated it looks.

---

## 15. Final Position

Mnemosyne Agent System v1 is not being built to impress with autonomy.

It is being built to create:

- controlled continuity
- evidence-led execution
- approval discipline
- package correctness
- safer operational leverage for KS

The protocol remains the center.

The agent system exists to help the protocol operate cleanly in the real world.

**Architecture first.  
Runtime second.  
Trust remains explicit.  
Fail-closed remains non-negotiable.**
