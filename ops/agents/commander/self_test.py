"""
Commander Agent — Self-Test
Sprint 1 / Mnemosyne Agent System v1

Runs without network access. Uses a temporary directory for isolation.

Verified behaviors:
  T1  valid intent → task envelope created
  T2  invalid intent → blocked, audit event written
  T3  gmail_draft() → explicitly inert (INERT_UNTIL_OUTREACH_RUNTIME)
  T4  approval stub → written to memory/approvals/
  T5  status summary → produced
  T6  all actions emit schema-valid audit events
  T7  task envelope persisted to memory/tasks/
"""

import json
import sys
import tempfile
import traceback
from pathlib import Path

# Ensure repo root on sys.path for relative imports
_REPO_ROOT = Path(__file__).parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from ops.agents.commander.commander import Commander
from ops.agents.commander.models import (
    VALID_APPROVAL_STATES,
    VALID_AUDIT_STATUSES,
    SPRINT1_VALID_INTENTS,
)


# ---------------------------------------------------------------------------
# Audit event schema validation (mirrors agent_contracts_v1.md §8)
# ---------------------------------------------------------------------------

REQUIRED_AUDIT_FIELDS = {
    "event_id", "timestamp_utc", "agent", "action",
    "task_id", "inputs", "outputs", "approval_state", "status",
}


def assert_audit_schema(event: dict, label: str) -> None:
    missing = REQUIRED_AUDIT_FIELDS - set(event.keys())
    assert not missing, f"[{label}] Audit event missing fields: {missing}"
    assert event["agent"] in {"commander", "archivist", "outreach", "pilot_ops"}, \
        f"[{label}] Invalid agent: {event['agent']}"
    assert event["status"] in VALID_AUDIT_STATUSES, \
        f"[{label}] Invalid status: {event['status']}"
    assert event["approval_state"] in VALID_APPROVAL_STATES, \
        f"[{label}] Invalid approval_state: {event['approval_state']}"
    assert isinstance(event["inputs"], list), f"[{label}] inputs must be list"
    assert isinstance(event["outputs"], list), f"[{label}] outputs must be list"


def read_audit_events(audit_log: Path) -> list:
    if not audit_log.exists():
        return []
    events = []
    for line in audit_log.read_text().splitlines():
        line = line.strip()
        if line:
            events.append(json.loads(line))
    return events


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_valid_intent_creates_task_envelope(tmp: Path) -> None:
    """T1: collect_evidence produces a valid task envelope."""
    c = Commander(repo_root=tmp)
    result = c.intake(
        intent="collect_evidence",
        payload_refs=["docs/agent_system/v1/agent_contracts_v1.md"],
        priority="normal",
    )
    assert result["status"] == "success", f"Expected success, got: {result}"
    env = result["task_envelope"]
    assert env["intent"] == "collect_evidence"
    assert env["from_agent"] == "commander"
    assert env["to_agent"] == "archivist"
    assert env["required_output"] == "evidence_summary_v1"
    assert env["approval_state"] == "not_required"
    assert "task_id" in env
    assert "timestamp_utc" in env

    # Task file must be persisted
    task_file = tmp / "memory" / "tasks" / f"{env['task_id']}.json"
    assert task_file.exists(), f"Task file not found: {task_file}"
    persisted = json.loads(task_file.read_text())
    assert persisted["task_id"] == env["task_id"]


def test_invalid_intent_blocked(tmp: Path) -> None:
    """T2: Unknown intent is blocked with audit event."""
    c = Commander(repo_root=tmp)
    result = c.intake(intent="hack_the_gate", payload_refs=[])
    assert result["status"] == "blocked", f"Expected blocked, got: {result}"
    assert "invalid_intent" in result.get("reason", "") or \
           "not valid" in result.get("reason", ""), f"Unexpected reason: {result['reason']}"
    assert "audit_event_id" in result


def test_out_of_scope_sprint1_intent_blocked(tmp: Path) -> None:
    """T2b: Out-of-scope intent (draft_outreach) blocked in Sprint 1."""
    c = Commander(repo_root=tmp)
    result = c.intake(intent="draft_outreach", payload_refs=[])
    assert result["status"] == "blocked"


