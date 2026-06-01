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
    account_id: str = Field(max_length=128, default="")
    display_name: str = Field(max_length=255)
    region: str = Field(max_length=64, default="us-east-1")
    credential_source: str = Field(max_length=64, default="env")
    credential_profile: str | None = Field(default=None, max_length=128)
    credential_role_arn: str | None = Field(default=None, max_length=512)
    status: str = Field(max_length=64, default="pending_preflight")
    bootstrap_status: str = Field(max_length=64, default="not_started")
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
    location: str = Field(max_length=32, default="cloud")
    name: str | None = Field(default=None, max_length=120)
    display_mode: str = Field(default="headless", max_length=16)  # "headless" | "interactive"
    mcp_exposed: bool = Field(default=True)
    state: str = Field(max_length=64, default="requested")
    phase: str | None = Field(default=None, max_length=64)
    provider_ids_json: str | None = Field(default=None, sa_column=Column(Text))
    cost_estimate: float | None = Field(default=None)
    tags_json: str | None = Field(default=None, sa_column=Column(Text))
    screen_version: int = Field(default=0)
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


# ---------------------------------------------------------------------------
# Phase 08 — Host Resource Ledger + Device Log Bus
# ---------------------------------------------------------------------------

class HostReservation(SQLModel, table=True):
    """Persisted per-device resource claim for the Host Resource Ledger."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    device_id: uuid.UUID = Field(index=True, unique=True)
    ram_mb: int = Field(default=0)
    vcpu: float = Field(default=0.0)
    disk_mb: int = Field(default=0)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class DeviceLogEvent(SQLModel, table=True):
    """One entry in the per-device structured log bus ring (Phase 08)."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    device_id: uuid.UUID = Field(index=True)
    ts: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    level: str = Field(max_length=16)      # debug | info | warn | error
    source: str = Field(max_length=32)     # lifecycle | provisioner | transport | stream | mcp | recording | manifest | ledger
    message: str = Field(sa_column=Column(Text))
    fields_json: str | None = Field(default=None, sa_column=Column(Text))  # secret-redacted extras


class DeviceLogEventPublic(SQLModel):
    id: uuid.UUID
    device_id: uuid.UUID
    ts: datetime
    level: str
    source: str
    message: str
    fields_json: str | None


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

class CloudAccountCreate(SQLModel):
    provider: str = "aws"
    display_name: str
    region: str = "us-east-1"
    credential_source: str = "env"
    credential_profile: str | None = None
    credential_role_arn: str | None = None


class CloudAccountPublic(SQLModel):
    id: uuid.UUID
    provider: str
    account_id: str
    display_name: str
    region: str
    credential_source: str
    status: str
    bootstrap_status: str
    last_preflight_at: datetime | None


class PreflightCheckResult(SQLModel):
    name: str
    status: str  # pass | warn | fail
    severity: str  # info | warning | error
    message: str
    remediation: str = ""
    evidence: str = ""
    retryable: bool = True


class PreflightReport(SQLModel):
    status: str  # pass | warn | fail
    checks: list[PreflightCheckResult]


class BootstrapPlanResource(SQLModel):
    resource_type: str
    resource_id: str
    action: str  # create | skip
    estimated_cost: str = "$0.00/month"


class BootstrapPlan(SQLModel):
    account_id: str
    region: str
    resources: list[BootstrapPlanResource]
    total_estimated_cost: str
    requires_confirmation: bool = True


class DeviceTemplatePublic(SQLModel):
    id: uuid.UUID
    family: str
    name: str
    description: str | None
    capability_json: str | None
    supported_regions: str | None


class DeviceCreate(SQLModel):
    template_id: uuid.UUID
    cloud_account_id: uuid.UUID | None = None
    region: str | None = None
    name: str | None = None
    location: str = "local"
    display_mode: str = "headless"
    mcp_exposed: bool = True


class DeviceLifecycleEvent(SQLModel):
    event_type: str
    timestamp: datetime
    message: str


class DevicePublic(SQLModel):
    id: uuid.UUID
    family: str
    location: str
    name: str | None
    display_mode: str
    mcp_exposed: bool
    state: str
    phase: str | None
    cost_estimate: float | None
    created_at: datetime
    updated_at: datetime

    @property
    def title(self) -> str:
        return self.name or f"{self.family} · {str(self.id)[:8]}"


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
# Phase 03 — Evidence + screen versioning
# ---------------------------------------------------------------------------

