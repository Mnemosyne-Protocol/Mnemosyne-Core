"""
Commander Agent — Sprint 1 Skeleton
Mnemosyne Agent System v1

Responsibilities (Sprint 1):
  - intake operator intent
  - create and validate task envelopes
  - route to archivist only
  - produce approval request stubs
  - produce status summary stubs
  - emit schema-valid audit events for every meaningful action
  - fail closed on invalid intent or missing approval state

Must NOT (enforced):
  - send external email         → INERT_UNTIL_OUTREACH_RUNTIME
  - push to git                 → forbidden
  - delete files                → forbidden
  - mutate Gate/taxonomy/policy → forbidden
  - route to outreach/pilot_ops → not active in Sprint 1

Source of truth: docs/agent_system/v1/agent_contracts_v1.md
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from ops.agents.commander.models import (
    ALLOWED_AGENTS,
    INTENT_TO_OUTPUT,
    SPRINT1_ACTIVE_AGENTS,
    SPRINT1_VALID_INTENTS,
    VALID_AUDIT_STATUSES,
    VALID_OUTPUT_TYPES,
    VALID_PRIORITIES,
    AuditEvent,
    TaskEnvelope,
    new_uuid,
    utc_now,
)

# ---------------------------------------------------------------------------
# Inert capability declarations
# ---------------------------------------------------------------------------

# Gmail Draft is architecturally present but not active in Sprint 1.
# No code path may call this function until Outreach Runtime is enabled.
GMAIL_DRAFT_CAPABILITY = "INERT_UNTIL_OUTREACH_RUNTIME"

# Out-of-scope agents in Sprint 1 (routing to these is blocked)
SPRINT1_BLOCKED_AGENTS = frozenset({"outreach", "pilot_ops"})


# ---------------------------------------------------------------------------
# Commander
# ---------------------------------------------------------------------------

class Commander:
    """
    Orchestration and approval gateway for Sprint 1.

    Routes only to archivist. Fails closed on ambiguity.
    Writes schema-valid audit events from the first action.
    """

    GMAIL_DRAFT = GMAIL_DRAFT_CAPABILITY  # visible, explicitly inert

    def __init__(self, repo_root: Optional[Path] = None) -> None:
        self.repo_root: Path = repo_root or Path(__file__).parents[3]
        self.audit_log_path: Path = self.repo_root / "telemetry" / "audits" / "audit_log.jsonl"
        self.task_memory_path: Path = self.repo_root / "memory" / "tasks"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def intake(
        self,
        intent: str,
        payload_refs: Optional[List[str]] = None,
        required_output: Optional[str] = None,
        operator_context: Optional[dict] = None,
        priority: str = "normal",
        notes: Optional[str] = None,
    ) -> dict:
        """
        Process operator intent. Returns a result dict with status and task envelope.

        Returns:
            {"status": "success", "task_envelope": {...}, "audit_event_id": "..."}
            {"status": "blocked",  "reason": "...",        "audit_event_id": "..."}
        """
        task_id = new_uuid()
        payload_refs = payload_refs or []

        # Validate priority
        if priority not in VALID_PRIORITIES:
            return self._block(
                task_id=task_id,
                action="intake_blocked",
                reason=f"Invalid priority '{priority}'. Valid: {sorted(VALID_PRIORITIES)}",
                error_code="invalid_priority",
                inputs=[f"intent:{intent}", f"priority:{priority}"],
            )

        # Validate intent against Sprint 1 scope
        if intent not in SPRINT1_VALID_INTENTS:
            reason = (
                f"Intent '{intent}' is not valid for Sprint 1 Commander. "
                f"Valid Sprint 1 intents: {sorted(SPRINT1_VALID_INTENTS)}"
            )
            if intent in ALLOWED_AGENTS:
                reason += " — did you mean to pass a payload_ref instead of an agent name?"
            return self._block(
                task_id=task_id,
                action="intake_blocked",
                reason=reason,
                error_code="invalid_intent",
                inputs=[f"intent:{intent}"],
            )

        # Resolve required_output
        resolved_output = required_output or INTENT_TO_OUTPUT.get(intent, "evidence_summary_v1")
        if resolved_output not in VALID_OUTPUT_TYPES:
            return self._block(
                task_id=task_id,
                action="intake_blocked",
                reason=f"Unknown required_output '{resolved_output}'.",
                error_code="invalid_output_type",
                inputs=[f"intent:{intent}", f"required_output:{resolved_output}"],
            )

        # Build task envelope
        envelope = TaskEnvelope(
            task_id=task_id,
            from_agent="commander",
            to_agent="archivist",
            intent=intent,
            payload_ref=payload_refs,
            required_output=resolved_output,
            approval_state="not_required",
            priority=priority,
            timestamp_utc=utc_now(),
            correlation_id=new_uuid(),
            operator_context=operator_context,
            notes=notes,
        )

        task_path = self._save_task(envelope)

        audit = self._emit(AuditEvent(
            event_id=new_uuid(),
            timestamp_utc=utc_now(),
            agent="commander",
            action="task_created",
            task_id=task_id,
            inputs=payload_refs,
            outputs=[str(task_path.relative_to(self.repo_root))],
            approval_state="not_required",
            status="success",
            notes=f"intent={intent} routed to archivist",
        ))

        return {
            "status": "success",
            "task_envelope": envelope.to_dict(),
            "audit_event_id": audit.event_id,
        }

    def produce_approval_stub(
        self,
        task_id: str,
        summary: str,
        required_by: Optional[str] = None,
    ) -> dict:
        """
        Produce an approval request stub for operator review.
        Does NOT send anything. Operator must act manually.
        """
        stub_id = new_uuid()
        stub = {
            "schema": "approval_request_v1",
            "stub_id": stub_id,
            "task_id": task_id,
            "requested_by": "commander",
            "approval_state": "ready_for_review",
            "summary": summary,
            "required_by": required_by,
            "timestamp_utc": utc_now(),
            "note": "Operator action required. No autonomous send will occur.",
        }

        stub_path = self.repo_root / "memory" / "approvals" / f"{stub_id}.json"
        stub_path.parent.mkdir(parents=True, exist_ok=True)
        stub_path.write_text(json.dumps(stub, indent=2))

        self._emit(AuditEvent(
            event_id=new_uuid(),
            timestamp_utc=utc_now(),
            agent="commander",
            action="approval_stub_created",
            task_id=task_id,
            inputs=[],
            outputs=[str(stub_path.relative_to(self.repo_root))],
            approval_state="ready_for_review",
            status="success",
            notes=f"Approval stub {stub_id} awaiting operator review.",
        ))

        return {"status": "success", "approval_stub": stub, "path": str(stub_path)}

    def produce_status_summary(self, tasks: List[dict]) -> dict:
        """
        Produce a status summary over a list of task results.
        No external output. Operator-facing only.
        """
        summary_id = new_uuid()
        counts: Dict[str, int] = {"success": 0, "blocked": 0, "escalated": 0, "other": 0}
        for t in tasks:
            s = t.get("status", "other")
            if s in counts:
                counts[s] += 1
            else:
                counts["other"] += 1

        summary = {
            "schema": "status_summary_v1",
            "summary_id": summary_id,
            "generated_by": "commander",
            "timestamp_utc": utc_now(),
            "total_tasks": len(tasks),
            "counts": counts,
            "tasks": tasks,
        }

        self._emit(AuditEvent(
            event_id=new_uuid(),
            timestamp_utc=utc_now(),
            agent="commander",
            action="status_summary_produced",
            task_id=summary_id,
            inputs=[],
            outputs=[],
            approval_state="not_required",
            status="success",
            notes=f"Summary over {len(tasks)} tasks.",
        ))

        return {"status": "success", "status_summary": summary}

    # ------------------------------------------------------------------
    # Inert capability (explicitly blocked in Sprint 1)
    # ------------------------------------------------------------------

    def gmail_draft(self, *args, **kwargs) -> dict:  # noqa: ANN002, ANN003
        """
        INERT_UNTIL_OUTREACH_RUNTIME

        Gmail Draft capability is architecturally present but inactive in Sprint 1.
        Any call to this method is a contract violation and is blocked.
        """
        task_id = new_uuid()
        return self._block(
            task_id=task_id,
            action="gmail_draft_blocked",
            reason="Gmail Draft is INERT_UNTIL_OUTREACH_RUNTIME. "
                   "No email capability is active in Sprint 1.",
            error_code="INERT_UNTIL_OUTREACH_RUNTIME",
            inputs=list(args) + [str(k) for k in kwargs],
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _block(
        self,
        task_id: str,
        action: str,
        reason: str,
        error_code: str,
        inputs: Optional[List[str]] = None,
    ) -> dict:
        audit = self._emit(AuditEvent(
            event_id=new_uuid(),
            timestamp_utc=utc_now(),
            agent="commander",
            action=action,
            task_id=task_id,
            inputs=inputs or [],
            outputs=[],
            approval_state="blocked",
            status="blocked",
            notes=reason,
            error_code=error_code,
        ))
        return {
            "status": "blocked",
            "reason": reason,
            "task_id": task_id,
            "audit_event_id": audit.event_id,
        }

    def _save_task(self, envelope: TaskEnvelope) -> Path:
        self.task_memory_path.mkdir(parents=True, exist_ok=True)
        path = self.task_memory_path / f"{envelope.task_id}.json"
        path.write_text(json.dumps(envelope.to_dict(), indent=2))
        return path

    def _emit(self, event: AuditEvent) -> AuditEvent:
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.audit_log_path.open("a") as f:
            f.write(json.dumps(event.to_dict()) + "\n")
        return event
