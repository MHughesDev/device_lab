---
doc_id: "24.6"
title: "Phase 05 — Guardrails, artifacts, and replay"
section: "Roadmap"
status: "complete"
completion: "100%"
updated: "2026-06-01"
---

# Phase 05 — Guardrails, Artifacts, and Replay

**Progress: 100%** `██████████` — complete

## Objective

Close the safety and accountability loop before broadening device family coverage. Every expensive lifecycle action passes through cost policy. Every test run produces retrievable artifacts. Every MCP action is replayable with full before/after evidence. This phase makes the system defensible — if something goes wrong, you can explain exactly what happened and why.

---

## OSS pulled in this phase

| Package / source | What we take | Where it lands |
|-----------------|-------------|----------------|
| `awspricing` (already in) | Real-time pricing lookups for cost estimate accuracy | `services/cost/guardrail.py` |
| `mitmproxy` (`pip install mitmproxy`) | Embeddable proxy + custom addon for network capture | `adapters/network/proxy.py` |
| `cloud-custodian` (reference only) | Tag-based resource inventory patterns from `c7n/resources/ec2.py` | `services/cost/inventory.py` |

Add to `apps/api/pyproject.toml` dependencies: `"mitmproxy>=10.0.0"`.

---

## Task batches and dependencies

```
Batch A (foundation — run first, everything depends on models)
  05-01  Add phase-05 SQLModel entities to models.py
  05-02  Alembic migration

Batch B (cost layer — depends on A, tasks parallelizable with each other)
  05-03  PricingCache extension
  05-04  CostGuardrail service
  05-05  CloudInventory + orphan detection
  05-06  Cost + orphan API routes + guardrail hook into device FSM

Batch C (snapshots — depends on A, parallel with B)
  05-07  Snapshot service (DB orchestration)
  05-08  Linux EBS snapshot adapter
  05-09  Snapshot API routes

Batch D (network proxy — independent of B and C)
  05-10  NetworkProxy mitmproxy addon

Batch E (artifacts + test runs — depends on A, parallel with B and C)
  05-11  Artifact store service
  05-12  TestRun service + JUnit XML builder
  05-13  TestRun + artifact API routes

Batch F (replay — depends on A and E)
  05-14  Replay service (timeline + evidence cross-reference)
  05-15  Replay + audit-verify API routes

Batch G (tests — write after the service each test covers)
  05-16  Test suite (one file per service)
```

---

## Task 05-01: Add phase-05 SQLModel entities

**Files:** `apps/api/app/models.py` (modify — append before `# Shared` section)

**New table models:**

```python
from decimal import Decimal as _Decimal

class CostPolicy(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", index=True)
    scope: str = Field(max_length=64, default="workspace")   # workspace|device|template|family
    scope_id: str | None = Field(default=None, max_length=255)
    soft_cap_usd: str | None = Field(default=None, max_length=32)   # Decimal as string
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
    status: str = Field(max_length=64, default="pending")   # pending|complete|failed|deleted
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
    run_id: uuid.UUID | None = Field(default=None, index=True)   # RecipeRun or TestRun id
    evidence_id: uuid.UUID | None = Field(default=None)
    artifact_type: str = Field(max_length=64)  # screenshot|log|video|junit|trace|har|recipe_draft
    storage_path: str = Field(max_length=1024)  # s3://bucket/key or local path
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
    status: str = Field(max_length=64, default="pending")  # pending|running|complete|failed
    collect_artifacts: bool = Field(default=True)
    steps_json: str | None = Field(default=None, sa_column=Column(Text))  # [{id, status, duration_ms, artifact_refs}]
    summary_json: str | None = Field(default=None, sa_column=Column(Text))  # {total, passed, failed, skipped}
    started_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    completed_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
```

**New response-only (non-table) models:**

