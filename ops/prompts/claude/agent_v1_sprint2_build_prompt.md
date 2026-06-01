# Sprint 2 Build Prompt — Real Commander ↔ Archivist Workflows Only

Read `CLAUDE.md` first.

**Status:** Sprint 1 accepted  
**Current Target:** Sprint 2  
**Scope Mode:** Commander ↔ Archivist only  
**Operating Mode:** Fail-closed, schema-disciplined, real-artifact grounded

You are implementing **Sprint 2** of the internal **Mnemosyne Agent System**.

Sprint 1 is already accepted.  
Your job in Sprint 2 is to implement and validate **real Commander ↔ Archivist workflows only**, under strict scope control.

---

## 1. Mission

Build the next thin, real slice of the system so that:

- **Commander** can orchestrate a bounded run
- **Archivist** can inspect and register **real artifacts**
- **Archivist** can emit **schema-valid `claim_validation_v1` payloads**
- the system emits **structured, schema-backed Session Memory and Artifact Memory write payloads**
- every meaningful action continues to emit **schema-valid audit events**
- the workflow is exercised using **real file refs from existing exported artifacts**
- the implementation remains **strictly fail-closed**
- no inactive agent or future runtime is accidentally activated

This sprint is **not** about building the full agent system.  
This sprint is about proving the **real operational handshake** between Commander and Archivist using real artifacts, claim validation, audit continuity, and schema discipline.

---

## 2. Source of Truth

Treat the following as authoritative, in this order:

1. `CLAUDE.md`
2. `docs/agent_system/v1/`
3. `ops/schemas/`

Important interpretation:

- `CLAUDE.md` is the constitutional operating instruction set.
- `docs/agent_system/v1/` defines the intended agent behavior and architectural truth.
- `ops/schemas/` contains shared runtime contracts and validation structures.
- Do **not** invert that relationship.
- Do **not** redefine the architecture around schema convenience.
- Do **not** prioritize implementation ease over architectural truth.

If ambiguity appears, resolve it in favor of:

1. fail-closed behavior
2. `CLAUDE.md`
3. architecture docs
4. explicit schema contracts
5. minimal implementation surface
6. verifiable real-flow evidence over abstraction

---

## 3. Active vs Inactive Scope

### Active in Sprint 2
Only these are in scope:

- **Commander**
- **Archivist**

### Explicitly inactive in Sprint 2
These must remain inactive:

- **Outreach**
- **Pilot Ops**

### Special rule: Gmail Draft
`Gmail Draft` must remain:

- **INERT_UNTIL_OUTREACH_RUNTIME**

That means:

- no live draft sending behavior
- no outreach execution path
- no hidden activation
- no “temporary” shortcut that bypasses this rule
- no accidental runtime wiring into inactive agents

If any dependency touches outreach behavior, stub or isolate it.  
Do not activate future runtime layers.

---

## 4. Critical Scope Lock

This sprint is only for **real Commander ↔ Archivist workflows**.

Specifically:

- Commander may create and run a bounded session
- Commander may pass real artifact refs into Archivist
- Archivist may inspect and normalize those refs
- Archivist may emit:
  - schema-valid artifact registration outputs
  - schema-valid `claim_validation_v1` payloads
  - schema-valid Artifact Memory write payloads
- Commander may assemble schema-valid Session Memory write payloads
- the workflow may emit schema-valid audit events exactly as enforced in Sprint 1
- memory persistence internals may be scaffolded only as needed to support contract-valid outputs

Do **not** expand this sprint into:

- multi-agent orchestration beyond Commander + Archivist
- outreach execution
- pilot operations logic
- autonomous planning loops
- generalized agent autonomy
- speculative memory intelligence
- production-scale persistence expansion beyond the necessary scaffold
- architectural beautification that is not needed to prove the real slice

---

## 5. Real File Refs Requirement (Critical)

For all self-tests, demos, workflow validation, and local harness execution in Sprint 2, you must **STRICTLY use existing real artifacts**.

Use only files inside:

- `exports/pilot_demo_v1/01_PASS_SCENARIO/`
- `exports/pilot_demo_v1/02_FAIL_SCENARIO/`

This is a hard requirement.

### Forbidden
Do **not**:

- invent placeholder files
- generate fake test artifacts such as `test_doc_1.txt`
- fabricate “real refs”
- simulate real refs with temporary stand-ins
- silently substitute missing artifacts with self-authored fixtures
- create false positives by validating against artifacts created during the run
- use files outside the required export folders unless explicitly already part of the accepted Sprint 1 path and clearly justified in the report

### Required behavior
If expected artifacts are missing, inconsistent, unreadable, unsupported, or insufficient:

- report it explicitly
- fail closed
- state exactly what is missing
- do not paper over the gap
- do not continue as though validation succeeded

---

## 6. Hidden Failure Modes to Prevent

You must explicitly defend against the following:

### A. False-positive validation via synthetic artifacts
The implementation must not “pass” by creating its own dummy files, substitute fixtures, or fake refs.

### B. Silent scope creep
The implementation must not quietly activate:

- Outreach
- Pilot Ops
- Gmail Draft runtime behavior
- future persistence behavior not required for Sprint 2
- extra orchestration layers beyond Commander ↔ Archivist

### C. Schema drift
The implementation must not emit ad hoc JSON blobs that merely “look right.”

The following must be explicit schema-backed outputs:

- Session Memory write payloads
- Artifact Memory write payloads
- `claim_validation_v1`
- audit events

### D. Soft-fail behavior
If artifact inspection fails, schema validation fails, required refs are missing, or claim validation cannot be grounded in real artifacts, the system must not continue as though the run succeeded.

### E. Audit regression
Sprint 2 must not regress the audit discipline established in Sprint 1.

Every meaningful action must continue to emit schema-valid audit events to:

- `telemetry/audits/audit_log.jsonl`

exactly as enforced in Sprint 1.

---

## 7. Sprint 2 Deliverable Goal

At the end of Sprint 2, we should be able to demonstrate a bounded run where:

1. Commander starts a real session
2. Commander references real artifacts from the required export folders
3. Archivist inspects those artifact refs
4. Archivist emits structured artifact registration outputs
5. Archivist emits a schema-valid `claim_validation_v1` payload grounded in those real artifacts
6. Archivist emits schema-valid Artifact Memory write payloads
7. Commander receives the Archivist outputs
8. Commander emits a schema-valid Session Memory write payload
9. every meaningful action emits a schema-valid audit event
10. PASS and FAIL scenarios are both replayable locally
11. the entire path remains fail-closed and bounded
12. inactive agents remain inactive

This sprint should prove that the **artifact handling path, claim validation path, memory contract path, and audit continuity path are real**, not imaginary.

---

## 8. Sprint 2 Tasks to Implement

Implement the **minimum** set of changes necessary to prove the real slice.

### Task 1 — Read and align to constitutional sources
Before coding:

- read `CLAUDE.md`
- inspect `docs/agent_system/v1/`
- inspect `ops/schemas/`
- confirm the actual Sprint 1 scaffolding state
- do not assume architecture from code convenience alone

### Task 2 — Inspect the real artifacts
Inspect the actual exported artifacts under:

- `exports/pilot_demo_v1/01_PASS_SCENARIO/`
- `exports/pilot_demo_v1/02_FAIL_SCENARIO/`

Determine:

- what files exist
- which refs are valid for Archivist inspection
- what minimum metadata can be extracted
- what can support grounded `claim_validation_v1`

Do not fabricate around gaps.

### Task 3 — Finalize schema-backed output contracts
Define or finalize explicit schema-backed structures for:

- Session Memory write payload
- Artifact Memory write payload
- `claim_validation_v1`
- audit events used by Sprint 2 actions

These structures must be real, validated, and stable enough for later persistence/runtime expansion.

### Task 4 — Build the minimal Commander → Archivist workflow
Implement the narrowest real workflow where:

- Commander opens a bounded run/session
- Commander passes real artifact refs
- Archivist inspects those refs
- Archivist emits schema-valid outputs
- Commander assembles the session-level output
- failure anywhere stops the run

Do not generalize this into a broader orchestration framework.

### Task 5 — Implement grounded claim validation
Archivist must produce **schema-valid `claim_validation_v1`** based only on the real artifacts used in the run.

That means:

- no hallucinated evidence
- no fabricated claims
- no “best effort” soft inference when evidence is missing
- explicit failure when grounding is insufficient

### Task 6 — Wire memory write payload generation
The system must emit real schema-valid write payloads for:

- Session Memory
- Artifact Memory

