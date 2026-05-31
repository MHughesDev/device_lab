"""Tests for the identity broker — uses mocked keyring to avoid OS keychain dependency."""
from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from app.models import SecretRef, Workspace


@pytest.fixture()
def db():
    """In-memory SQLite session with required tables."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        ws = Workspace(name="test-workspace")
        session.add(ws)
        session.commit()
        yield session


@pytest.fixture()
def workspace_id(db) -> uuid.UUID:
    ws = db.exec(select(Workspace).limit(1)).first()
    assert ws is not None
    return ws.id


def test_store_and_list(db, workspace_id):
    """store() persists metadata; list_refs() returns it without the secret value."""
    from app.services.identity.broker import list_refs, store

    with patch("keyring.set_password") as mock_set:
        ref = store(db, workspace_id, "my-secret", "s3cr3t", description="A test secret")

    mock_set.assert_called_once()
    assert ref.name == "my-secret"
    assert ref.description == "A test secret"
    assert ref.backend == "keyring"

    refs = list_refs(db, workspace_id)
    assert len(refs) == 1
    assert refs[0].name == "my-secret"
    # Ensure value is not stored anywhere in the ref
    assert not hasattr(refs[0], "value") or getattr(refs[0], "value", None) is None


def test_resolve_calls_keyring(db, workspace_id):
    """resolve() fetches the value from keyring.get_password."""
    from app.services.identity.broker import resolve, store

    with patch("keyring.set_password"):
        store(db, workspace_id, "api-key", "super-secret")

    with patch("keyring.get_password", return_value="super-secret") as mock_get:
        value = resolve(db, workspace_id, "api-key")

    mock_get.assert_called_once()
    assert value == "super-secret"


def test_resolve_missing_raises(db, workspace_id):
    """resolve() raises SecretNotFound for an unknown ref name."""
    from app.services.identity.broker import SecretNotFound, resolve

    with pytest.raises(SecretNotFound):
        resolve(db, workspace_id, "nonexistent-secret")


def test_delete_removes_from_db(db, workspace_id):
    """delete() removes the ref from DB; subsequent list_refs() does not include it."""
    from app.services.identity.broker import delete, list_refs, store

    with patch("keyring.set_password"):
        store(db, workspace_id, "temp-secret", "value123")

    # Confirm it's there
    refs = list_refs(db, workspace_id)
    assert any(r.name == "temp-secret" for r in refs)

    # Delete it
    with patch("keyring.delete_password"):
        delete(db, workspace_id, "temp-secret")

    # Confirm it's gone
    refs_after = list_refs(db, workspace_id)
    assert not any(r.name == "temp-secret" for r in refs_after)


def test_store_updates_existing(db, workspace_id):
    """Calling store() twice with the same name updates description without duplicating."""
    from app.services.identity.broker import list_refs, store

    with patch("keyring.set_password"):
        store(db, workspace_id, "dup-secret", "value1", description="first")
        store(db, workspace_id, "dup-secret", "value2", description="second")

    refs = list_refs(db, workspace_id)
    assert len(refs) == 1
    assert refs[0].description == "second"