```python
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
    decision: str           # allow|warn|block
    message: str
    current_spend_usd: str
    soft_cap_usd: str | None
    hard_cap_usd: str | None
    override_available: bool
    policy_id: str | None

class OrphanResource(SQLModel):
    provider_resource_id: str
    resource_type: str       # ec2_instance|ebs_volume|ebs_snapshot
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
    download_url: str | None = None   # presigned URL, generated on request

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
    event_type: str           # action|observe|state_change|recipe_step|artifact_captured
    evidence_id: str | None
    tool: str | None
    params_summary: str | None
    before_screen_version: int | None
    after_screen_version: int | None
    artifact_refs: list[str] = []
```

**Do not:** modify any existing model fields. Do not add relationships to table models in this task — keep the entity definitions minimal.

---

## Task 05-02: Alembic migration

**Files:** `apps/api/app/alembic/versions/d5e6f7a8b9c0_devicelab_phase05_guardrails.py` (new)

```python
revision = "d5e6f7a8b9c0"
down_revision = "d4e5f6a7b8c9"
```

**upgrade() creates these tables:**

| Table | Columns |
|-------|---------|
| `costpolicy` | id UUID PK, workspace_id UUID FK→workspace, scope VARCHAR(64), scope_id VARCHAR(255) NULL, soft_cap_usd VARCHAR(32) NULL, hard_cap_usd VARCHAR(32) NULL, monthly_budget_usd VARCHAR(32) NULL, action_overrides_json TEXT NULL, override_requires_dangerous_mode BOOLEAN, created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ |
| `snapshot` | id UUID PK, workspace_id UUID FK→workspace, source_device_id UUID, status VARCHAR(64), provider_snapshot_id VARCHAR(255) NULL, size_gb FLOAT NULL, cost_estimate_usd VARCHAR(32) NULL, family VARCHAR(64), region VARCHAR(64), created_at TIMESTAMPTZ, completed_at TIMESTAMPTZ NULL |
| `artifact` | id UUID PK, workspace_id UUID FK→workspace, session_id VARCHAR(128) NULL, run_id UUID NULL, evidence_id UUID NULL, artifact_type VARCHAR(64), storage_path VARCHAR(1024), size_bytes INT, content_type VARCHAR(128), captured_at TIMESTAMPTZ, retention_days INT, purge_after TIMESTAMPTZ, purged BOOLEAN |
| `testrun` | id UUID PK, workspace_id UUID FK→workspace, device_id UUID, recipe_id UUID NULL, recipe_run_id UUID NULL, status VARCHAR(64), collect_artifacts BOOLEAN, steps_json TEXT NULL, summary_json TEXT NULL, started_at TIMESTAMPTZ NULL, completed_at TIMESTAMPTZ NULL |

**Indexes:** ix_costpolicy_workspace_id, ix_snapshot_workspace_id, ix_snapshot_source_device_id, ix_artifact_workspace_id, ix_artifact_run_id, ix_testrun_workspace_id, ix_testrun_device_id

**Do not:** add any data seed rows. downgrade() drops all four tables in reverse order.

---

## Task 05-03: PricingCache extension

**Files:** `apps/api/app/services/cost/pricing.py` (modify — extend existing file)

The existing file has `get_hourly_price` and `estimate_monthly_cost`. Append:

```python
def get_ebs_snapshot_price_per_gb_month(region: str) -> Decimal:
    """Return EBS snapshot storage price per GB-month for the region.
    Falls back to $0.05/GB-month (us-east-1 standard) if awspricing fails."""
    try:
        import awspricing  # type: ignore[import]
        offer = awspricing.offer("AmazonEC2")
        # awspricing uses service code "AmazonEBS" for storage pricing
        price = offer.storage_price(
            storage_type="Amazon EBS Snapshots to Amazon S3",
            region=region,
        )
        return Decimal(str(price))
    except Exception:
        return Decimal("0.05")


def get_data_transfer_price_per_gb(region: str) -> Decimal:
    """Return outbound data transfer price per GB for the region."""
    try:
        import awspricing  # type: ignore[import]
        offer = awspricing.offer("AWSDataTransfer")
        price = offer.data_transfer_price(region=region, transfer_type="DataTransfer-Out-Bytes")
        return Decimal(str(price))
    except Exception:
        return Decimal("0.09")


def estimate_snapshot_cost(region: str, size_gb: float, retention_days: int = 30) -> Decimal:
    """Estimate cost for keeping a snapshot for retention_days."""
    price_per_gb_month = get_ebs_snapshot_price_per_gb_month(region)
    months = Decimal(str(retention_days)) / Decimal("30")
    return (price_per_gb_month * Decimal(str(size_gb)) * months).quantize(Decimal("0.01"))
```

