"""Session management — thin wrapper used by stream routes."""
from __future__ import annotations

import uuid

from sqlmodel import Session, select

from app.models import StreamSession


def get_active_sessions(db: Session, device_id: uuid.UUID) -> list[StreamSession]:
    return list(db.exec(
        select(StreamSession).where(
            StreamSession.device_id == device_id,
            StreamSession.status == "active",
        )
    ).all())
