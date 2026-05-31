"""Identity broker — stores SecretRef metadata in DB, values in OS keychain via keyring."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

import keyring
from sqlmodel import Session, select

from app.models import SecretRef


class SecretNotFound(Exception): ...
class SecretBackendError(Exception): ...


def store(db: Session, workspace_id: uuid.UUID, name: str, value: str, description: str = "", backend: str = "keyring") -> SecretRef:
    """Store a secret value in the OS keychain and persist metadata in DB."""
    service = f"devicelab:{workspace_id}"
    username = name
    try:
        keyring.set_password(service, username, value)
    except Exception as e:
        raise SecretBackendError(f"keyring write failed: {e}") from e

    existing = db.exec(select(SecretRef).where(SecretRef.name == name, SecretRef.workspace_id == workspace_id)).first()
    if existing:
        existing.description = description
        existing.backend = backend
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    ref = SecretRef(
        workspace_id=workspace_id,
        name=name,
        description=description,
        backend=backend,
        keyring_service=service,
        keyring_username=username,
    )
    db.add(ref)
    db.commit()
    db.refresh(ref)
    return ref


def resolve(db: Session, workspace_id: uuid.UUID, name: str) -> str:
    """Return raw secret value. Never log or return this in API responses."""
    ref = db.exec(select(SecretRef).where(SecretRef.name == name, SecretRef.workspace_id == workspace_id)).first()
    if not ref:
        raise SecretNotFound(f"SecretRef '{name}' not found")

    if ref.backend == "env":
        import os
        value = os.environ.get(ref.keyring_username)
        if value is None:
            raise SecretNotFound(f"Env var '{ref.keyring_username}' not set")
    else:
        value = keyring.get_password(ref.keyring_service, ref.keyring_username)
        if value is None:
            raise SecretNotFound(f"Secret '{name}' not in keychain")

    ref.last_used_at = datetime.now(UTC)
    db.add(ref)
    db.commit()
    return value


def list_refs(db: Session, workspace_id: uuid.UUID) -> list[SecretRef]:
    return list(db.exec(select(SecretRef).where(SecretRef.workspace_id == workspace_id)).all())


def delete(db: Session, workspace_id: uuid.UUID, name: str) -> None:
    ref = db.exec(select(SecretRef).where(SecretRef.name == name, SecretRef.workspace_id == workspace_id)).first()
    if not ref:
        raise SecretNotFound(f"SecretRef '{name}' not found")
    try:
        keyring.delete_password(ref.keyring_service, ref.keyring_username)
    except keyring.errors.PasswordDeleteError:
        pass  # already gone from keychain
    db.delete(ref)
    db.commit()