Persistence internals may remain scaffolded if not yet in scope, but payload generation and validation must already be real.

### Task 7 — Preserve audit continuity
Every meaningful action in Sprint 2 **MUST** continue to emit schema-valid audit events to:

- `telemetry/audits/audit_log.jsonl`

exactly as enforced in Sprint 1.

This includes, at minimum:

- session start
- artifact inspection attempts
- claim validation outcomes
- memory payload generation
- hard failures / fail-closed stops
- PASS / FAIL scenario completion outcomes

Stub logging does not count.

### Task 8 — Add fail-closed validation and error handling
If any of the following break:

- required real refs
- schema validation
- supported artifact inspection
- grounded claim validation
- memory payload construction
- audit event emission

the system must stop with a hard failure and surface the exact reason.

### Task 9 — Build a replayable local workflow harness
Create a **replayable local workflow harness** for Sprint 2 that can run locally against:

- one real PASS scenario
- one real FAIL scenario

Requirements:

- uses only the required export folders
- does not depend on network access
- clearly shows PASS vs FAIL behavior
- clearly shows what artifact refs were used
- clearly shows what outputs were emitted
- clearly shows where fail-closed logic triggered

This harness is part of the proof, not an optional convenience.

### Task 10 — Report exact evidence honestly
At the end, report:

- what was implemented
- which files changed
- which real artifact refs were used
- which schema-backed outputs were produced
- what passed
- what failed
- what remains unfinished

Do not disguise unfinished work.

---

## 9. Implementation Requirements

### 9.1 Commander
Commander should:

- initiate a bounded session/run
- track run/session identifiers
- pass real artifact refs into Archivist
- receive structured Archivist outputs
- assemble schema-valid Session Memory write payloads
- stop on validation failure or inspection failure
- remain operationally narrow

Commander must **not** become a general autonomous planner in this sprint.

### 9.2 Archivist
Archivist should:

- accept real artifact refs
- inspect and normalize those refs
- extract the minimum metadata required
- emit schema-valid artifact registration outputs
- emit schema-valid Artifact Memory write payloads
- emit schema-valid `claim_validation_v1`
- fail closed if refs are invalid, missing, unreadable, unsupported, or out of scope

Archivist must operate only on the actual files provided by the required export folders.

### 9.3 Memory write contracts
This sprint must establish structured, validated write payloads for:

- Session Memory
- Artifact Memory

Interpretation:

- payload structures must be real
- validation must be real
- interfaces/hooks may be scaffolded
- persistence internals may remain minimal/inert if not yet in scope

But the payload shape must already be good enough that Sprint 3+ can plug in real persistence without redefining the contract.

### 9.4 Validation
Use explicit schema validation for all relevant structures, including at minimum:

- task/session envelope validation
- artifact memory payload validation
- session memory payload validation
- `claim_validation_v1` validation
- audit event validation

If validation fails:

- return a hard failure
- surface the exact reason
- do not silently coerce invalid structures into passing

---

## 10. Suggested Work Order

Use this order unless the repo structure forces a safer equivalent:

1. Read `CLAUDE.md`
2. Inspect current Sprint 1 scaffolding
3. Locate authoritative docs under `docs/agent_system/v1/`
4. Identify relevant schemas under `ops/schemas/`
5. Inspect real artifacts under:
   - `exports/pilot_demo_v1/01_PASS_SCENARIO/`
   - `exports/pilot_demo_v1/02_FAIL_SCENARIO/`
6. Finalize schema-backed structures for:
   - Session Memory write payload
   - Artifact Memory write payload
   - `claim_validation_v1`
   - audit events
7. Implement the minimal Commander → Archivist workflow
8. Wire artifact inspection to real refs only
9. Add grounded claim validation
10. Add fail-closed validation and error handling
11. Confirm audit continuity to `telemetry/audits/audit_log.jsonl`
12. Build the replayable local workflow harness
13. Run bounded local self-tests using only the required export folders
14. Report exact outputs, failures, and remaining gaps honestly

---

## 11. Acceptance Criteria

Sprint 2 is acceptable only if **all** of the following are true:

### Scope control
- Only Commander and Archivist are active
- Outreach remains inactive
- Pilot Ops remains inactive
- Gmail Draft remains `INERT_UNTIL_OUTREACH_RUNTIME`

