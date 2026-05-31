from fastapi import APIRouter
from sqlmodel import select

from app.api.deps import SessionDep
from app.core.config import VERSION, settings
from app.models import (
    CloudAccount,
    CloudAccountPublic,
    Workspace,
    WorkspaceCapabilities,
    WorkspaceStatus,
)

router = APIRouter(prefix="/workspace", tags=["workspace"])


@router.get("/", response_model=WorkspaceStatus)
def get_workspace(db: SessionDep) -> WorkspaceStatus:
    workspace = db.exec(select(Workspace).limit(1)).first()
    if workspace is None:
        import uuid
        from datetime import UTC, datetime
        workspace = Workspace(name="default", created_at=datetime.now(UTC))
        db.add(workspace)
        db.commit()
        db.refresh(workspace)

    accounts = db.exec(
        select(CloudAccount).where(CloudAccount.workspace_id == workspace.id)
    ).all()

    return WorkspaceStatus(
        id=workspace.id,
        name=workspace.name,
        version=VERSION,
        bind_host=settings.BIND_HOST,
        dangerous_mode=settings.DANGEROUS_MODE,
        capabilities=WorkspaceCapabilities(),
        cloud_accounts=[
            CloudAccountPublic(
                id=a.id,
                provider=a.provider,
                account_id=a.account_id,
                display_name=a.display_name,
                status=a.status,
            )
            for a in accounts
        ],
    )
