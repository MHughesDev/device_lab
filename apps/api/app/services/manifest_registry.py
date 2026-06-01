# services/manifest_registry.py — ManifestRegistry CRUD service (Phase 10, task 10-02)
"""
CRUD service for DeviceManifest. Powers the "Existing" manifest picker in the
create-device wizard and the manifest library view.

Registry operations:
  list(workspace_id, family, location) → filter + paginate
  get(manifest_id) → DeviceManifest
  create(body: ManifestCreate) → DeviceManifest
  update(manifest_id, body: ManifestUpdate) → DeviceManifest
  delete(manifest_id) → None (refuses if referenced by a live device)
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime

from sqlmodel import Session, select

from app.models import Device, DeviceManifest, ManifestCreate, ManifestUpdate

log = logging.getLogger(__name__)


class ManifestNotFoundError(KeyError):
    pass


class ManifestInUseError(ValueError):
    """Raised when trying to delete a manifest referenced by a live device."""
    pass


def list_manifests(
    db: Session,
    workspace_id: uuid.UUID,
    *,
    family: str | None = None,
    location: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[DeviceManifest]:
    stmt = select(DeviceManifest).where(DeviceManifest.workspace_id == workspace_id)
    if family:
        stmt = stmt.where(DeviceManifest.family == family)
    if location:
        stmt = stmt.where(DeviceManifest.location == location)
    stmt = stmt.order_by(DeviceManifest.created_at.desc()).offset(offset).limit(limit)
    return list(db.exec(stmt).all())


def get_manifest(db: Session, manifest_id: uuid.UUID) -> DeviceManifest:
    m = db.get(DeviceManifest, manifest_id)
    if not m:
        raise ManifestNotFoundError(f"Manifest {manifest_id} not found")
    return m


def create_manifest(db: Session, body: ManifestCreate) -> DeviceManifest:
    from app.services.manifest_spec import validate
    # Validate spec before persisting
    validate(body.spec_json, body.family)

    now = datetime.now(UTC)
    m = DeviceManifest(
        workspace_id=body.workspace_id,
        name=body.name,
        family=body.family,
        location=body.location,
        description=body.description,
        spec_json=body.spec_json,
        source_device_id=body.source_device_id,
        created_at=now,
        updated_at=now,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    _emit(str(body.workspace_id), "create", {"manifest_id": str(m.id), "name": m.name})
    return m


def update_manifest(db: Session, manifest_id: uuid.UUID, body: ManifestUpdate) -> DeviceManifest:
    m = get_manifest(db, manifest_id)
    if body.name is not None:
        m.name = body.name
    if body.description is not None:
        m.description = body.description
    if body.spec_json is not None:
        from app.services.manifest_spec import validate
        validate(body.spec_json, m.family)
        m.spec_json = body.spec_json
    m.updated_at = datetime.now(UTC)
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


def delete_manifest(db: Session, manifest_id: uuid.UUID) -> None:
    m = get_manifest(db, manifest_id)

    # Refuse if any live (non-terminated) device was created from this manifest
    live = db.exec(
        select(Device)
        .where(Device.source_manifest_id == manifest_id)
        .where(Device.state.notin_(["terminated", "failed"]))
    ).first()
    if live:
        raise ManifestInUseError(
            f"Manifest {manifest_id} is referenced by live device {live.id} (state={live.state}). "
            "Terminate the device before deleting the manifest."
        )

    db.delete(m)
    db.commit()


def manifest_to_public(m: DeviceManifest) -> dict:
    return {
        "id": str(m.id),
        "workspace_id": str(m.workspace_id),
        "name": m.name,
        "family": m.family,
        "location": m.location,
        "description": m.description,
        "spec_json": m.spec_json,
        "source_device_id": str(m.source_device_id) if m.source_device_id else None,
        "created_at": m.created_at.isoformat(),
        "updated_at": m.updated_at.isoformat(),
        "title": m.title,
    }


def _emit(workspace_id: str, event: str, fields: dict | None = None) -> None:
    try:
        from app.services.device_log_bus import get_log_bus
        get_log_bus().emit(
            workspace_id,
            level="info",
            source="manifest",
            message=f"Manifest registry event: {event}",
            fields={"event": event, **(fields or {})},
        )
    except Exception:
        pass
