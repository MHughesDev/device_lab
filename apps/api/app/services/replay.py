# replay.py — Replay service: session timelines, evidence detail, recipe draft generation
from __future__ import annotations
import uuid
from sqlmodel import Session, select
from app.models import AuditEvent, Evidence, Artifact, TimelineEvent


def build_session_timeline(
    db: Session,
    workspace_id: uuid.UUID,
    session_id: str,
) -> list[TimelineEvent]:
    """Return all Evidence records for the session ordered by created_at ascending."""
    records = db.exec(
        select(Evidence).where(Evidence.session_id == session_id).order_by(Evidence.created_at)
    ).all()

    events: list[TimelineEvent] = []
    for ev in records:
        artifact_rows = db.exec(
            select(Artifact).where(Artifact.evidence_id == ev.id)
        ).all()
        events.append(TimelineEvent(
            timestamp=ev.created_at,
            event_type="action",
            evidence_id=str(ev.id),
            tool=ev.mcp_tool,
            params_summary=ev.request_payload_json,
            before_screen_version=ev.before_screen_version,
            after_screen_version=ev.after_screen_version,
            artifact_refs=[str(a.id) for a in artifact_rows],
        ))
    return events


def build_evidence_detail(
    db: Session,
    evidence_id: uuid.UUID,
) -> dict:
    """Return Evidence record + observation refs + artifact list."""
    ev = db.get(Evidence, evidence_id)
    if not ev:
        return {}
    artifact_rows = db.exec(
        select(Artifact).where(Artifact.evidence_id == evidence_id)
    ).all()
    return {
        "id": str(ev.id),
        "session_id": ev.session_id,
        "device_id": str(ev.device_id),
        "mcp_tool": ev.mcp_tool,
        "policy_decision": ev.policy_decision,
        "before_screen_version": ev.before_screen_version,
        "after_screen_version": ev.after_screen_version,
        "observation_before": ev.observation_before_ref,
        "observation_after": ev.observation_after_ref,
        "created_at": ev.created_at.isoformat(),
        "artifact_refs": [str(a.id) for a in artifact_rows],
    }


def replay_as_recipe_draft(
    db: Session,
    evidence_id: uuid.UUID,
) -> str:
    """Fetch Evidence and produce a single-step recipe YAML draft."""
    from app.services.recipes.recorder import build_recipe_draft
    ev = db.get(Evidence, evidence_id)
    if not ev:
        raise ValueError(f"Evidence {evidence_id} not found")
    return build_recipe_draft([ev])
