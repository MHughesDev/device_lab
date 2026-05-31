from datetime import UTC, datetime

from fastapi import APIRouter
from sqlmodel import select

from app.api.deps import SessionDep
from app.core.config import VERSION, settings
from app.models import (
    CloudAccount,
    CloudAccountPublic,
    Device,
    Workspace,
    WorkspaceCapabilities,
    WorkspaceStatus,
)

router = APIRouter(prefix="/workspace", tags=["workspace"])


@router.get("/", response_model=WorkspaceStatus)
def get_workspace(db: SessionDep) -> WorkspaceStatus:
    workspace = db.exec(select(Workspace).limit(1)).first()
    if workspace is None:
        workspace = Workspace(name="default", created_at=datetime.now(UTC))
        db.add(workspace)
        db.commit()
        db.refresh(workspace)

    accounts = db.exec(
        select(CloudAccount).where(CloudAccount.workspace_id == workspace.id)
    ).all()

    aws_connect = any(a.status in ("preflight_passed", "preflight_warned") for a in accounts)
    device_lifecycle = db.exec(select(Device).where(Device.workspace_id == workspace.id).limit(1)).first() is not None

    return WorkspaceStatus(
        id=workspace.id,
        name=workspace.name,
        version=VERSION,
        bind_host=settings.BIND_HOST,
        dangerous_mode=settings.DANGEROUS_MODE,
        capabilities=WorkspaceCapabilities(
            aws_connect=aws_connect,
            device_lifecycle=device_lifecycle,
            mcp_gateway=True,
        ),
        cloud_accounts=[
            CloudAccountPublic(
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
            for a in accounts
        ],
    )