### Real artifacts
- Tests and demo paths use only real file refs from:
  - `exports/pilot_demo_v1/01_PASS_SCENARIO/`
  - `exports/pilot_demo_v1/02_FAIL_SCENARIO/`
- No fabricated stand-in artifacts are used

### Schema discipline
- Session Memory write payloads are schema-backed
- Artifact Memory write payloads are schema-backed
- `claim_validation_v1` payloads are schema-backed
- audit events are schema-backed
- validation is real and enforced

### Claim validation
- `claim_validation_v1` is grounded in real artifacts
- unsupported or insufficient evidence causes hard failure
- no ungrounded claims are emitted as success

### Audit continuity
- every meaningful action emits schema-valid audit events
- audit events are appended to `telemetry/audits/audit_log.jsonl`
- audit behavior continues exactly as enforced in Sprint 1

### Replayable proof
- there is a local replayable harness
- PASS scenario behavior can be replayed
- FAIL scenario behavior can be replayed
- the difference between PASS and FAIL is explicit and evidenced

### Fail-closed behavior
- invalid refs, invalid schemas, failed inspections, ungrounded claims, or audit failures produce hard failures
- the system does not silently continue after broken intermediate states

### Evidence
- the implementation reports which real artifact refs were used
- the implementation shows the exact schema-backed outputs produced
- the implementation clearly distinguishes PASS vs FAIL scenario behavior where applicable

---

## 12. Non-Goals

The following are explicitly out of scope for Sprint 2:

- full multi-agent runtime
- Outreach activation or execution
- Pilot Ops activation
- Gmail draft generation/send flow
- generalized long-horizon planning
- broad autonomous planning loops
- advanced persistence engine work beyond needed scaffolding
- broad refactors for elegance alone
- speculative abstractions for future sprints not needed now
- any fake demo path that creates the illusion of progress

Do not spend time polishing future architecture at the expense of proving the real Commander ↔ Archivist slice.

---

## 13. Required Output Format

Return your work as a single structured result under:

# Sprint 2 Result

## A. Scope confirmation
State exactly what you treated as:

- source of truth
- active scope
- inactive scope

## B. Repo changes
List the files added/changed and why.

## C. Workflow summary
Describe the implemented Commander ↔ Archivist path.

## D. Real artifact evidence
List the actual artifact refs used from:

- `exports/pilot_demo_v1/01_PASS_SCENARIO/`
- `exports/pilot_demo_v1/02_FAIL_SCENARIO/`

## E. Schema-backed outputs
Show the produced structures for:

- Session Memory write payload
- Artifact Memory write payload
- `claim_validation_v1`

## F. Audit evidence
Show:

- where audit events were emitted
- which meaningful actions were logged
- confirmation that events were appended to `telemetry/audits/audit_log.jsonl`

## G. Replayable local harness
Show:

- how the PASS scenario is executed
- how the FAIL scenario is executed
- how outputs differ
- where fail-closed behavior appears

## H. Validation / self-test results
Show:

- what passed
- what failed
- why failures failed
- whether fail-closed behavior worked correctly

## I. Remaining gaps
List only the real gaps that remain for Sprint 3.

Do not disguise unfinished work.

---

## 14. Hard Rules

1. Do not fabricate artifacts.
2. Do not widen scope.
3. Do not activate inactive agents.
4. Do not bypass schema validation.
5. Do not hide failures.
6. Do not optimize for appearance over truth.
7. If a required real artifact is missing, say so and fail closed.
8. Every meaningful action in Sprint 2 **MUST** continue to emit schema-valid audit events to `telemetry/audits/audit_log.jsonl`, exactly as enforced in Sprint 1.
9. `claim_validation_v1` must be grounded only in real inspected artifacts.
10. If you encounter a design choice between **more abstraction** and **more verifiable real-flow evidence**, always choose the latter.

---

## 15. Operating Principle

The goal of Sprint 2 is not to create the illusion of progress.

The goal is to prove that the system can perform a **real, bounded, schema-disciplined Commander ↔ Archivist run** using **real exported artifacts**, while preserving:

- fail-closed integrity
- audit continuity
- grounded claim validation
- inert future runtimes
- stable memory contracts

Build the **smallest implementation that proves that truth**.

---

**Commit signature for this sprint:**  
`Sprint 2 = real refs, real claims, real audits, fail-closed truth.`