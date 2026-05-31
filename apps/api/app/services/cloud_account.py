import uuid
from datetime import UTC, datetime

from sqlmodel import Session, select

from app.models import CloudAccount, CloudAccountCreate, Workspace


def create_cloud_account(
    db: Session, workspace_id: uuid.UUID, data: CloudAccountCreate
) -> CloudAccount:
    account = CloudAccount(
        workspace_id=workspace_id,
        provider=data.provider,
        display_name=data.display_name,
        region=data.region,
        credential_source=data.credential_source,
        credential_profile=data.credential_profile,
        credential_role_arn=data.credential_role_arn,
        status="pending_preflight",
        bootstrap_status="not_started",
        account_id="",
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def list_cloud_accounts(db: Session, workspace_id: uuid.UUID) -> list[CloudAccount]:
    return list(
        db.exec(select(CloudAccount).where(CloudAccount.workspace_id == workspace_id)).all()
    )


def get_cloud_account(db: Session, account_id: uuid.UUID) -> CloudAccount | None:
    return db.get(CloudAccount, account_id)


def delete_cloud_account(db: Session, account: CloudAccount) -> None:
    db.delete(account)
    db.commit()
