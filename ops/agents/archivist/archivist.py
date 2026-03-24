"""
Archivist Agent — Sprint 1 Skeleton
Mnemosyne Agent System v1

Responsibilities (Sprint 1):
  - validate that referenced artifact paths exist on disk
  - build evidence summaries from real artifact refs
  - build lineage records
  - validate claims conservatively (artifacts-first)
  - escalate on missing, ambiguous, or unverifiable evidence
  - emit schema-valid audit events for every meaningful action

Must NOT:
  - rewrite source code
  - draft outreach
  - send messages
  - upgrade uncertain evidence to supported
  - use embeddings / vector DB / RAG
  - parse PDFs (unless available as plain text)
  - mutate Gate/taxonomy/policy

Source of truth:
  docs/agent_system/v1/agent_contracts_v1.md
  docs/agent_system/v1/archivist_write_permissions_addendum_v1.md
"""

import json
from pathlib import Path
from typing import List, Optional

from ops.agents.archivist.models import (
    AuditEvent,
    ClaimValidation,
    EscalationRecord,
    EvidenceSummary,
    LineageRecord,
    new_uuid,
    utc_now,
)


class Archivist:
    """
    Factual stabilizer for the Mnemosyne agent layer.

    Validates artifact refs, builds evidence summaries, validates claims.
    Escalates on missing or ambiguous evidence. Never upgrades weak evidence.
    Writes schema-valid audit events from the first action.
    """

    def __init__(self, repo_root: Optional[Path] = None) -> None:
        self.repo_root: Path = repo_root or Path(__file__).parents[3]
        self.audit_log_path: Path = self.repo_root / "telemetry" / "audits" / "audit_log.jsonl"
        self.lineage_path: Path = self.repo_root / "memory" / "lineage"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_task(self, task_envelope: dict) -> dict:
        """
        Dispatch a task envelope to the appropriate handler.

        Returns a result dict. Blocks on unknown or unsupported intents.
        """
        task_id = task_envelope.get("task_id", new_uuid())
        intent = task_envelope.get("intent", "")
        payload_refs: List[str] = task_envelope.get("payload_ref", [])

        if intent == "collect_evidence":
            return self.collect_evidence(task_id, payload_refs)
        elif intent == "validate_claims":
            claims: List[dict] = task_envelope.get("claims", [])
            return self.validate_claims(task_id, payload_refs, claims)
        elif intent == "collect_lineage":
            return self.collect_lineage(task_id, payload_refs)
        else:
            return self._block_task(
                task_id=task_id,
                action="task_blocked",
                reason=f"Intent '{intent}' is not handled by Archivist in Sprint 1.",
                error_code="unsupported_intent",
                inputs=[f"intent:{intent}"],
            )

    def collect_evidence(self, task_id: str, payload_refs: List[str]) -> dict:
        """
        Validate each artifact ref. Return evidence summary.
        Escalates if any ref is missing.
        """
        found = []
        missing = []

        for ref in payload_refs:
            path = self.repo_root / ref
            if path.exists():
                found.append(ref)
            else:
                missing.append(ref)

        if missing:
            esc = self._escalate(
                task_id=task_id,
                reason="artifact_missing",
                details=f"Missing artifact refs: {missing}",
            )
            audit = self._emit(AuditEvent(
                event_id=new_uuid(),
                timestamp_utc=utc_now(),
                agent="archivist",
                action="evidence_collection_escalated",
                task_id=task_id,
                inputs=payload_refs,
                outputs=[str(esc["path"].relative_to(self.repo_root))],
                approval_state="escalated",
                status="escalated",
                notes=f"Missing: {missing}",
                error_code="artifact_missing",
            ))
            return {
                "status": "escalated",
                "reason": f"Missing artifact refs: {missing}",
                "escalation": esc["record"],
                "audit_event_id": audit.event_id,
            }

        summary = EvidenceSummary(
            schema="evidence_summary_v1",
            task_id=task_id,
            timestamp_utc=utc_now(),
            validated_by="archivist",
            artifacts_found=found,
            artifacts_missing=[],
            status="complete" if found else "empty",
            notes=None,
        )

        audit = self._emit(AuditEvent(
            event_id=new_uuid(),
            timestamp_utc=utc_now(),
            agent="archivist",
            action="evidence_summary_created",
            task_id=task_id,
            inputs=payload_refs,
            outputs=[],
            approval_state="not_required",
            status="success",
            notes=f"Validated {len(found)} artifact refs.",
        ))

        return {
            "status": "success",
            "evidence_summary": summary.to_dict(),
            "audit_event_id": audit.event_id,
        }

    def validate_claims(
        self,
        task_id: str,
        payload_refs: List[str],
        claims: List[dict],
    ) -> dict:
        """
        Validate each claim against provided artifact refs.

        A claim is 'supported' only if an artifact exists AND the
        evidence_excerpt is provided in the claim dict. Otherwise blocked.
        """
        if not claims:
            return self._block_task(
                task_id=task_id,
                action="claim_validation_blocked",
                reason="No claims provided in task envelope.",
                error_code="empty_claims",
                inputs=payload_refs,
            )

        results = []
        for c in claims:
            claim_text = c.get("claim_text", "")
            artifact_ref = c.get("artifact_ref")
            evidence_excerpt = c.get("evidence_excerpt")
            lineage_ref = c.get("lineage_ref")

            # Check artifact exists
            artifact_exists = (
                artifact_ref is not None
                and (self.repo_root / artifact_ref).exists()
            )

            if artifact_exists and evidence_excerpt and lineage_ref:
                state = "supported"
                blocked_reason = None
            elif artifact_exists and evidence_excerpt:
                state = "partially_supported"
                blocked_reason = "lineage_ref missing — cannot fully verify provenance"
            elif not artifact_ref:
                state = "unsupported"
                blocked_reason = "No artifact_ref provided."
            elif not artifact_exists:
                state = "unsupported"
                blocked_reason = f"Artifact '{artifact_ref}' does not exist on disk."
            else:
                state = "insufficient_evidence"
                blocked_reason = "Artifact exists but evidence_excerpt not provided."

            cv = ClaimValidation(
                claim_id=new_uuid(),
                task_id=task_id,
                claim_text=claim_text,
                validation_state=state,
                validated_by="archivist",
                timestamp_utc=utc_now(),
                supporting_artifacts=[artifact_ref] if artifact_ref else [],
                evidence_excerpt=evidence_excerpt,
                lineage_ref=lineage_ref,
                blocked_reason=blocked_reason,
            )
            results.append(cv.to_dict())

        overall_status = "success" if all(
            r["validation_state"] in {"supported", "partially_supported"}
            for r in results
        ) else "blocked"

        audit = self._emit(AuditEvent(
            event_id=new_uuid(),
            timestamp_utc=utc_now(),
            agent="archivist",
            action="claim_validation_completed",
            task_id=task_id,
            inputs=payload_refs,
            outputs=[],
            approval_state="not_required",
            status=overall_status,
            notes=f"Validated {len(results)} claim(s). Overall: {overall_status}.",
        ))

        return {
            "status": overall_status,
            "claim_validations": results,
            "audit_event_id": audit.event_id,
        }

    def collect_lineage(self, task_id: str, payload_refs: List[str]) -> dict:
        """
        Map artifact chain for the given refs. Mark lineage complete only if
        all artifacts exist. Escalates on any missing link.
        """
        chain = []
        all_found = True

        for ref in payload_refs:
            path = self.repo_root / ref
            exists = path.exists()
            if not exists:
                all_found = False
            chain.append({"path": ref, "exists": exists, "role": "artifact"})

        blocked_reason: Optional[str] = None
        if not all_found:
            missing = [e["path"] for e in chain if not e["exists"]]
            blocked_reason = f"Lineage incomplete. Missing: {missing}"

        record = LineageRecord(
            lineage_id=new_uuid(),
            task_id=task_id,
            timestamp_utc=utc_now(),
            validated_by="archivist",
            artifact_chain=chain,
            lineage_complete=all_found,
            blocked_reason=blocked_reason,
        )

        lineage_file: Optional[Path] = None
        if all_found:
            self.lineage_path.mkdir(parents=True, exist_ok=True)
            lineage_file = self.lineage_path / f"{record.lineage_id}.json"
            lineage_file.write_text(json.dumps(record.to_dict(), indent=2))

        audit_status = "success" if all_found else "blocked"
        audit = self._emit(AuditEvent(
            event_id=new_uuid(),
            timestamp_utc=utc_now(),
            agent="archivist",
            action="lineage_record_created",
            task_id=task_id,
            inputs=payload_refs,
            outputs=[str(lineage_file.relative_to(self.repo_root))] if lineage_file else [],
            approval_state="not_required",
            status=audit_status,
            notes=blocked_reason or f"Lineage complete for {len(chain)} artifact(s).",
        ))

        result = {
            "status": audit_status,
            "lineage_record": record.to_dict(),
            "audit_event_id": audit.event_id,
        }
        if blocked_reason:
            result["reason"] = blocked_reason
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _escalate(self, task_id: str, reason: str, details: str) -> dict:
        esc = EscalationRecord(
            escalation_id=new_uuid(),
            task_id=task_id,
            agent="archivist",
            reason=reason,
            details=details,
            timestamp_utc=utc_now(),
            status="open",
        )
        esc_path = self.repo_root / "memory" / "approvals" / f"esc_{esc.escalation_id}.json"
        esc_path.parent.mkdir(parents=True, exist_ok=True)
        esc_path.write_text(json.dumps(esc.to_dict(), indent=2))
        return {"record": esc.to_dict(), "path": esc_path}

    def _block_task(
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
            agent="archivist",
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

    def _emit(self, event: AuditEvent) -> AuditEvent:
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.audit_log_path.open("a") as f:
            f.write(json.dumps(event.to_dict()) + "\n")
        return event
