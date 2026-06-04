# api/routes/manifests.py — Manifest registry REST routes (Phase 10, task 10-02, 10-11, 10-12)
"""
REST routes for DeviceManifest CRUD + import/export.

GET    /manifests?workspace_id=&family=&location=  — list
POST   /manifests                                  — create
GET    /manifests/{id}                             — get
PATCH  /manifests/{id}                             — update (rename / edit spec)
DELETE /manifests/{id}                             — delete (refused if in-use)
GET    /manifests/{id}/export                      — export standalone JSON
POST   /manifests/import                           — import from exported JSON
"""
from __future__ import annotations

import json
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.api.deps import CurrentUser, SessionDep
from app.models import ManifestCreate, ManifestPublic, ManifestUpdate
from app.services.manifest_spec import ManifestValidationError

router = APIRouter(prefix="/manifests", tags=["manifests"])


class ManifestImportBody(BaseModel):
    name: str | None = None
    family: str
    location: str = "local"
    description: str | None = None
    spec_json: str
    workspace_id: uuid.UUID


def _public(m) -> ManifestPublic:
    return ManifestPublic(
        id=m.id,
        workspace_id=m.workspace_id,
        name=m.name,
        family=m.family,
        location=m.location,
        description=m.description,
        spec_json=m.spec_json,
        source_device_id=m.source_device_id,
        created_at=m.created_at,
        updated_at=m.updated_at,
        title=m.title,
    )


@router.get("", response_model=list[ManifestPublic])
def list_manifests(
    db: SessionDep,
    _current_user: CurrentUser,
    workspace_id: uuid.UUID = Query(...),
    family: str | None = Query(default=None),
    location: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[ManifestPublic]:
    from app.services.manifest_registry import list_manifests as _list
    return [_public(m) for m in _list(db, workspace_id, family=family, location=location, limit=limit, offset=offset)]


@router.post("", response_model=ManifestPublic, status_code=201)
def create_manifest(
    body: ManifestCreate,
    db: SessionDep,
    _current_user: CurrentUser,
) -> ManifestPublic:
    from app.services.manifest_registry import create_manifest as _create
    try:
        return _public(_create(db, body))
    except ManifestValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/import", include_in_schema=False)
def import_redirect():
    raise HTTPException(status_code=405, detail="Use POST /manifests/import")


@router.post("/import", response_model=ManifestPublic, status_code=201)
def import_manifest(
    body: ManifestImportBody,
    db: SessionDep,
    _current_user: CurrentUser,
) -> ManifestPublic:
    """Import a manifest from the export JSON format. Validates spec; handles duplicate names."""
    from app.services.manifest_registry import create_manifest as _create, list_manifests as _list
    from app.models import ManifestCreate

    # Validate spec
    try:
        from app.services.manifest_spec import validate
        validate(body.spec_json, body.family)
    except ManifestValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Handle duplicate name by suffixing
    name = body.name
    if name:
        existing_names = {m.name for m in _list(db, body.workspace_id)}
        if name in existing_names:
            suffix = 2
            candidate = f"{name} ({suffix})"
            while candidate in existing_names:
                suffix += 1
                candidate = f"{name} ({suffix})"
            name = candidate

    create_body = ManifestCreate(
        workspace_id=body.workspace_id,
        name=name,
        family=body.family,
        location=body.location,
        description=body.description,
        spec_json=body.spec_json,
    )
    return _public(_create(db, create_body))


@router.get("/{manifest_id}", response_model=ManifestPublic)
def get_manifest(
    manifest_id: uuid.UUID,
    db: SessionDep,
    _current_user: CurrentUser,
) -> ManifestPublic:
    from app.services.manifest_registry import get_manifest as _get, ManifestNotFoundError
    try:
        return _public(_get(db, manifest_id))
    except ManifestNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{manifest_id}", response_model=ManifestPublic)
def update_manifest(
    manifest_id: uuid.UUID,
    body: ManifestUpdate,
    db: SessionDep,
    _current_user: CurrentUser,
) -> ManifestPublic:
    from app.services.manifest_registry import update_manifest as _update, ManifestNotFoundError
    try:
        return _public(_update(db, manifest_id, body))
    except ManifestNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ManifestValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/{manifest_id}", status_code=204)
def delete_manifest(
    manifest_id: uuid.UUID,
    db: SessionDep,
    _current_user: CurrentUser,
) -> None:
    from app.services.manifest_registry import delete_manifest as _delete, ManifestNotFoundError, ManifestInUseError
    try:
        _delete(db, manifest_id)
    except ManifestNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ManifestInUseError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/{manifest_id}/export")
def export_manifest(
    manifest_id: uuid.UUID,
    db: SessionDep,
    _current_user: CurrentUser,
) -> dict:
    """Export a manifest as a standalone JSON document for sharing / source control."""
    from app.services.manifest_registry import get_manifest as _get, ManifestNotFoundError
    try:
        m = _get(db, manifest_id)
    except ManifestNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {
        "name": m.name,
        "family": m.family,
        "location": m.location,
        "description": m.description,
        "spec": json.loads(m.spec_json),
        "spec_json": m.spec_json,
        "metadata": {
            "exported_from": str(m.id),
            "exported_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        },
    }
