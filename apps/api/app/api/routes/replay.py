# replay.py — Replay and audit-verify API routes
import uuid

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.core.audit_log import verify_chain
from app.models import AuditEvent, TimelineEvent, Workspace
from app.services import replay as replay_svc

router = APIRouter(tags=["replay"])


def _get_workspace(db) -> Workspace:
    ws = db.exec(select(Workspace).limit(1)).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not initialised")
    return ws


@router.get("/sessions/{session_id}/timeline", response_model=list[TimelineEvent])
def session_timeline(session_id: str, db: SessionDep, current_user: CurrentUser) -> list:
    ws = _get_workspace(db)
    return replay_svc.build_session_timeline(db, ws.id, session_id)


@router.get("/evidence/{evidence_id}")
def evidence_detail(evidence_id: uuid.UUID, db: SessionDep, current_user: CurrentUser) -> dict:
    detail = replay_svc.build_evidence_detail(db, evidence_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return detail


@router.post("/evidence/{evidence_id}/replay")
def replay_evidence(evidence_id: uuid.UUID, db: SessionDep, current_user: CurrentUser) -> dict:
    try:
        draft = replay_svc.replay_as_recipe_draft(db, evidence_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {
        "draft_yaml": draft,
        "warning": "This is a draft for human review only — do not execute without verification.",
    }


@router.get("/audit/verify")
def audit_verify(db: SessionDep, current_user: CurrentUser) -> dict:
    ws = _get_workspace(db)
    events = db.exec(
        select(AuditEvent).where(AuditEvent.workspace_id == ws.id).order_by(AuditEvent.created_at.asc())
    ).all()
    chain_length = len(events)
    first_broken_at: str | None = None

    from app.core.audit_log import _compute_hash
    import json
    prev_hash = "genesis"
    valid = True
    for event in events:
        entry = {
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
            valid = False
            first_broken_at = event.created_at.isoformat()
            break
        prev_hash = event.hash

    return {"valid": valid, "chain_length": chain_length, "first_broken_at": first_broken_at}
