import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
import yaml
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel

from app.models import Evidence, Workspace


def _engine():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    return engine


def _make_workspace(db: Session) -> Workspace:
    ws = Workspace(id=uuid.uuid4(), name="test-ws", created_at=datetime.now(UTC), updated_at=datetime.now(UTC))
    db.add(ws)
    db.commit()
    db.refresh(ws)
    return ws


def _make_evidence(db, session_id, device_id, offset_seconds=0):
    ev = Evidence(
        session_id=session_id,
        device_id=device_id,
        mcp_tool="tap",
        created_at=datetime.now(UTC) + timedelta(seconds=offset_seconds),
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev


def test_build_session_timeline_orders_by_time():
    engine = _engine()
    with Session(engine) as db:
        ws = _make_workspace(db)
        session_id = "sess-abc"
        device_id = uuid.uuid4()
        e2 = _make_evidence(db, session_id, device_id, offset_seconds=10)
        e1 = _make_evidence(db, session_id, device_id, offset_seconds=0)
        from app.services.replay import build_session_timeline
        events = build_session_timeline(db, ws.id, session_id)
    assert len(events) == 2
    assert events[0].timestamp <= events[1].timestamp


def test_build_session_timeline_empty():
    engine = _engine()
    with Session(engine) as db:
        ws = _make_workspace(db)
        from app.services.replay import build_session_timeline
        events = build_session_timeline(db, ws.id, "no-such-session")
    assert events == []


def test_build_evidence_detail_has_artifacts():
    engine = _engine()
    with Session(engine) as db:
        ws = _make_workspace(db)
        from app.models import Artifact
        ev = _make_evidence(db, "sess-xyz", uuid.uuid4())
        art = Artifact(
            workspace_id=ws.id,
            artifact_type="screenshot",
            storage_path="/path/img.png",
            content_type="image/png",
            size_bytes=500,
            evidence_id=ev.id,
            captured_at=datetime.now(UTC),
            purge_after=datetime.now(UTC) + timedelta(days=30),
        )
        db.add(art)
        db.commit()
        from app.services.replay import build_evidence_detail
        detail = build_evidence_detail(db, ev.id)
    assert str(art.id) in detail["artifact_refs"]


def test_replay_as_recipe_draft_valid_yaml():
    engine = _engine()
    with Session(engine) as db:
        ws = _make_workspace(db)
        ev = _make_evidence(db, "sess-replay", uuid.uuid4())
        with patch(
            "app.services.recipes.recorder.build_recipe_draft",
            return_value="steps:\n  - tap: foo\n",
        ):
            from app.services.replay import replay_as_recipe_draft
            draft = replay_as_recipe_draft(db, ev.id)
    yaml.safe_load(draft)  # must not raise


def test_replay_as_recipe_draft_one_step():
    engine = _engine()
    with Session(engine) as db:
        ws = _make_workspace(db)
        ev = _make_evidence(db, "sess-one", uuid.uuid4())
        with patch(
            "app.services.recipes.recorder.build_recipe_draft",
            return_value="steps:\n  - tap: foo\n",
        ):
            from app.services.replay import replay_as_recipe_draft
            draft = replay_as_recipe_draft(db, ev.id)
    parsed = yaml.safe_load(draft)
    assert len(parsed["steps"]) == 1
