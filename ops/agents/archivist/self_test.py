"""
Archivist Agent — Self-Test
Sprint 1 / Mnemosyne Agent System v1

Runs without network access. Uses a temporary directory for isolation.

Verified behaviors:
  T1  existing artifact refs → evidence summary created
  T2  missing artifact refs → escalation triggered, blocked result
  T3  valid claims with evidence → supported
  T4  claims without artifact ref → unsupported
  T5  lineage complete → record persisted
  T6  lineage incomplete → blocked
  T7  unsupported intent → blocked
  T8  all actions emit schema-valid audit events
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

from ops.agents.archivist.archivist import Archivist
from ops.agents.commander.models import VALID_APPROVAL_STATES, VALID_AUDIT_STATUSES


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
    assert isinstance(event["inputs"], list)
    assert isinstance(event["outputs"], list)


def read_audit_events(audit_log: Path) -> list:
    if not audit_log.exists():
        return []
    events = []
    for line in audit_log.read_text().splitlines():
        line = line.strip()
        if line:
            events.append(json.loads(line))
    return events


def make_test_artifact(tmp: Path, rel_path: str, content: str = "test") -> str:
    """Create a real file in tmp and return the relative path string."""
    full = tmp / rel_path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content)
    return rel_path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_existing_refs_produce_evidence_summary(tmp: Path) -> None:
    """T1: All refs exist → evidence summary complete."""
    a = Archivist(repo_root=tmp)
    ref1 = make_test_artifact(tmp, "bench/out/pass_run.json", '{"verdict": "PASS"}')
    ref2 = make_test_artifact(tmp, "docs/faz9d4_report.md", "# Report")

    result = a.collect_evidence(task_id="t001", payload_refs=[ref1, ref2])
    assert result["status"] == "success", f"Unexpected: {result}"
    s = result["evidence_summary"]
    assert s["schema"] == "evidence_summary_v1"
    assert s["status"] == "complete"
    assert set(s["artifacts_found"]) == {ref1, ref2}
    assert s["artifacts_missing"] == []
    assert s["validated_by"] == "archivist"


def test_missing_refs_escalate(tmp: Path) -> None:
    """T2: Missing ref → escalation, blocked result."""
    a = Archivist(repo_root=tmp)
    ref_exists = make_test_artifact(tmp, "bench/out/pass_run.json", "{}")
    ref_missing = "bench/out/nonexistent_file.json"

    result = a.collect_evidence(task_id="t002", payload_refs=[ref_exists, ref_missing])
    assert result["status"] == "escalated", f"Unexpected: {result}"
    assert ref_missing in result.get("reason", "")
    esc = result["escalation"]
    assert esc["reason"] == "artifact_missing"
    assert esc["status"] == "open"
    assert esc["agent"] == "archivist"


def test_supported_claim_with_evidence(tmp: Path) -> None:
    """T3: Claim with artifact_ref, evidence_excerpt, lineage_ref → supported."""
    a = Archivist(repo_root=tmp)
    ref = make_test_artifact(tmp, "bench/out/faz9d4_report.json", '{"fps": 141.45}')
    lineage_ref = make_test_artifact(tmp, "memory/lineage/l1.json", '{"chain": []}')

    claims = [{
        "claim_text": "Gate achieves 141 fps",
        "artifact_ref": ref,
        "evidence_excerpt": '"fps": 141.45',
        "lineage_ref": lineage_ref,
    }]
    result = a.validate_claims(task_id="t003", payload_refs=[ref], claims=claims)
    assert result["status"] == "success", f"Unexpected: {result}"
    cv = result["claim_validations"][0]
    assert cv["validation_state"] == "supported"
    assert cv["validated_by"] == "archivist"


def test_claim_without_artifact_is_unsupported(tmp: Path) -> None:
    """T4: Claim with no artifact_ref → unsupported."""
    a = Archivist(repo_root=tmp)
    claims = [{"claim_text": "System is the best", "artifact_ref": None}]
    result = a.validate_claims(task_id="t004", payload_refs=[], claims=claims)
    assert result["status"] == "blocked"
    cv = result["claim_validations"][0]
    assert cv["validation_state"] == "unsupported"
    assert cv["blocked_reason"] is not None


def test_claim_missing_artifact_on_disk_is_unsupported(tmp: Path) -> None:
    """T4b: Claim with artifact_ref that does not exist → unsupported."""
    a = Archivist(repo_root=tmp)
    claims = [{
        "claim_text": "Some claim",
        "artifact_ref": "does/not/exist.json",
        "evidence_excerpt": "some excerpt",
        "lineage_ref": None,
    }]
    result = a.validate_claims(task_id="t004b", payload_refs=[], claims=claims)
    cv = result["claim_validations"][0]
    assert cv["validation_state"] == "unsupported"


def test_empty_claims_blocked(tmp: Path) -> None:
    """T4c: Empty claims list → blocked."""
    a = Archivist(repo_root=tmp)
    result = a.validate_claims(task_id="t004c", payload_refs=[], claims=[])
    assert result["status"] == "blocked"


def test_lineage_complete(tmp: Path) -> None:
    """T5: All refs exist → lineage complete, record persisted."""
    a = Archivist(repo_root=tmp)
    ref1 = make_test_artifact(tmp, "bench/out/pass.json", "{}")
    ref2 = make_test_artifact(tmp, "bench/out/fail.json", "{}")

    result = a.collect_lineage(task_id="t005", payload_refs=[ref1, ref2])
    assert result["status"] == "success"
    rec = result["lineage_record"]
    assert rec["lineage_complete"] is True
    assert len(rec["artifact_chain"]) == 2
    # Record must be persisted
    lineage_file = tmp / "memory" / "lineage" / f"{rec['lineage_id']}.json"
    assert lineage_file.exists(), f"Lineage file not found: {lineage_file}"


def test_lineage_incomplete_blocked(tmp: Path) -> None:
    """T6: Missing ref → lineage blocked, not persisted."""
    a = Archivist(repo_root=tmp)
    ref_exists = make_test_artifact(tmp, "bench/out/pass.json", "{}")
    ref_missing = "bench/out/missing.json"

    result = a.collect_lineage(task_id="t006", payload_refs=[ref_exists, ref_missing])
    assert result["status"] == "blocked"
    rec = result["lineage_record"]
    assert rec["lineage_complete"] is False
    assert rec["blocked_reason"] is not None
    # File must NOT be persisted for incomplete lineage
    lineage_file = tmp / "memory" / "lineage" / f"{rec['lineage_id']}.json"
    assert not lineage_file.exists(), "Incomplete lineage must not be persisted"


def test_unsupported_intent_blocked(tmp: Path) -> None:
    """T7: Unknown intent via process_task → blocked."""
    a = Archivist(repo_root=tmp)
    envelope = {
        "task_id": "t007",
        "intent": "draft_outreach",
        "payload_ref": [],
    }
    result = a.process_task(envelope)
    assert result["status"] == "blocked"


def test_all_actions_emit_valid_audit_events(tmp: Path) -> None:
    """T8: Every action writes at least one schema-valid audit event."""
    a = Archivist(repo_root=tmp)
    ref = make_test_artifact(tmp, "bench/out/x.json", "{}")
    ref_lin = make_test_artifact(tmp, "memory/lineage/l.json", "{}")

    a.collect_evidence("t-ev1", [ref])
    a.collect_evidence("t-ev2", ["missing/ref.json"])
    a.validate_claims("t-cv1", [ref], [{
        "claim_text": "x",
        "artifact_ref": ref,
        "evidence_excerpt": "{}",
        "lineage_ref": ref_lin,
    }])
    a.validate_claims("t-cv2", [], [])
    a.collect_lineage("t-ln1", [ref])
    a.collect_lineage("t-ln2", ["missing.json"])
    a.process_task({"task_id": "t-pi1", "intent": "bad_intent", "payload_ref": []})

    events = read_audit_events(a.audit_log_path)
    assert len(events) >= 7, f"Expected >=7 audit events, got {len(events)}"
    for ev in events:
        assert_audit_schema(ev, label=ev.get("action", "unknown"))


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

TESTS = [
    test_existing_refs_produce_evidence_summary,
    test_missing_refs_escalate,
    test_supported_claim_with_evidence,
    test_claim_without_artifact_is_unsupported,
    test_claim_missing_artifact_on_disk_is_unsupported,
    test_empty_claims_blocked,
    test_lineage_complete,
    test_lineage_incomplete_blocked,
    test_unsupported_intent_blocked,
    test_all_actions_emit_valid_audit_events,
]


def main() -> int:
    passed = 0
    failed = 0

    print("=" * 60)
    print("Archivist Self-Test — Sprint 1")
    print("=" * 60)

    for test_fn in TESTS:
        name = test_fn.__name__
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
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
