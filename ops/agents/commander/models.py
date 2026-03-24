"""
Commander Agent — Shared Models
Sprint 1 / Mnemosyne Agent System v1

Source of truth: docs/agent_system/v1/agent_contracts_v1.md
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import uuid
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Registry constants (from agent_contracts_v1.md §2, §5, §6, §7)
# ---------------------------------------------------------------------------

ALLOWED_AGENTS = frozenset({"commander", "archivist", "outreach", "pilot_ops"})

SPRINT1_ACTIVE_AGENTS = frozenset({"commander", "archivist"})

# Intents valid for Sprint 1 Commander → Archivist routing
SPRINT1_VALID_INTENTS = frozenset({
    "collect_evidence",
    "validate_claims",
    "collect_lineage",
    "summarize_status",
    "request_approval",
})

# Full v1 intent set (for reference; Sprint 1 rejects out-of-scope intents)
ALL_VALID_INTENTS = frozenset({
    "collect_evidence",
    "validate_claims",
    "draft_outreach",
    "prepare_package",
    "validate_package",
    "request_approval",
    "summarize_status",
    "collect_delivery_readiness",
    "collect_lineage",
    "redraft_message",
})

VALID_APPROVAL_STATES = frozenset({
    "not_required",
    "draft",
    "ready_for_review",
    "approved",
    "rejected",
    "blocked",
    "escalated",
    "delivered",
})

VALID_PRIORITIES = frozenset({"low", "normal", "high", "urgent"})

VALID_OUTPUT_TYPES = frozenset({
    "evidence_summary_v1",
    "claim_validation_v1",
    "artifact_lineage_v1",
    "outreach_draft_v1",
    "followup_draft_v1",
    "package_export_v1",
    "package_readiness_v1",
    "approval_request_v1",
    "status_summary_v1",
})

VALID_AUDIT_STATUSES = frozenset({"success", "failure", "blocked", "escalated", "rejected"})

# Default output type per intent
INTENT_TO_OUTPUT: Dict[str, str] = {
    "collect_evidence": "evidence_summary_v1",
    "validate_claims": "claim_validation_v1",
    "collect_lineage": "artifact_lineage_v1",
    "summarize_status": "status_summary_v1",
    "request_approval": "approval_request_v1",
    "draft_outreach": "outreach_draft_v1",
    "prepare_package": "package_export_v1",
    "validate_package": "package_readiness_v1",
    "collect_delivery_readiness": "package_readiness_v1",
    "redraft_message": "followup_draft_v1",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Task Envelope
# ---------------------------------------------------------------------------

@dataclass
class TaskEnvelope:
    task_id: str
    from_agent: str
    to_agent: str
    intent: str
    payload_ref: List[str]
    required_output: str
    approval_state: str
    priority: str
    timestamp_utc: str
    parent_task_id: Optional[str] = None
    correlation_id: Optional[str] = None
    operator_context: Optional[dict] = None
    constraints: Optional[List[str]] = None
    deadline_utc: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self) -> dict:
        d: dict = {
            "task_id": self.task_id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "intent": self.intent,
            "payload_ref": self.payload_ref,
            "required_output": self.required_output,
            "approval_state": self.approval_state,
            "priority": self.priority,
            "timestamp_utc": self.timestamp_utc,
        }
        if self.parent_task_id is not None:
            d["parent_task_id"] = self.parent_task_id
        if self.correlation_id is not None:
            d["correlation_id"] = self.correlation_id
        if self.operator_context is not None:
            d["operator_context"] = self.operator_context
        if self.constraints is not None:
            d["constraints"] = self.constraints
        if self.deadline_utc is not None:
            d["deadline_utc"] = self.deadline_utc
        if self.notes is not None:
            d["notes"] = self.notes
        return d


# ---------------------------------------------------------------------------
# Audit Event
# ---------------------------------------------------------------------------

@dataclass
class AuditEvent:
    event_id: str
    timestamp_utc: str
    agent: str
    action: str
    task_id: str
    inputs: List[str]
    outputs: List[str]
    approval_state: str
    status: str
    notes: Optional[str] = None
    error_code: Optional[str] = None
    operator_ref: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "timestamp_utc": self.timestamp_utc,
            "agent": self.agent,
            "action": self.action,
            "task_id": self.task_id,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "approval_state": self.approval_state,
            "status": self.status,
            "notes": self.notes,
            "error_code": self.error_code,
            "operator_ref": self.operator_ref,
        }
