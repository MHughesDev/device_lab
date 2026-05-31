import json
import uuid
from datetime import UTC, datetime

from sqlmodel import Session

from app.models import Evidence


def create_evidence(
    db: Session,
    *,
    session_id: str,
    device_id: uuid.UUID,
    mcp_tool: str,
    request_payload: dict,
    policy_decision: str = "allow",
    before_screen_version: int = 0,
    after_screen_version: int = 0,
    observation_before_ref: str | None = None,
    observation_after_ref: str | None = None,
    warnings: list[str] | None = None,
    audit_event_id: uuid.UUID | None = None,
) -> Evidence:
    # Redact any keys containing 'secret', 'password', 'token', 'key'
    safe_payload = {
        k: "***REDACTED***" if any(s in k.lower() for s in ("secret", "password", "token", "key")) else v
        for k, v in request_payload.items()
    }
    ev = Evidence(
        session_id=session_id,
        device_id=device_id,
        mcp_tool=mcp_tool,
        request_payload_json=json.dumps(safe_payload),
        policy_decision=policy_decision,
        before_screen_version=before_screen_version,
        after_screen_version=after_screen_version,
        observation_before_ref=observation_before_ref,
        observation_after_ref=observation_after_ref,
        warnings_json=json.dumps(warnings or []),
        audit_event_id=audit_event_id,
        created_at=datetime.now(UTC),
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev


def get_evidence(db: Session, evidence_id: uuid.UUID) -> Evidence | None:
    return db.get(Evidence, evidence_id)