**Tests (`tests/services/test_pricing.py` — new):**
| Test | Asserts |
|------|---------|
| `test_get_hourly_price_fallback` | returns a positive Decimal when awspricing raises |
| `test_estimate_monthly_cost` | result = hourly × 730, rounded to cents |
| `test_get_ebs_snapshot_price_fallback` | returns Decimal("0.05") when awspricing raises |
| `test_estimate_snapshot_cost` | 100 GB × 30 days = price_per_gb × 100 × 1.0 |

---

## Task 05-04: CostGuardrail service

**Files:** `apps/api/app/services/cost/guardrail.py` (new)

```python
from __future__ import annotations
from decimal import Decimal
import uuid
from sqlmodel import Session, select
from app.models import CostPolicy, Device, GuardrailResult
from app.core.audit_log import append_event


COST_CLASS: dict[str, str] = {
    "provision": "moderate",
    "start": "cheap",
    "snapshot": "moderate",
    "fork": "expensive",
    "recipe_long": "moderate",
    "terminate": "free",
    "stop": "free",
}


def check(
    db: Session,
    workspace_id: uuid.UUID,
    action: str,
    device: Device,
    estimated_cost_usd: Decimal,
    current_spend_usd: Decimal,
) -> GuardrailResult:
    """
    Evaluate action against workspace cost policy. Always appends an AuditEvent
    for expensive-class or blocked decisions.

    Returns GuardrailResult with decision = "allow" | "warn" | "block".
    """
    ...


def _load_policy(db: Session, workspace_id: uuid.UUID, device: Device) -> CostPolicy | None:
    """Return most-specific policy: device > template > family > workspace."""
    ...
```

**Full logic for `check()`:**
1. Load policy via `_load_policy`. If no policy exists, treat as no caps (allow + no warn).
2. Compute projected total = `current_spend_usd + estimated_cost_usd`.
3. Decision matrix:
   - projected_total >= hard_cap AND hard_cap is set → `block`, override_available = policy.override_requires_dangerous_mode
   - projected_total >= soft_cap AND soft_cap is set → `warn`
   - else → `allow`
4. If decision is `block` or action cost_class is `expensive`, call `append_event(db, workspace_id=workspace_id, actor="guardrail", action="cost_check", target_type="Device", target_id=str(device.id), decision=decision, metadata={...})`.
5. Return `GuardrailResult`.

**Tests (`tests/services/test_guardrail.py` — new):**
| Test | Asserts |
|------|---------|
| `test_allow_below_soft_cap` | decision == "allow" when spend < soft_cap |
| `test_warn_at_soft_cap` | decision == "warn" when spend >= soft_cap |
| `test_block_at_hard_cap` | decision == "block" when spend >= hard_cap |
| `test_no_policy_allows` | decision == "allow" when no policy exists |
| `test_block_appends_audit_event` | AuditEvent row created in DB for block decision |
| `test_override_available_flag` | override_available matches policy.override_requires_dangerous_mode |

Use in-memory SQLite + mocked `append_event` to isolate from keyring/AWS.

---

## Task 05-05: CloudInventory + orphan detection

**Files:** `apps/api/app/services/cost/inventory.py` (new)

```python
from __future__ import annotations
import uuid
from datetime import UTC, datetime
from sqlmodel import Session, select
from app.models import Device, OrphanResource


DEVICELAB_TAG_KEY = "DeviceLab:Workspace"


def list_tagged_resources(workspace_id: uuid.UUID, region: str, boto_session=None) -> list[dict]:
    """
    Return all EC2 instances + EBS volumes tagged DeviceLab:Workspace={workspace_id}.
    boto_session is injectable for tests (pass a fake/mocked session).
    """
    ...


def detect_orphans(
    db: Session,
    workspace_id: uuid.UUID,
    region: str,
    boto_session=None,
) -> list[OrphanResource]:
    """
    Compare tagged AWS resources against Device table.
    Resources tagged for this workspace but absent from DB = orphan candidates.
    Returns list[OrphanResource] sorted by estimated_monthly_cost_usd descending.
    """
    ...


def cleanup_orphan(resource_id: str, resource_type: str, region: str, boto_session=None) -> None:
    """
    Terminate/delete a single orphan resource. Caller must confirm dangerous_mode before calling.
    Raises ValueError if resource_type is not supported.
    """
    ...
```

