import json
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    CloudAccount,
    Device,
    DeviceCreate,
    DeviceLifecycleEvent,
    DevicePublic,
    DeviceTemplate,
    Message,
    Workspace,
)
from app.services.device_fsm import get_device_fsm
from app.services.templates import ensure_seed_templates

router = APIRouter(prefix="/devices", tags=["devices"])


def _get_workspace(db) -> Workspace:
    ws = db.exec(select(Workspace).limit(1)).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not initialised")
    return ws


def _to_public(d: Device) -> DevicePublic:
    return DevicePublic(
        id=d.id,
        family=d.family,
        location=d.location,
        name=d.name,
        display_mode=d.display_mode,
        mcp_exposed=d.mcp_exposed,
        state=d.state,
        phase=d.phase,
        cost_estimate=d.cost_estimate,
        created_at=d.created_at,
        updated_at=d.updated_at,
    )


async def _run_linux_lifecycle(device_id: uuid.UUID, account_id: uuid.UUID, region: str) -> None:
    """Background task: drive linux device through FSM to ready."""
    from app.core.db import engine
    from sqlmodel import Session

    with Session(engine) as db:
        device = db.get(Device, device_id)
        account = db.get(CloudAccount, account_id)
        template = db.get(DeviceTemplate, device.template_id) if device and device.template_id else None
        if not device or not account or not template:
            return

        from app.adapters.aws.client import AWSClient
        from app.adapters.linux.adapter import LinuxAdapter
        from app.services.cost.pricing import estimate_monthly_cost

        fsm = get_device_fsm(device, db)
        client = AWSClient(
            credential_source=account.credential_source,
            profile=account.credential_profile,
            role_arn=account.credential_role_arn,
            region=region,
        )
        adapter = LinuxAdapter(client, region)

        try:
            fsm.transition("preflight_pass")

            cost = estimate_monthly_cost(region, "t3.medium")
            device.cost_estimate = float(cost)
            db.add(device)
            db.commit()

            provider_ids = await adapter.provision(device, template)
            device.provider_ids_json = json.dumps({
                "instance_id": provider_ids.instance_id,
                "region": provider_ids.region,
            })
            db.add(device)
            db.commit()

            fsm.transition("provision_done")

            await adapter.wait_for_running(provider_ids.instance_id)
            await adapter.bootstrap_agent(provider_ids.instance_id)
            fsm.transition("agent_ready")

        except Exception as e:
            device = db.get(Device, device_id)
            if device:
                fsm2 = get_device_fsm(device, db)
                try:
                    fsm2.transition("fail")
                except Exception:
                    pass


