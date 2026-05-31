# snapshots.py — Snapshot API routes: create, retrieve, fork, and delete device snapshots
import uuid

from fastapi import APIRouter, HTTPException, Response
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.core.config import settings
from app.models import DevicePublic, Snapshot, SnapshotPublic, Workspace
from app.services import snapshots as snapshot_svc
from app.services.snapshots import CapabilityUnsupportedError

router = APIRouter(tags=["snapshots"])


def _get_workspace(db) -> Workspace:
    ws = db.exec(select(Workspace).limit(1)).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not initialised")
    return ws


@router.post("/devices/{device_id}/snapshot", response_model=SnapshotPublic, status_code=201)
async def create_snapshot(
    device_id: uuid.UUID,
    db: SessionDep,
    current_user: CurrentUser,
) -> Snapshot:
    ws = _get_workspace(db)
    try:
        return await snapshot_svc.create_snapshot(db, ws.id, device_id)
    except CapabilityUnsupportedError as e:
        raise HTTPException(
            status_code=422,
            detail={"error": "CAPABILITY_UNSUPPORTED", "capability": e.capability, "family": e.family},
        )


@router.get("/snapshots/{snapshot_id}", response_model=SnapshotPublic)
async def get_snapshot(snapshot_id: uuid.UUID, db: SessionDep, current_user: CurrentUser) -> Snapshot:
    snap = db.get(Snapshot, snapshot_id)
    if not snap:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    if snap.status == "pending":
        snap = await snapshot_svc.poll_snapshot_status(db, snapshot_id)
    return snap


@router.post("/snapshots/{snapshot_id}/fork", response_model=DevicePublic, status_code=201)
async def fork_snapshot(
    snapshot_id: uuid.UUID,
    body: dict,
    db: SessionDep,
    current_user: CurrentUser,
) -> object:
    ws = _get_workspace(db)
    template_overrides = body.get("template_overrides", {})
    return await snapshot_svc.fork_from_snapshot(db, snapshot_id, ws.id, template_overrides)


@router.delete("/snapshots/{snapshot_id}", status_code=204)
async def delete_snapshot(snapshot_id: uuid.UUID, db: SessionDep, current_user: CurrentUser) -> Response:
    ws = _get_workspace(db)
    snap = db.get(Snapshot, snapshot_id)
    if not snap:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    try:
        await snapshot_svc.delete_snapshot(db, snapshot_id, ws.id, dangerous_mode=settings.DANGEROUS_MODE)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    return Response(status_code=204)