class Evidence(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    session_id: str = Field(max_length=128)
    device_id: uuid.UUID = Field(index=True)
    mcp_tool: str = Field(max_length=128)
    request_payload_json: str | None = Field(default=None, sa_column=Column(Text))
    policy_decision: str = Field(max_length=64, default="allow")
    before_screen_version: int = Field(default=0)
    after_screen_version: int = Field(default=0)
    observation_before_ref: str | None = Field(default=None, max_length=255)
    observation_after_ref: str | None = Field(default=None, max_length=255)
    warnings_json: str | None = Field(default=None, sa_column=Column(Text))
    audit_event_id: uuid.UUID | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class ObservationEnvelope(SQLModel):
    device_id: str
    screen_version: int
    tier: str  # ax | ocr | screenshot | vlm
    structured: dict | None = None
    screenshot_ref: str | None = None
    delta_from_version: int | None = None
    warnings: list[str] = []
    observed_at: datetime


class ActionResult(SQLModel):
    success: bool
    before_screen_version: int
    after_screen_version: int
    observation_delta: dict | None = None
    evidence_id: str
    warnings: list[str] = []
    error: str | None = None


class Step(SQLModel):
    action: str
    params: dict = {}
    wait_after_ms: int = 0
    expected_screen_version: int | None = None


class BatchResult(SQLModel):
    success: bool
    steps: list[ActionResult]
    final_screen_version: int
    total_steps: int
    completed_steps: int


# ---------------------------------------------------------------------------
# Phase 04 — Recipes, Identity, Streaming
# ---------------------------------------------------------------------------

class SecretRef(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", index=True)
    name: str = Field(max_length=255, unique=True)        # e.g. "workspace/demo-creds"
    description: str = Field(max_length=1024, default="")
    backend: str = Field(max_length=64, default="keyring")  # "keyring" | "env"
    keyring_service: str = Field(max_length=255)
    keyring_username: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=get_datetime_utc, sa_type=DateTime(timezone=True))  # type: ignore
    last_used_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))  # type: ignore


class Recipe(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", index=True)
    name: str = Field(max_length=255)
    version: int = Field(default=1)
    families_json: str = Field(default="[]", sa_column=Column(Text))  # JSON list of family strings
    yaml_content: str = Field(sa_column=Column(Text))
    created_at: datetime = Field(default_factory=get_datetime_utc, sa_type=DateTime(timezone=True))  # type: ignore
    updated_at: datetime = Field(default_factory=get_datetime_utc, sa_type=DateTime(timezone=True))  # type: ignore
    runs: list["RecipeRun"] = Relationship(back_populates="recipe")


class RecipeRun(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    recipe_id: uuid.UUID = Field(foreign_key="recipe.id", index=True)
    device_id: uuid.UUID = Field(index=True)
    status: str = Field(max_length=64, default="pending")  # pending|running|paused|complete|failed
    current_step_index: int = Field(default=0)
    steps_json: str | None = Field(default=None, sa_column=Column(Text))   # JSON array of per-step status
    started_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))  # type: ignore
    completed_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))  # type: ignore
    recipe: Recipe | None = Relationship(back_populates="runs")


