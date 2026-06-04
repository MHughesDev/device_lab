# tests/services/test_manifest_registry.py — Phase 10 manifest registry tests
from __future__ import annotations

import json
import uuid
import pytest
from unittest.mock import MagicMock, patch

from app.models import ManifestCreate, ManifestUpdate


def _make_manifest_create(workspace_id=None, name="Test", family="linux", spec_json="{}"):
    return ManifestCreate(
        workspace_id=workspace_id or uuid.uuid4(),
        name=name,
        family=family,
        spec_json=spec_json,
    )


def test_manifest_model_defaults():
    from app.models import DeviceManifest
    from datetime import datetime, timezone
    m = DeviceManifest(
        workspace_id=uuid.uuid4(),
        family="linux",
        spec_json="{}",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    assert m.name is None
    assert m.location == "local"
    assert m.source_device_id is None


def test_manifest_public_title_with_name():
    from app.models import DeviceManifest
    from datetime import datetime, timezone
    m = DeviceManifest(
        id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        name="My Dev Env",
        family="linux",
        spec_json="{}",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    assert m.title == "My Dev Env"


def test_manifest_public_title_fallback():
    from app.models import DeviceManifest
    from datetime import datetime, timezone
    mid = uuid.uuid4()
    m = DeviceManifest(
        id=mid,
        workspace_id=uuid.uuid4(),
        name=None,
        family="android",
        spec_json="{}",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    assert m.title == f"android · {str(mid)[:8]}"


def test_registry_create_valid(tmp_path):
    """ManifestRegistry.create() stores a valid manifest."""
    from sqlmodel import SQLModel, create_engine, Session
    from app.services.manifest_registry import create_manifest, list_manifests, ManifestNotFoundError

    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    ws_id = uuid.uuid4()
    with Session(engine) as db:
        body = _make_manifest_create(workspace_id=ws_id, name="MyEnv")
        m = create_manifest(db, body)
        assert m.name == "MyEnv"
        assert m.family == "linux"


def test_registry_lists_by_family(tmp_path):
    from sqlmodel import SQLModel, create_engine, Session
    from app.services.manifest_registry import create_manifest, list_manifests

    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    ws_id = uuid.uuid4()
    with Session(engine) as db:
        create_manifest(db, _make_manifest_create(ws_id, name="A", family="linux"))
        create_manifest(db, _make_manifest_create(ws_id, name="B", family="android"))

        linux_only = list_manifests(db, ws_id, family="linux")
        assert all(m.family == "linux" for m in linux_only)
        assert len(linux_only) == 1


def test_registry_rename(tmp_path):
    from sqlmodel import SQLModel, create_engine, Session
    from app.services.manifest_registry import create_manifest, update_manifest

    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    ws_id = uuid.uuid4()
    with Session(engine) as db:
        m = create_manifest(db, _make_manifest_create(ws_id, name="Old Name"))
        updated = update_manifest(db, m.id, ManifestUpdate(name="New Name"))
        assert updated.name == "New Name"


def test_registry_delete_not_in_use(tmp_path):
    from sqlmodel import SQLModel, create_engine, Session
    from app.services.manifest_registry import create_manifest, delete_manifest, get_manifest, ManifestNotFoundError

    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    ws_id = uuid.uuid4()
    with Session(engine) as db:
        m = create_manifest(db, _make_manifest_create(ws_id, name="Deletable"))
        mid = m.id
        delete_manifest(db, mid)
        with pytest.raises(ManifestNotFoundError):
            get_manifest(db, mid)


def test_registry_create_invalid_spec_raises():
    from sqlmodel import SQLModel, create_engine, Session
    from app.services.manifest_registry import create_manifest
    from app.services.manifest_spec import ManifestValidationError

    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    ws_id = uuid.uuid4()
    with Session(engine) as db:
        body = _make_manifest_create(ws_id, spec_json='{"install_steps": [{"type": "invalid_type"}]}')
        with pytest.raises(ManifestValidationError):
            create_manifest(db, body)