**Implementation notes for `list_tagged_resources`:**
- Use `boto3.client("ec2").describe_instances(Filters=[{"Name": "tag:" + DEVICELAB_TAG_KEY, "Values": [str(workspace_id)]}])`
- Also `describe_volumes` with same tag filter
- Return raw resource dicts with at minimum: `resource_id`, `resource_type`, `tags`, `region`

**Tests (`tests/services/test_inventory.py` — new):**
| Test | Asserts |
|------|---------|
| `test_list_tagged_resources_empty` | returns [] when boto returns no instances |
| `test_detect_orphans_none` | returns [] when all tagged resources have matching Device rows |
| `test_detect_orphans_finds_untracked` | returns OrphanResource for instance not in Device table |
| `test_cleanup_orphan_terminates_instance` | calls boto3 terminate_instances for ec2_instance type |
| `test_cleanup_orphan_unknown_type_raises` | raises ValueError for unknown resource_type |

Use `unittest.mock.patch("boto3.client")` to inject fake responses.

---

## Task 05-06: Cost + orphan API routes + FSM guardrail hook

**Files:**
- `apps/api/app/api/routes/cost.py` (new)
- `apps/api/app/services/device_fsm.py` (modify — add guardrail check before provisioning)
- `apps/api/app/api/main.py` (modify — add `cost` to imports and include_router)

**`cost.py` endpoints:**

```
GET  /api/v1/cost/policies
     response: list[CostPolicyPublic]

POST /api/v1/cost/policies
     body: CostPolicyCreate
     response: CostPolicyPublic, 201

PUT  /api/v1/cost/policies/{policy_id}
     body: CostPolicyCreate
     response: CostPolicyPublic

DELETE /api/v1/cost/policies/{policy_id}
     response: 204

GET  /api/v1/cost/orphans?region={region}
     response: list[OrphanResource]
     calls: inventory.detect_orphans()

POST /api/v1/cost/orphans/{resource_id}/cleanup
     body: { resource_type: str, region: str }
     requires: settings.DANGEROUS_MODE == True, else 403
     calls: inventory.cleanup_orphan()
     side-effect: append_event(action="orphan_cleanup", ...)
     response: { cleaned: true }
```

**FSM guardrail hook in `device_fsm.py`:**

In the `trigger_transition` function (or equivalent), before the `requested → provisioning` transition:
1. Call `guardrail.check(db, workspace_id, "provision", device, estimated_cost, current_spend)`
2. If result.decision == "block" → raise `GuardrailBlocked(result.message)` instead of transitioning
3. If result.decision == "warn" → log warning but allow transition

**`main.py` modification:** add `cost` to imports and `api_router.include_router(cost.router)`.

---

## Task 05-07: Snapshot service

**Files:** `apps/api/app/services/snapshots.py` (new)

