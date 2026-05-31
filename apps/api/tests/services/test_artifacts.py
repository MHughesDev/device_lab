import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel

from app.models import Artifact, Workspace


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


def test_store_artifact_persists():
    engine = _engine()
    with Session(engine) as db:
        ws = _make_workspace(db)
        from app.services.artifacts import store_artifact
        art = store_artifact(db, ws.id, "screenshot", "/local/path.png", "image/png", 1024)
    assert art.id is not None
    assert art.artifact_type == "screenshot"


def test_list_artifacts_excludes_purged():
    engine = _engine()
    with Session(engine) as db:
        ws = _make_workspace(db)
        from app.services.artifacts import store_artifact, list_artifacts
        a1 = store_artifact(db, ws.id, "log", "/local/a.log", "text/plain", 100)
        a2 = store_artifact(db, ws.id, "log", "/local/b.log", "text/plain", 100)
        a2.purged = True
        db.add(a2)
        db.commit()
        results = list_artifacts(db, ws.id)
    assert len(results) == 1
    assert results[0].id == a1.id


def test_list_artifacts_by_run_id():
    engine = _engine()
    with Session(engine) as db:
        ws = _make_workspace(db)
        run_id = uuid.uuid4()
        from app.services.artifacts import store_artifact, list_artifacts
        a1 = store_artifact(db, ws.id, "log", "/a.log", "text/plain", 10, run_id=run_id)
        a2 = store_artifact(db, ws.id, "log", "/b.log", "text/plain", 10)
        results = list_artifacts(db, ws.id, run_id=run_id)
    assert len(results) == 1
    assert results[0].id == a1.id


def test_purge_expired_marks_rows():
    engine = _engine()
    with Session(engine) as db:
        ws = _make_workspace(db)
        past = datetime.now(UTC) - timedelta(days=1)
        art = Artifact(
            workspace_id=ws.id,
            artifact_type="log",
            storage_path="/old.log",
            content_type="text/plain",
            size_bytes=10,
            captured_at=past,
            retention_days=0,
            purge_after=past,
            purged=False,
        )
        db.add(art)
        db.commit()
        from app.services.artifacts import purge_expired
        count = purge_expired(db, ws.id)
    assert count == 1


def test_purge_expired_skips_fresh():
    engine = _engine()
    with Session(engine) as db:
        ws = _make_workspace(db)
        from app.services.artifacts import store_artifact, purge_expired
        store_artifact(db, ws.id, "log", "/fresh.log", "text/plain", 10, retention_days=30)
        count = purge_expired(db, ws.id)
    assert count == 0


def test_presigned_url_local_path():
    engine = _engine()
    with Session(engine) as db:
        ws = _make_workspace(db)
        from app.services.artifacts import store_artifact, get_presigned_download_url
        art = store_artifact(db, ws.id, "log", "/local/file.log", "text/plain", 10)
        url = get_presigned_download_url(art)
    assert url == "/local/file.log"
