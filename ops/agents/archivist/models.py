"""
Archivist Agent — Shared Models
Sprint 1 / Mnemosyne Agent System v1

Source of truth: docs/agent_system/v1/agent_contracts_v1.md
"""

from dataclasses import dataclass
from typing import List, Optional

# Re-export shared constants from commander models to avoid duplication
from ops.agents.commander.models import (  # noqa: F401
    ALLOWED_AGENTS,
    SPRINT1_ACTIVE_AGENTS,
    VALID_APPROVAL_STATES,
    VALID_AUDIT_STATUSES,
    AuditEvent,
    TaskEnvelope,
    new_uuid,
    utc_now,
)


# ---------------------------------------------------------------------------
# Claim Validation States (agent_contracts_v1.md §11.2)
# ---------------------------------------------------------------------------

VALID_CLAIM_STATES = frozenset({
    "supported",
    "partially_supported",
    "unsupported",
    "unclear",
    "blocked",
    "insufficient_evidence",
    "escalated",
})


# ---------------------------------------------------------------------------
# Evidence Summary
# ---------------------------------------------------------------------------

@dataclass
class EvidenceSummary:
    schema: str
    task_id: str
    timestamp_utc: str
    validated_by: str
    artifacts_found: List[str]
    artifacts_missing: List[str]
    status: str  # "complete" | "partial" | "empty"
    notes: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "schema": self.schema,
            "task_id": self.task_id,
            "timestamp_utc": self.timestamp_utc,
            "validated_by": self.validated_by,
            "artifacts_found": self.artifacts_found,
            "artifacts_missing": self.artifacts_missing,
            "status": self.status,
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# Claim Validation
# ---------------------------------------------------------------------------

@dataclass
class ClaimValidation:
    claim_id: str
    task_id: str
    claim_text: str
    validation_state: str
    validated_by: str
    timestamp_utc: str
    supporting_artifacts: List[str]
    evidence_excerpt: Optional[str] = None
    lineage_ref: Optional[str] = None
    blocked_reason: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "claim_id": self.claim_id,
            "task_id": self.task_id,
            "claim_text": self.claim_text,
            "validation_state": self.validation_state,
            "validated_by": self.validated_by,
            "timestamp_utc": self.timestamp_utc,
            "supporting_artifacts": self.supporting_artifacts,
            "evidence_excerpt": self.evidence_excerpt,
            "lineage_ref": self.lineage_ref,
            "blocked_reason": self.blocked_reason,
        }


# ---------------------------------------------------------------------------
# Lineage Record
# ---------------------------------------------------------------------------

@dataclass
class LineageRecord:
    lineage_id: str
    task_id: str
    timestamp_utc: str
    validated_by: str
    artifact_chain: List[dict]  # [{path, exists, role}]
    lineage_complete: bool
    blocked_reason: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "lineage_id": self.lineage_id,
            "task_id": self.task_id,
            "timestamp_utc": self.timestamp_utc,
            "validated_by": self.validated_by,
            "artifact_chain": self.artifact_chain,
            "lineage_complete": self.lineage_complete,
            "blocked_reason": self.blocked_reason,
        }


# ---------------------------------------------------------------------------
# Escalation Record
# ---------------------------------------------------------------------------

@dataclass
class EscalationRecord:
    escalation_id: str
    task_id: str
    agent: str
    reason: str
    details: str
    timestamp_utc: str
    status: str  # "open" | "resolved" | "rejected" | "blocked"
    operator_ref: Optional[str] = None
    resolution_note: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "escalation_id": self.escalation_id,
            "task_id": self.task_id,
            "agent": self.agent,
            "reason": self.reason,
            "details": self.details,
            "timestamp_utc": self.timestamp_utc,
            "status": self.status,
            "operator_ref": self.operator_ref,
            "resolution_note": self.resolution_note,
        }