```python
from __future__ import annotations
import uuid
from datetime import UTC, datetime
from sqlmodel import Session
from app.models import Device, Snapshot


SNAPSHOT_CAPABLE_FAMILIES = {"linux"}


async def create_snapshot(
    db: Session,
    workspace_id: uuid.UUID,
    device_id: uuid.UUID,
    boto_session=None,
) -> Snapshot:
    """
    Initiates an EBS snapshot for a Linux device.
    For non-snapshotable families raises CapabilityUnsupportedError.
    Returns a Snapshot in "pending" status immediately; polling completes it.
    """
    ...


async def poll_snapshot_status(
    db: Session,
    snapshot_id: uuid.UUID,
    boto_session=None,
) -> Snapshot:
    """
    Calls DescribeSnapshots for the provider_snapshot_id.
    Updates Snapshot.status to "complete" or "failed" and sets size_gb, completed_at.
    """
    ...


async def fork_from_snapshot(
    db: Session,
    snapshot_id: uuid.UUID,
    workspace_id: uuid.UUID,
    template_overrides: dict,
    boto_session=None,
) -> Device:
    """
    Launch a new EC2 instance from a snapshot (RunInstances with block device mapping).
    Creates a Device in "provisioning" state with forked_from tag.
    """
    ...


async def delete_snapshot(
    db: Session,
    snapshot_id: uuid.UUID,
    workspace_id: uuid.UUID,
    boto_session=None,
) -> None:
    """
    Calls EBS DeleteSnapshot. Marks Snapshot.status = "deleted".
    Raises ValueError for snapshots < 24h old unless dangerous_mode.
    """
    ...


class CapabilityUnsupportedError(Exception):
    def __init__(self, capability: str, family: str):
        self.capability = capability
        self.family = family
        super().__init__(f"CAPABILITY_UNSUPPORTED: {capability} not available for family {family}")
```

**Tests (`tests/services/test_snapshots.py` — new):**
| Test | Asserts |
|------|---------|
| `test_create_snapshot_browser_raises` | CapabilityUnsupportedError for browser family |
| `test_create_snapshot_linux_pending` | returns Snapshot with status="pending" |
| `test_poll_snapshot_status_completes` | mocked DescribeSnapshots → status="complete", size_gb set |
| `test_delete_snapshot_young_requires_dangerous` | raises ValueError if < 24h old and not dangerous |
| `test_fork_creates_device` | creates Device row in "provisioning" state |

---

## Task 05-08: Linux EBS snapshot adapter

**Files:** `apps/api/app/adapters/linux/snapshots.py` (new)

```python
from __future__ import annotations


def get_root_volume_id(instance_id: str, region: str, boto_session=None) -> str:
    """
    Describe EC2 instance and return the root EBS volume ID.
    Raises ValueError if no root volume found.
    """
    ...


def create_ebs_snapshot(
    volume_id: str,
    region: str,
    tags: dict[str, str],
    boto_session=None,
) -> str:
    """
    Call ec2.create_snapshot(VolumeId=volume_id, TagSpecifications=[...]).
    Returns the SnapshotId string.
    tags must include at minimum DeviceLab:Workspace and DeviceLab:Device.
    """
    ...


def describe_ebs_snapshot(
    snapshot_id: str,
    region: str,
    boto_session=None,
) -> dict:
    """
    Call ec2.describe_snapshots(SnapshotIds=[snapshot_id]).
    Returns dict with keys: status (pending|completed|error), volume_size (int), start_time.
    """
    ...


def delete_ebs_snapshot(snapshot_id: str, region: str, boto_session=None) -> None:
    """Call ec2.delete_snapshot(SnapshotId=snapshot_id)."""
    ...
```

---

## Task 05-09: Snapshot API routes

**Files:**
- `apps/api/app/api/routes/snapshots.py` (new)
- `apps/api/app/api/main.py` (modify — add `snapshots` to imports and include_router)

**Endpoints:**

```
POST /api/v1/devices/{device_id}/snapshot
     response: SnapshotPublic, 201
     calls: snapshots.create_snapshot()
     error: 422 with { error: "CAPABILITY_UNSUPPORTED", capability: "snapshot", family: str }
            if CapabilityUnsupportedError raised

GET  /api/v1/snapshots/{snapshot_id}
     response: SnapshotPublic
     calls: db.get(Snapshot, snapshot_id), also calls poll_snapshot_status if status=="pending"

POST /api/v1/snapshots/{snapshot_id}/fork
     body: { template_overrides: dict = {} }
     response: DevicePublic, 201
     calls: snapshots.fork_from_snapshot()

DELETE /api/v1/snapshots/{snapshot_id}
     response: 204
     calls: snapshots.delete_snapshot()
     requires: settings.DANGEROUS_MODE for snapshots > 24h old
```

---

## Task 05-10: NetworkProxy mitmproxy addon

