# cost.py — Cost policy and orphan resource API routes
import uuid

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.core.audit_log import append_event
from app.core.config import settings
from app.models import CostPolicy, CostPolicyCreate, CostPolicyPublic, OrphanResource, Workspace
from app.services.cost import inventory

router = APIRouter(prefix="/cost", tags=["cost"])


def _get_workspace(db) -> Workspace:
    ws = db.exec(select(Workspace).limit(1)).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not initialised")
    return ws


@router.get("/policies", response_model=list[CostPolicyPublic])
def list_policies(db: SessionDep, current_user: CurrentUser) -> list[CostPolicy]:
    ws = _get_workspace(db)
    return list(db.exec(select(CostPolicy).where(CostPolicy.workspace_id == ws.id)).all())


@router.post("/policies", response_model=CostPolicyPublic, status_code=201)
def create_policy(body: CostPolicyCreate, db: SessionDep, current_user: CurrentUser) -> CostPolicy:
    ws = _get_workspace(db)
    policy = CostPolicy(workspace_id=ws.id, **body.model_dump())
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


@router.put("/policies/{policy_id}", response_model=CostPolicyPublic)
def update_policy(
    policy_id: uuid.UUID, body: CostPolicyCreate, db: SessionDep, current_user: CurrentUser
) -> CostPolicy:
    policy = db.get(CostPolicy, policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    for field, value in body.model_dump().items():
        setattr(policy, field, value)
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


@router.delete("/policies/{policy_id}", status_code=204)
def delete_policy(policy_id: uuid.UUID, db: SessionDep, current_user: CurrentUser) -> None:
    policy = db.get(CostPolicy, policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    db.delete(policy)
    db.commit()


@router.get("/orphans", response_model=list[OrphanResource])
def list_orphans(region: str, db: SessionDep, current_user: CurrentUser) -> list[OrphanResource]:
    ws = _get_workspace(db)
    return inventory.detect_orphans(db, ws.id, region)


@router.post("/orphans/{resource_id}/cleanup")
def cleanup_orphan(
    resource_id: str,
    body: dict,
    db: SessionDep,
    current_user: CurrentUser,
) -> dict:
    if not settings.DANGEROUS_MODE:
        raise HTTPException(status_code=403, detail="DANGEROUS_MODE must be enabled for orphan cleanup")
    ws = _get_workspace(db)
    resource_type = body.get("resource_type", "")
    region = body.get("region", "")
    inventory.cleanup_orphan(resource_id, resource_type, region)
    append_event(
        db,
        workspace_id=ws.id,
        actor=str(current_user.id),
        action="orphan_cleanup",
        target_type="OrphanResource",
        target_id=resource_id,
        metadata={"resource_type": resource_type, "region": region},
    )
    return {"cleaned": True}
