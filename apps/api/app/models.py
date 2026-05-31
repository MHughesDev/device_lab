import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import EmailStr
from sqlalchemy import DateTime, Text
from sqlmodel import Column, Field, Relationship, SQLModel


def get_datetime_utc() -> datetime:
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore[assignment]
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime | None = None


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# ---------------------------------------------------------------------------
# DeviceLab domain models
# ---------------------------------------------------------------------------

class Workspace(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255, default="default")
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    settings_json: str | None = Field(default=None, sa_column=Column(Text))

    cloud_accounts: list["CloudAccount"] = Relationship(back_populates="workspace")
    devices: list["Device"] = Relationship(back_populates="workspace")
    audit_events: list["AuditEvent"] = Relationship(back_populates="workspace")


class CloudAccount(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", index=True)
    provider: str = Field(max_length=64, default="aws")
    account_id: str = Field(max_length=128)
    display_name: str = Field(max_length=255)
    status: str = Field(max_length=64, default="unknown")
    last_preflight_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    preflight_summary_json: str | None = Field(default=None, sa_column=Column(Text))

    workspace: Workspace | None = Relationship(back_populates="cloud_accounts")


class DeviceTemplate(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    family: str = Field(max_length=64, index=True)
    name: str = Field(max_length=255)
    description: str | None = Field(default=None, max_length=1024)
    capability_json: str | None = Field(default=None, sa_column=Column(Text))
    supported_regions: str | None = Field(default=None, sa_column=Column(Text))

    devices: list["Device"] = Relationship(back_populates="template")


class Device(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    template_id: uuid.UUID | None = Field(default=None, foreign_key="devicetemplate.id")
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", index=True)
    family: str = Field(max_length=64)
    state: str = Field(max_length=64, default="requested")
    phase: str | None = Field(default=None, max_length=64)
    provider_ids_json: str | None = Field(default=None, sa_column=Column(Text))
    cost_estimate: float | None = Field(default=None)
    tags_json: str | None = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )

    template: DeviceTemplate | None = Relationship(back_populates="devices")
    workspace: Workspace | None = Relationship(back_populates="devices")


class AuditEvent(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", index=True)
    actor: str = Field(max_length=255)
    action: str = Field(max_length=255)
    target_type: str = Field(max_length=128)
    target_id: str = Field(max_length=255)
    decision: str = Field(max_length=64, default="allow")
    metadata_json: str | None = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    hash: str = Field(max_length=64)
    prev_hash: str = Field(max_length=64)

    workspace: Workspace | None = Relationship(back_populates="audit_events")


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class CloudAccountPublic(SQLModel):
    id: uuid.UUID
    provider: str
    account_id: str
    display_name: str
    status: str


class DevicePublic(SQLModel):
    id: uuid.UUID
    family: str
    state: str
    phase: str | None
    cost_estimate: float | None
    created_at: datetime
    updated_at: datetime


class WorkspaceCapabilities(SQLModel):
    aws_connect: bool = False
    device_lifecycle: bool = False
    mcp_gateway: bool = False
    streaming: bool = False
    recipes: bool = False


class WorkspaceStatus(SQLModel):
    id: uuid.UUID
    name: str
    version: str
    bind_host: str
    dangerous_mode: bool
    capabilities: WorkspaceCapabilities
    cloud_accounts: list[CloudAccountPublic]


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------

class Message(SQLModel):
    message: str


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(SQLModel):
    sub: uuid.UUID | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)