**Files:**
- `apps/api/app/adapters/network/__init__.py` (new, empty)
- `apps/api/app/adapters/network/proxy.py` (new)

```python
from __future__ import annotations
import asyncio
import uuid
from typing import Any

# mitmproxy imports are guarded so the module can be imported even if mitmproxy
# is not installed — the proxy is opt-in per session.
try:
    import mitmproxy.http  # type: ignore[import]
    from mitmproxy.options import Options  # type: ignore[import]
    from mitmproxy.tools.dump import DumpMaster  # type: ignore[import]
    _MITMPROXY_AVAILABLE = True
except ImportError:
    _MITMPROXY_AVAILABLE = False


class DeviceLabAddon:
    """mitmproxy addon — tags flows with device context and applies policy."""

    def __init__(self, device_id: uuid.UUID, session_id: str, capture: bool = True):
        self.device_id = device_id
        self.session_id = session_id
        self.capture = capture
        self.captured_flows: list[dict] = []

    def request(self, flow: Any) -> None:
        """Tag and optionally capture outbound request."""
        ...

    def response(self, flow: Any) -> None:
        """Capture response if enabled; store as artifact reference."""
        ...


class NetworkProxy:
    def __init__(self, device_id: uuid.UUID, session_id: str, port: int = 8080):
        self.device_id = device_id
        self.session_id = session_id
        self.port = port
        self._master: Any = None

    async def start(self) -> None:
        """Start the mitmproxy DumpMaster in a background thread. Raises if unavailable."""
        if not _MITMPROXY_AVAILABLE:
            raise RuntimeError("mitmproxy not installed — pip install mitmproxy")
        ...

    async def stop(self) -> None:
        """Shut down the proxy master cleanly."""
        ...

    def get_captured_flows(self) -> list[dict]:
        return self._addon.captured_flows if self._addon else []


def is_available() -> bool:
    return _MITMPROXY_AVAILABLE
```

**Tests (`tests/adapters/test_network_proxy.py` — new):**
| Test | Asserts |
|------|---------|
| `test_is_available_returns_bool` | returns True or False without raising |
| `test_proxy_unavailable_raises` | start() raises RuntimeError when mitmproxy not installed (mock `_MITMPROXY_AVAILABLE = False`) |
| `test_addon_captures_flow` | DeviceLabAddon.response() appends to captured_flows when capture=True |
| `test_addon_skips_capture` | captured_flows stays empty when capture=False |

---

## Task 05-11: Artifact store service

**Files:** `apps/api/app/services/artifacts.py` (new)

```python
from __future__ import annotations
import uuid
from datetime import UTC, datetime, timedelta
from sqlmodel import Session, select
from app.models import Artifact


def store_artifact(
    db: Session,
    workspace_id: uuid.UUID,
    artifact_type: str,
    storage_path: str,
    content_type: str,
    size_bytes: int,
    run_id: uuid.UUID | None = None,
    evidence_id: uuid.UUID | None = None,
    session_id: str | None = None,
    retention_days: int = 30,
) -> Artifact:
    """Persist artifact metadata. Does NOT upload — caller handles storage."""
    ...


def get_presigned_download_url(
    artifact: Artifact,
    expires_in_seconds: int = 3600,
    boto_session=None,
) -> str:
    """
    Generate a presigned GET URL for an S3-stored artifact.
    For non-S3 storage_path (local dev), returns the path string directly.
    """
    ...


def list_artifacts(
    db: Session,
    workspace_id: uuid.UUID,
    run_id: uuid.UUID | None = None,
    evidence_id: uuid.UUID | None = None,
) -> list[Artifact]:
    """Return artifacts matching filters, excluding purged=True rows."""
    ...


def purge_expired(db: Session, workspace_id: uuid.UUID) -> int:
    """
    Mark all artifacts past their purge_after date as purged=True.
    Returns count of rows marked. Does NOT delete S3 objects (lifecycle rule handles that).
    """
    ...
```

