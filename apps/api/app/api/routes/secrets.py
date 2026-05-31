"""Secrets API — metadata only, no values in responses."""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.models import SecretRefCreate, SecretRefPublic, Workspace
from app.services.identity.broker import SecretBackendError, SecretNotFound, delete, list_refs, store

router = APIRouter(prefix="/secrets", tags=["secrets"])


def _get_workspace(db: Session) -> Workspace:
    ws = db.exec(select(Workspace).limit(1)).first()
    if not ws:
        raise HTTPException(status_code=503, detail="Workspace not initialised")
    return ws


@router.get("/", response_model=list[SecretRefPublic])
def list_secrets(db: SessionDep, _current_user: CurrentUser) -> list[SecretRefPublic]:
    ws = _get_workspace(db)
    refs = list_refs(db, ws.id)
    return [SecretRefPublic(**r.model_dump()) for r in refs]


@router.post("/", response_model=SecretRefPublic, status_code=201)
def create_secret(body: SecretRefCreate, db: SessionDep, _current_user: CurrentUser) -> SecretRefPublic:
    ws = _get_workspace(db)
    try:
        ref = store(db, ws.id, body.name, body.value, body.description, body.backend)
    except SecretBackendError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return SecretRefPublic(**ref.model_dump())


@router.delete("/{name}", status_code=204)
def delete_secret(name: str, db: SessionDep, _current_user: CurrentUser) -> None:
    ws = _get_workspace(db)
    try:
        delete(db, ws.id, name)
    except SecretNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
