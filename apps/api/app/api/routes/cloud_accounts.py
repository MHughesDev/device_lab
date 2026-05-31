import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlmodel import select

from app.api.deps import SessionDep
from app.models import (
    BootstrapPlan,
    CloudAccountCreate,
    CloudAccountPublic,
    Message,
    PreflightReport,
    Workspace,
)
from app.services import bootstrap, cloud_account, preflight

router = APIRouter(prefix="/cloud-accounts", tags=["cloud-accounts"])


def _get_workspace(db) -> Workspace:
    ws = db.exec(select(Workspace).limit(1)).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not initialised")
    return ws


def _to_public(a) -> CloudAccountPublic:
    return CloudAccountPublic(
        id=a.id,
        provider=a.provider,
        account_id=a.account_id,
        display_name=a.display_name,
        region=a.region,
        credential_source=a.credential_source,
        status=a.status,
        bootstrap_status=a.bootstrap_status,
        last_preflight_at=a.last_preflight_at,
    )


@router.post("/", response_model=CloudAccountPublic, status_code=201)
def create_cloud_account(db: SessionDep, body: CloudAccountCreate) -> CloudAccountPublic:
    ws = _get_workspace(db)
    acct = cloud_account.create_cloud_account(db, ws.id, body)
    return _to_public(acct)


@router.get("/", response_model=list[CloudAccountPublic])
def list_cloud_accounts(db: SessionDep) -> list[CloudAccountPublic]:
    ws = _get_workspace(db)
    accounts = cloud_account.list_cloud_accounts(db, ws.id)
    return [_to_public(a) for a in accounts]


@router.get("/{account_id}", response_model=CloudAccountPublic)
def get_cloud_account(db: SessionDep, account_id: uuid.UUID) -> CloudAccountPublic:
    acct = cloud_account.get_cloud_account(db, account_id)
    if not acct:
        raise HTTPException(status_code=404, detail="Cloud account not found")
    return _to_public(acct)


@router.delete("/{account_id}", response_model=Message)
def delete_cloud_account(db: SessionDep, account_id: uuid.UUID) -> Message:
    acct = cloud_account.get_cloud_account(db, account_id)
    if not acct:
        raise HTTPException(status_code=404, detail="Cloud account not found")
    cloud_account.delete_cloud_account(db, acct)
    return Message(message="Deleted")


@router.post("/{account_id}/preflight", response_model=PreflightReport)
def run_preflight(db: SessionDep, account_id: uuid.UUID) -> PreflightReport:
    acct = cloud_account.get_cloud_account(db, account_id)
    if not acct:
        raise HTTPException(status_code=404, detail="Cloud account not found")
    return preflight.run_preflight(db, acct)


@router.get("/{account_id}/bootstrap/plan", response_model=BootstrapPlan)
def get_bootstrap_plan(db: SessionDep, account_id: uuid.UUID) -> BootstrapPlan:
    acct = cloud_account.get_cloud_account(db, account_id)
    if not acct:
        raise HTTPException(status_code=404, detail="Cloud account not found")
    try:
        return bootstrap.plan_bootstrap(db, acct)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/{account_id}/bootstrap/execute", response_model=Message)
def execute_bootstrap(
    db: SessionDep, account_id: uuid.UUID, background: BackgroundTasks
) -> Message:
    acct = cloud_account.get_cloud_account(db, account_id)
    if not acct:
        raise HTTPException(status_code=404, detail="Cloud account not found")
    if acct.bootstrap_status == "complete":
        return Message(message="Bootstrap already complete")
    background.add_task(bootstrap.execute_bootstrap, db, acct)
    acct.bootstrap_status = "planning"
    db.add(acct)
    db.commit()
    return Message(message="Bootstrap started in background")