**Tests (`tests/services/test_artifacts.py` — new):**
| Test | Asserts |
|------|---------|
| `test_store_artifact_persists` | Artifact row exists in DB after call |
| `test_list_artifacts_excludes_purged` | purged=True rows not returned |
| `test_list_artifacts_by_run_id` | only returns artifacts with matching run_id |
| `test_purge_expired_marks_rows` | rows past purge_after get purged=True |
| `test_purge_expired_skips_fresh` | rows before purge_after unchanged |
| `test_presigned_url_local_path` | non-S3 path returned as-is without boto3 call |

---

## Task 05-12: TestRun service + JUnit XML builder

**Files:** `apps/api/app/services/test_runs.py` (new)

```python
from __future__ import annotations
import json
import uuid
from datetime import UTC, datetime
from xml.etree import ElementTree as ET
from sqlmodel import Session
from app.models import TestRun, TestRunCreate
from app.services.recipes.runner import run_recipe


async def create_test_run(
    db: Session,
    workspace_id: uuid.UUID,
    body: TestRunCreate,
) -> TestRun:
    """
    Create TestRun record, start recipe execution via run_recipe(), populate steps_json
    and summary_json from the RecipeRun result. Update TestRun.status on completion.
    """
    ...


def get_test_run(db: Session, run_id: uuid.UUID) -> TestRun | None:
    return db.get(TestRun, run_id)


def build_junit_xml(run: TestRun) -> str:
    """
    Produce JUnit XML string from a completed TestRun.

    Format:
    <testsuite name="{recipe_name}" tests="{n}" failures="{f}" time="{total_s}">
      <testcase name="{step_id}" time="{step_s}">
        <failure message="{error}" type="{error_code}" />  <!-- only if failed -->
      </testcase>
    </testsuite>
    """
    ...


def build_summary(steps: list[dict]) -> dict:
    """Return {total, passed, failed, skipped} counts from steps_json list."""
    total = len(steps)
    failed = sum(1 for s in steps if s.get("status") == "failed")
    return {"total": total, "passed": total - failed, "failed": failed, "skipped": 0}
```

**Tests (`tests/services/test_test_runs.py` — new):**
| Test | Asserts |
|------|---------|
| `test_build_summary_all_pass` | passed=3, failed=0 for 3 passing steps |
| `test_build_summary_one_fail` | failed=1 for one failed step |
| `test_build_junit_xml_parseable` | output is valid XML, has `<testsuite>` root |
| `test_build_junit_xml_failure_element` | failed step produces `<failure>` child element |
| `test_build_junit_xml_no_failure_on_pass` | passing step has no `<failure>` child |

---

## Task 05-13: TestRun + artifact API routes

**Files:**
- `apps/api/app/api/routes/test_runs.py` (new)
- `apps/api/app/api/main.py` (modify — add `test_runs` to imports and include_router)

**Endpoints:**

```
POST /api/v1/test-runs
     body: TestRunCreate
     response: TestRunPublic, 201
     calls: test_runs.create_test_run()

GET  /api/v1/test-runs/{run_id}
     response: TestRunPublic
     calls: test_runs.get_test_run()

GET  /api/v1/test-runs/{run_id}/artifacts
     response: list[ArtifactPublic]
     calls: artifacts.list_artifacts(run_id=run_id), generates presigned URLs

GET  /api/v1/test-runs/{run_id}/junit
     response: XML string with Content-Type: application/xml
     calls: test_runs.build_junit_xml()

GET  /api/v1/artifacts/{artifact_id}
     response: ArtifactPublic with download_url
     calls: artifacts.get_presigned_download_url()
```

---

## Task 05-14: Replay service

**Files:** `apps/api/app/services/replay.py` (new)