def test_gmail_draft_is_inert(tmp: Path) -> None:
    """T3: gmail_draft() must be explicitly inert."""
    c = Commander(repo_root=tmp)
    # The attribute must be flagged inert
    assert c.GMAIL_DRAFT == "INERT_UNTIL_OUTREACH_RUNTIME", \
        "GMAIL_DRAFT capability must be INERT_UNTIL_OUTREACH_RUNTIME"
    # Calling it must return blocked
    result = c.gmail_draft("test_arg")
    assert result["status"] == "blocked"
    assert "INERT_UNTIL_OUTREACH_RUNTIME" in result.get("reason", "")


def test_approval_stub_created(tmp: Path) -> None:
    """T4: produce_approval_stub writes a stub to memory/approvals/."""
    c = Commander(repo_root=tmp)
    result = c.produce_approval_stub(
        task_id="test-task-001",
        summary="Pilot demo package ready for review",
    )
    assert result["status"] == "success"
    stub = result["approval_stub"]
    assert stub["approval_state"] == "ready_for_review"
    assert stub["task_id"] == "test-task-001"
    stub_path = Path(result["path"])
    assert stub_path.exists(), f"Approval stub file not found: {stub_path}"


def test_status_summary_produced(tmp: Path) -> None:
    """T5: produce_status_summary returns a valid summary."""
    c = Commander(repo_root=tmp)
    tasks = [
        {"status": "success", "task_id": "t1"},
        {"status": "blocked", "task_id": "t2"},
        {"status": "success", "task_id": "t3"},
    ]
    result = c.produce_status_summary(tasks)
    assert result["status"] == "success"
    s = result["status_summary"]
    assert s["total_tasks"] == 3
    assert s["counts"]["success"] == 2
    assert s["counts"]["blocked"] == 1


def test_audit_events_schema_valid(tmp: Path) -> None:
    """T6: All commander actions emit schema-valid audit events."""
    c = Commander(repo_root=tmp)
    c.intake(intent="collect_evidence", payload_refs=[])
    c.intake(intent="unknown_intent", payload_refs=[])
    c.gmail_draft("blocked_call")
    c.produce_approval_stub(task_id="t-stub", summary="test")
    c.produce_status_summary([{"status": "success"}])

    events = read_audit_events(c.audit_log_path)
    assert len(events) >= 5, f"Expected >=5 audit events, got {len(events)}"
    for ev in events:
        assert_audit_schema(ev, label=ev.get("action", "unknown"))


def test_invalid_priority_blocked(tmp: Path) -> None:
    """T7: Invalid priority is rejected."""
    c = Commander(repo_root=tmp)
    result = c.intake(intent="collect_evidence", payload_refs=[], priority="turbo")
    assert result["status"] == "blocked"
    assert "priority" in result.get("reason", "").lower()


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

TESTS = [
    test_valid_intent_creates_task_envelope,
    test_invalid_intent_blocked,
    test_out_of_scope_sprint1_intent_blocked,
    test_gmail_draft_is_inert,
    test_approval_stub_created,
    test_status_summary_produced,
    test_audit_events_schema_valid,
    test_invalid_priority_blocked,
]


def main() -> int:
    passed = 0
    failed = 0

    print("=" * 60)
    print("Commander Self-Test — Sprint 1")
    print("=" * 60)

    for test_fn in TESTS:
        name = test_fn.__name__
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            # Provide minimal directory structure
            (tmp / "memory" / "tasks").mkdir(parents=True)
            (tmp / "memory" / "approvals").mkdir(parents=True)
            (tmp / "memory" / "lineage").mkdir(parents=True)
            (tmp / "telemetry" / "audits").mkdir(parents=True)
            try:
                test_fn(tmp)
                print(f"  PASS  {name}")
                passed += 1
            except Exception as e:  # noqa: BLE001
                print(f"  FAIL  {name}")
                print(f"        {e}")
                traceback.print_exc()
                failed += 1

    print("-" * 60)
    print(f"Result: {passed} passed, {failed} failed")
    print("=" * 60)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