class StreamSession(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    device_id: uuid.UUID = Field(index=True)
    session_token: str = Field(max_length=512)
    status: str = Field(max_length=64, default="negotiating")  # negotiating|active|closed
    client_id: str = Field(max_length=255, default="")
    created_at: datetime = Field(default_factory=get_datetime_utc, sa_type=DateTime(timezone=True))  # type: ignore
    expires_at: datetime = Field(default_factory=get_datetime_utc, sa_type=DateTime(timezone=True))  # type: ignore


class SecretRefCreate(SQLModel):
    name: str
    value: str           # only at creation; never stored in DB
    description: str = ""
    backend: str = "keyring"


class SecretRefPublic(SQLModel):
    id: uuid.UUID
    name: str
    description: str
    backend: str
    created_at: datetime
    last_used_at: datetime | None


class RecipePublic(SQLModel):
    id: uuid.UUID
    name: str
    version: int
    families_json: str
    created_at: datetime
    updated_at: datetime


class RecipeCreate(SQLModel):
    name: str
    yaml_content: str


class RecipeRunPublic(SQLModel):
    id: uuid.UUID
    recipe_id: uuid.UUID
    device_id: uuid.UUID
    status: str
    current_step_index: int
    started_at: datetime | None
    completed_at: datetime | None


class StreamNegotiateRequest(SQLModel):
    sdp_offer: str
    client_id: str


class StreamNegotiateResponse(SQLModel):
    sdp_answer: str
    session_token: str
    input_channel_id: str


# ---------------------------------------------------------------------------
# Phase 05 — Guardrails, Artifacts, Replay
# ---------------------------------------------------------------------------

class CostPolicy(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", index=True)
    scope: str = Field(max_length=64, default="workspace")
    scope_id: str | None = Field(default=None, max_length=255)
    soft_cap_usd: str | None = Field(default=None, max_length=32)
    hard_cap_usd: str | None = Field(default=None, max_length=32)
    monthly_budget_usd: str | None = Field(default=None, max_length=32)
    action_overrides_json: str | None = Field(default=None, sa_column=Column(Text))
    override_requires_dangerous_mode: bool = Field(default=True)
    created_at: datetime = Field(default_factory=get_datetime_utc, sa_type=DateTime(timezone=True))
    updated_at: datetime = Field(default_factory=get_datetime_utc, sa_type=DateTime(timezone=True))


class Snapshot(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", index=True)
    source_device_id: uuid.UUID = Field(index=True)
    status: str = Field(max_length=64, default="pending")
    provider_snapshot_id: str | None = Field(default=None, max_length=255)
    size_gb: float | None = Field(default=None)
    cost_estimate_usd: str | None = Field(default=None, max_length=32)
    family: str = Field(max_length=64)
    region: str = Field(max_length=64)
    created_at: datetime = Field(default_factory=get_datetime_utc, sa_type=DateTime(timezone=True))
    completed_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))


class Artifact(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", index=True)
    session_id: str | None = Field(default=None, max_length=128)
    run_id: uuid.UUID | None = Field(default=None, index=True)
    evidence_id: uuid.UUID | None = Field(default=None)
    artifact_type: str = Field(max_length=64)
    storage_path: str = Field(max_length=1024)
    size_bytes: int = Field(default=0)
    content_type: str = Field(max_length=128, default="application/octet-stream")
    captured_at: datetime = Field(default_factory=get_datetime_utc, sa_type=DateTime(timezone=True))
    retention_days: int = Field(default=30)
    purge_after: datetime = Field(default_factory=get_datetime_utc, sa_type=DateTime(timezone=True))
    purged: bool = Field(default=False)


class TestRun(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", index=True)
    device_id: uuid.UUID = Field(index=True)
    recipe_id: uuid.UUID | None = Field(default=None)
    recipe_run_id: uuid.UUID | None = Field(default=None)
    status: str = Field(max_length=64, default="pending")
    collect_artifacts: bool = Field(default=True)
    steps_json: str | None = Field(default=None, sa_column=Column(Text))
    summary_json: str | None = Field(default=None, sa_column=Column(Text))
    started_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    completed_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))


# --- Response-only models ---

class CostPolicyPublic(SQLModel):
    id: uuid.UUID
    scope: str
    scope_id: str | None
    soft_cap_usd: str | None
    hard_cap_usd: str | None
    monthly_budget_usd: str | None
    override_requires_dangerous_mode: bool
    created_at: datetime


class CostPolicyCreate(SQLModel):
    scope: str = "workspace"
    scope_id: str | None = None
    soft_cap_usd: str | None = None
    hard_cap_usd: str | None = None
    monthly_budget_usd: str | None = None
    override_requires_dangerous_mode: bool = True


class GuardrailResult(SQLModel):
    decision: str
    message: str
    current_spend_usd: str
    soft_cap_usd: str | None
    hard_cap_usd: str | None
    override_available: bool
    policy_id: str | None


class OrphanResource(SQLModel):
    provider_resource_id: str
    resource_type: str
    region: str
    tags: dict
    estimated_monthly_cost_usd: str
    last_seen_at: datetime


class SnapshotPublic(SQLModel):
    id: uuid.UUID
    source_device_id: uuid.UUID
    status: str
    provider_snapshot_id: str | None
    size_gb: float | None
    cost_estimate_usd: str | None
    family: str
    region: str
    created_at: datetime
    completed_at: datetime | None


class ArtifactPublic(SQLModel):
    id: uuid.UUID
    artifact_type: str
    content_type: str
    size_bytes: int
    captured_at: datetime
    purge_after: datetime
    download_url: str | None = None


class TestRunCreate(SQLModel):
    device_id: uuid.UUID
    recipe_id: uuid.UUID
    collect_artifacts: bool = True


class TestRunPublic(SQLModel):
    id: uuid.UUID
    device_id: uuid.UUID
    recipe_id: uuid.UUID | None
    status: str
    steps_json: str | None
    summary_json: str | None
    started_at: datetime | None
    completed_at: datetime | None


class TimelineEvent(SQLModel):
    timestamp: datetime
    event_type: str
    evidence_id: str | None
    tool: str | None
    params_summary: str | None
    before_screen_version: int | None
    after_screen_version: int | None
    artifact_refs: list[str] = []


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