```python
from __future__ import annotations
import uuid
from sqlmodel import Session, select
from app.models import AuditEvent, Evidence, Artifact, RecipeRun, TimelineEvent


def build_session_timeline(
    db: Session,
    workspace_id: uuid.UUID,
    session_id: str,
) -> list[TimelineEvent]:
    """
    Return all Evidence records for the session, joined with AuditEvent and Artifact refs,
    ordered by created_at ascending.
    Each evidence record becomes one TimelineEvent.
    """
    ...


def build_evidence_detail(
    db: Session,
    evidence_id: uuid.UUID,
) -> dict:
    """
    Return Evidence record + observation_before (from observation_before_ref) +
    observation_after (from observation_after_ref) + list of Artifact rows
    whose evidence_id matches.
    """
    ...


def replay_as_recipe_draft(
    db: Session,
    evidence_id: uuid.UUID,
) -> str:
    """
    Fetch the Evidence record and produce a single-step recipe YAML draft.
    Uses recorder.build_recipe_draft([evidence]) under the hood.
    Caller must present draft to human for review before executing.
    """
    from app.services.recipes.recorder import build_recipe_draft
    ...
```

**Tests (`tests/services/test_replay.py` — new):**
| Test | Asserts |
|------|---------|
| `test_build_session_timeline_orders_by_time` | events sorted ascending by created_at |
| `test_build_session_timeline_empty` | returns [] for unknown session |
| `test_build_evidence_detail_has_artifacts` | artifact refs included when matching evidence_id |
| `test_replay_as_recipe_draft_valid_yaml` | returns parseable YAML |
| `test_replay_as_recipe_draft_one_step` | draft has exactly one step |

---

## Task 05-15: Replay + audit-verify API routes

**Files:**
- `apps/api/app/api/routes/replay.py` (new)
- `apps/api/app/api/main.py` (modify — add `replay` to imports and include_router)

**Endpoints:**

```
GET  /api/v1/sessions/{session_id}/timeline
     response: list[TimelineEvent]
     calls: replay.build_session_timeline()

GET  /api/v1/evidence/{evidence_id}
     response: dict (Evidence + observation refs + artifact_refs)
     calls: replay.build_evidence_detail()

POST /api/v1/evidence/{evidence_id}/replay
     response: { draft_yaml: str, warning: str }
     calls: replay.replay_as_recipe_draft()
     note: never auto-executes; returns draft for human review

GET  /api/v1/audit/verify
     response: { valid: bool, chain_length: int, first_broken_at: str | null }
     calls: audit_log.verify_chain()
     note: workspace_id resolved from the first workspace in DB
```

---

## Task 05-16: Full test suite

Run after all services are implemented. Ensure each test file exists with the tests listed in its task spec. Verify all tests import correctly with no circular imports.

**All test files for this phase:**
- `tests/services/test_pricing.py` — task 05-03
- `tests/services/test_guardrail.py` — task 05-04
- `tests/services/test_inventory.py` — task 05-05
- `tests/services/test_snapshots.py` — task 05-07
- `tests/services/test_artifacts.py` — task 05-11
- `tests/services/test_test_runs.py` — task 05-12
- `tests/services/test_replay.py` — task 05-14
- `tests/adapters/test_network_proxy.py` — task 05-10

All tests use in-memory SQLite (`create_engine("sqlite:///:memory:")`) and `unittest.mock.patch` for boto3 and keyring. No real AWS calls.

---

## Security invariants (all must have tests or route-level assertions)

- `GET /api/v1/cost/orphans` and `/cleanup` require `CurrentUser` auth
- Orphan cleanup requires `settings.DANGEROUS_MODE == True`, returns 403 otherwise
- Snapshot delete for snapshots > 24h requires `settings.DANGEROUS_MODE == True`
- Presigned artifact URLs expire in ≤ 1 hour
- No Artifact row is deleted — only `purged = True` is set

---

## Exit criteria

- Device provisioned above hard cap is blocked with `GuardrailBlocked` error and clear remediation
- Soft cap warning appears in the guardrail API response for devices above threshold
- Snapshot creates and forks successfully for Linux; returns `CAPABILITY_UNSUPPORTED` for browser
- TestRun produces valid JUnit XML for a 3-step recipe
- Artifact retrieval returns a presigned URL (or local path in dev) within retention window
- Replay timeline orders all evidence records for a session correctly by timestamp
- HMAC chain verify detects a tampered audit event (set `hash = "tampered"` in test)
- Orphan detection returns resources tagged for workspace but absent from Device table
- Orphan cleanup blocked without `DANGEROUS_MODE=true`