@router.post("/", response_model=DevicePublic, status_code=202)
def create_device(
    db: SessionDep, body: DeviceCreate, background: BackgroundTasks
) -> DevicePublic:
    ensure_seed_templates(db)
    ws = _get_workspace(db)

    template = db.get(DeviceTemplate, body.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    account: CloudAccount | None = None
    region = body.region or "us-east-1"

    if template.family == "linux":
        if not body.cloud_account_id:
            raise HTTPException(status_code=400, detail="cloud_account_id required for linux family")
        account = db.get(CloudAccount, body.cloud_account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Cloud account not found")
        region = body.region or account.region

    # Phase 10: create-from-manifest inherits name from manifest if not supplied
    manifest = None
    if body.manifest_id:
        from app.models import DeviceManifest
        manifest = db.get(DeviceManifest, body.manifest_id)
        if not manifest:
            raise HTTPException(status_code=404, detail="Manifest not found")

    device = Device(
        template_id=template.id,
        workspace_id=ws.id,
        family=template.family,
        location=body.location,
        name=body.name or (manifest.name if manifest else None),
        display_mode=body.display_mode,
        mcp_exposed=body.mcp_exposed,
        source_manifest_id=body.manifest_id,
        state="requested",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(device)
    db.commit()
    db.refresh(device)

    if template.family == "linux" and account:
        background.add_task(_run_linux_lifecycle, device.id, account.id, region)

    return _to_public(device)


@router.get("/", response_model=list[DevicePublic])
def list_devices(db: SessionDep) -> list[DevicePublic]:
    ws = _get_workspace(db)
    devices = db.exec(select(Device).where(Device.workspace_id == ws.id)).all()
    return [_to_public(d) for d in devices]


@router.get("/{device_id}", response_model=DevicePublic)
def get_device(db: SessionDep, device_id: uuid.UUID) -> DevicePublic:
    device = db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return _to_public(device)


@router.get("/{device_id}/events", response_model=list[DeviceLifecycleEvent])
def get_device_events(db: SessionDep, device_id: uuid.UUID) -> list[DeviceLifecycleEvent]:
    device = db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if not device.provider_ids_json:
        return []
    ids = json.loads(device.provider_ids_json)
    if not ids.get("instance_id"):
        return []
    from app.adapters.aws.client import AWSClient
    from app.adapters.linux.adapter import LinuxAdapter

    ws = _get_workspace(db)
    accounts = db.exec(select(CloudAccount).where(CloudAccount.workspace_id == ws.id)).all()
    if not accounts:
        return []
    account = accounts[0]
    client = AWSClient(credential_source=account.credential_source, region=account.region)
    adapter = LinuxAdapter(client, account.region)
    events = adapter.get_lifecycle_events(ids["instance_id"])
    return [DeviceLifecycleEvent(event_type=e.event_type, timestamp=e.timestamp, message=e.message) for e in events]


def _lifecycle_action(db: SessionDep, device_id: uuid.UUID, trigger: str) -> DevicePublic:
    device = db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    try:
        get_device_fsm(device, db).transition(trigger)
    except Exception as e:
        raise HTTPException(status_code=409, detail=f"Transition '{trigger}' not valid from state '{device.state}': {e}") from e
    return _to_public(device)


@router.post("/{device_id}/lifecycle/stop", response_model=DevicePublic)
def stop_device(db: SessionDep, device_id: uuid.UUID) -> DevicePublic:
    return _lifecycle_action(db, device_id, "stop")


@router.post("/{device_id}/lifecycle/start", response_model=DevicePublic)
def start_device(db: SessionDep, device_id: uuid.UUID) -> DevicePublic:
    return _lifecycle_action(db, device_id, "start")


@router.post("/{device_id}/lifecycle/terminate", response_model=DevicePublic)
def terminate_device(db: SessionDep, device_id: uuid.UUID, background: BackgroundTasks) -> DevicePublic:
    device = db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    fsm = get_device_fsm(device, db)
    try:
        fsm.transition("terminate")
    except Exception as e:
        raise HTTPException(status_code=409, detail=str(e)) from e

    if device.provider_ids_json and device.family == "linux":
        ids = json.loads(device.provider_ids_json)
        if ids.get("instance_id"):
            async def _terminate_bg(device_id: uuid.UUID) -> None:
                from app.core.db import engine
                from sqlmodel import Session
                with Session(engine) as inner_db:
                    d = inner_db.get(Device, device_id)
                    if not d:
                        return
                    ws = inner_db.exec(select(Workspace).limit(1)).first()
                    if not ws:
                        return
                    accounts = inner_db.exec(select(CloudAccount).where(CloudAccount.workspace_id == ws.id)).all()
                    if not accounts:
                        return
                    account = accounts[0]
                    from app.adapters.aws.client import AWSClient
                    from app.adapters.linux.adapter import LinuxAdapter
                    client = AWSClient(credential_source=account.credential_source, region=account.region)
                    adapter = LinuxAdapter(client, account.region)
                    await adapter.terminate(d)
                    get_device_fsm(d, inner_db).transition("terminate_done")

            background.add_task(_terminate_bg, device.id)

    return _to_public(device)


@router.post("/{device_id}/heartbeat", response_model=Message)
def device_heartbeat(db: SessionDep, device_id: uuid.UUID) -> Message:
    device = db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    device.updated_at = datetime.now(UTC)
    db.add(device)
    db.commit()
    return Message(message="ok")


@router.post("/{device_id}/manifest/capture", status_code=201)
async def capture_device_manifest(
    db: SessionDep,
    device_id: uuid.UUID,
    _current_user: CurrentUser,
) -> dict:
    """Introspect a running device and save a new DeviceManifest in the registry."""
    from app.adapters.spi import CapabilityUnsupportedError
    from app.models import ManifestCreate
    from app.services.manifest_registry import create_manifest
    import json as _json

    device = db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if device.state != "ready":
        raise HTTPException(status_code=409, detail=f"Device is not ready (state={device.state})")

    try:
        from app.adapters.registry import AdapterRegistry
        adapter_cls = AdapterRegistry.get(device.family)
        # Instantiate without cloud credentials for local capture path
        adapter = adapter_cls.__new__(adapter_cls)  # type: ignore[misc]
        spec = await adapter.capture_manifest(device)
    except KeyError:
        raise HTTPException(status_code=400, detail=f"No adapter registered for family '{device.family}'")
    except CapabilityUnsupportedError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Capture failed: {e}")

    body = ManifestCreate(
        workspace_id=device.workspace_id,
        name=f"{device.name or device.family} (captured)",
        family=device.family,
        location=device.location,
        description=f"Captured from device {device_id}",
        spec_json=_json.dumps(spec),
        source_device_id=device_id,
    )
    manifest = create_manifest(db, body)
    return {
        "manifest_id": str(manifest.id),
        "name": manifest.title,
        "family": manifest.family,
    }


# ── Phase 11: rename + file push/pull ─────────────────────────────────────────

class DevicePatch(BaseModel):
    name: str | None = None
    display_mode: str | None = None
    mcp_exposed: bool | None = None


@router.patch("/{device_id}", response_model=DevicePublic)
def patch_device(
    db: SessionDep,
    device_id: uuid.UUID,
    patch: DevicePatch,
    _current_user: CurrentUser,
) -> DevicePublic:
    """Update mutable device fields (name, display_mode, mcp_exposed)."""
    device = db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if patch.name is not None:
        device.name = patch.name.strip() or None
    if patch.display_mode is not None:
        if patch.display_mode not in ("headless", "interactive"):
            raise HTTPException(status_code=422, detail="display_mode must be headless or interactive")
        device.display_mode = patch.display_mode
    if patch.mcp_exposed is not None:
        device.mcp_exposed = patch.mcp_exposed
    device.updated_at = datetime.now(UTC)
    db.add(device)
    db.commit()
    db.refresh(device)
    return _to_public(device)


@router.post("/{device_id}/files/push", status_code=200)
async def push_file(
    db: SessionDep,
    device_id: uuid.UUID,
    file: UploadFile,
    remote_path: str = "/tmp/",
    _current_user: CurrentUser = None,
) -> dict:
    """Push a local file to the device via the channel."""
    device = db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if device.state != "ready":
        raise HTTPException(status_code=409, detail="Device is not ready")

    data = await file.read()
    if len(data) > 500 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds 500 MB limit")

    dest = remote_path if not remote_path.endswith("/") else remote_path + file.filename

    try:
        from app.adapters.registry import AdapterRegistry
        from app.stream.factory import media_source_for
        adapter_cls = AdapterRegistry.get(device.family)
        adapter = adapter_cls.__new__(adapter_cls)
        ch = await adapter.get_channel(device)
        await ch.push_file(data, dest)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File push failed: {e}")

    return {"remote_path": dest, "bytes": len(data)}


@router.get("/{device_id}/files/pull")
async def pull_file(
    db: SessionDep,
    device_id: uuid.UUID,
    path: str,
    _current_user: CurrentUser = None,
) -> Response:
    """Pull a file from the device."""
    device = db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if device.state != "ready":
        raise HTTPException(status_code=409, detail="Device is not ready")

    try:
        from app.adapters.registry import AdapterRegistry
        adapter_cls = AdapterRegistry.get(device.family)
        adapter = adapter_cls.__new__(adapter_cls)
        ch = await adapter.get_channel(device)
        data = await ch.pull_file(path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File pull failed: {e}")

    fname = path.split("/")[-1] or "file"
    return Response(
        content=data,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )
