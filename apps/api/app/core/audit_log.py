import hashlib
import hmac
import json
import uuid
from datetime import UTC, datetime

from sqlmodel import Session, select

from app.core.config import settings
from app.models import AuditEvent


def _compute_hash(entry: dict, prev_hash: str) -> str:
    key = settings.AUDIT_SECRET_KEY.encode()
    payload = json.dumps({**entry, "prev_hash": prev_hash}, sort_keys=True)
    return hmac.new(key, payload.encode(), hashlib.sha256).hexdigest()


def append_event(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    actor: str,
    action: str,
    target_type: str,
    target_id: str,
    metadata: dict | None = None,
    decision: str = "allow",
) -> AuditEvent:
    last = db.exec(
        select(AuditEvent)
        .where(AuditEvent.workspace_id == workspace_id)
        .order_by(AuditEvent.created_at.desc())  # type: ignore[arg-type]
        .limit(1)
    ).first()
    prev_hash = last.hash if last else "genesis"

    entry: dict = {
        "actor": actor,
        "action": action,
        "target_type": target_type,
        "target_id": target_id,
        "decision": decision,
        "metadata": metadata or {},
        "timestamp": datetime.now(UTC).isoformat(),
    }
    event_hash = _compute_hash(entry, prev_hash)

    event = AuditEvent(
        workspace_id=workspace_id,
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        decision=decision,
        metadata_json=json.dumps(metadata or {}),
        created_at=datetime.now(UTC),
        hash=event_hash,
        prev_hash=prev_hash,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def verify_chain(db: Session, workspace_id: uuid.UUID) -> bool:
    events = db.exec(
        select(AuditEvent)
        .where(AuditEvent.workspace_id == workspace_id)
        .order_by(AuditEvent.created_at.asc())  # type: ignore[arg-type]
    ).all()

    prev_hash = "genesis"
    for event in events:
        entry: dict = {
            "actor": event.actor,
            "action": event.action,
            "target_type": event.target_type,
            "target_id": event.target_id,
            "decision": event.decision,
            "metadata": json.loads(event.metadata_json or "{}"),
            "timestamp": event.created_at.isoformat(),
        }
        expected = _compute_hash(entry, prev_hash)
        if expected != event.hash:
            return False
        prev_hash = event.hash
    return True
