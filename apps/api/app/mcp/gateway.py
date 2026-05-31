"""
DeviceLab MCP gateway — FastMCP server mounted at /mcp.
Tools are organized by function group; manifest filtering happens per-session.
"""
import uuid

from mcp.server.fastmcp import FastMCP

from app.mcp.manifest import build_manifest
from app.mcp.permissions import Role, parse_role

mcp = FastMCP("DeviceLab")


# ---------------------------------------------------------------------------
# Inventory tools
# ---------------------------------------------------------------------------

@mcp.tool()
def workspace_status() -> dict:
    """Return workspace capabilities, version, and cloud account status."""
    from app.core.db import engine
    from sqlmodel import Session, select
    from app.models import CloudAccount, Device, Workspace
    from app.core.config import VERSION, settings

    with Session(engine) as db:
        ws = db.exec(select(Workspace).limit(1)).first()
        if not ws:
            return {"error": "Workspace not initialised"}
        accounts = db.exec(select(CloudAccount).where(CloudAccount.workspace_id == ws.id)).all()
        return {
            "workspace_id": str(ws.id),
            "name": ws.name,
            "version": VERSION,
            "bind_host": settings.BIND_HOST,
            "dangerous_mode": settings.DANGEROUS_MODE,
            "cloud_accounts": [
                {"id": str(a.id), "provider": a.provider, "status": a.status}
                for a in accounts
            ],
        }


@mcp.tool()
def list_devices(state: str | None = None, family: str | None = None) -> list[dict]:
    """List all devices and their current lifecycle state. Optionally filter by state or family."""
    from app.core.db import engine
    from sqlmodel import Session, select
    from app.models import Device, Workspace

    with Session(engine) as db:
        ws = db.exec(select(Workspace).limit(1)).first()
        if not ws:
            return []
        query = select(Device).where(Device.workspace_id == ws.id)
        devices = db.exec(query).all()
        result = []
        for d in devices:
            if state and d.state != state:
                continue
            if family and d.family != family:
                continue
            result.append({
                "id": str(d.id),
                "family": d.family,
                "state": d.state,
                "cost_estimate": d.cost_estimate,
            })
        return result


@mcp.tool()
def get_device(device_id: str) -> dict:
    """Get detailed status for a specific device."""
    from app.core.db import engine
    from sqlmodel import Session
    from app.models import Device
    import uuid

    with Session(engine) as db:
        try:
            did = uuid.UUID(device_id)
        except ValueError:
            return {"error": "Invalid device_id"}
        device = db.get(Device, did)
        if not device:
            return {"error": "Device not found"}
        return {
            "id": str(device.id),
            "family": device.family,
            "state": device.state,
            "phase": device.phase,
            "cost_estimate": device.cost_estimate,
            "created_at": device.created_at.isoformat(),
            "updated_at": device.updated_at.isoformat(),
        }


@mcp.tool()
def list_templates(family: str | None = None) -> list[dict]:
    """List available device templates."""
    from app.core.db import engine
    from sqlmodel import Session
    from app.services.templates import ensure_seed_templates, list_templates as _list

    with Session(engine) as db:
        ensure_seed_templates(db)
        templates = _list(db)
        return [
            {
                "id": str(t.id),
                "family": t.family,
                "name": t.name,
                "description": t.description,
            }
            for t in templates
            if not family or t.family == family
        ]


@mcp.tool()
def get_evidence(evidence_id: str) -> dict:
    """Retrieve an evidence record by ID."""
    from app.core.db import engine
    from sqlmodel import Session
    from app.services.evidence import get_evidence as _get
    import uuid

    with Session(engine) as db:
        try:
            eid = uuid.UUID(evidence_id)
        except ValueError:
            return {"error": "Invalid evidence_id"}
        ev = _get(db, eid)
        if not ev:
            return {"error": "Evidence not found"}
        return {
            "id": str(ev.id),
            "device_id": str(ev.device_id),
            "mcp_tool": ev.mcp_tool,
            "policy_decision": ev.policy_decision,
            "before_screen_version": ev.before_screen_version,
            "after_screen_version": ev.after_screen_version,
            "created_at": ev.created_at.isoformat(),
        }


@mcp.tool()
def cost_status(device_id: str | None = None) -> dict:
    """Return cost estimates for devices."""
    from app.core.db import engine
    from sqlmodel import Session, select
    from app.models import Device, Workspace
    import uuid

    with Session(engine) as db:
        ws = db.exec(select(Workspace).limit(1)).first()
        if not ws:
            return {"total_estimate": 0.0, "devices": []}
        query = select(Device).where(Device.workspace_id == ws.id)
        if device_id:
            try:
                query = query.where(Device.id == uuid.UUID(device_id))
            except ValueError:
                return {"error": "Invalid device_id"}
        devices = db.exec(query).all()
        device_costs = [
            {"id": str(d.id), "family": d.family, "state": d.state, "cost_estimate": d.cost_estimate}
            for d in devices if d.cost_estimate
        ]
        return {
            "total_estimate": sum(d["cost_estimate"] for d in device_costs if d["cost_estimate"]),
            "devices": device_costs,
        }


# ---------------------------------------------------------------------------
# Observation tools
# ---------------------------------------------------------------------------

@mcp.tool()
def observe(device_id: str, tier: str = "ax", delta_from_version: int | None = None) -> dict:
    """Observe the current state of a device. Tiers: ax (default) | ocr | screenshot."""
    import asyncio
    import uuid
    from app.core.db import engine
    from sqlmodel import Session
    from app.services.observation import observe as _observe

    with Session(engine) as db:
        try:
            did = uuid.UUID(device_id)
        except ValueError:
            return {"error": "Invalid device_id"}
        env = asyncio.get_event_loop().run_until_complete(_observe(db, did, tier, delta_from_version))
        return env.model_dump()


# ---------------------------------------------------------------------------
# Interaction tools
# ---------------------------------------------------------------------------

@mcp.tool()
def click(device_id: str, target: str, expected_screen_version: int | None = None) -> dict:
    """Click a UI element identified by accessible name, role, or selector."""
    return _run_action(device_id, "click", {"target": target}, expected_screen_version)


@mcp.tool()
def type_text(device_id: str, target: str, text: str, expected_screen_version: int | None = None) -> dict:
    """Type text into a field identified by accessible name or selector."""
    return _run_action(device_id, "type_text", {"target": target, "text": text}, expected_screen_version)


@mcp.tool()
def fill_form(device_id: str, fields: dict, expected_screen_version: int | None = None) -> dict:
    """Fill multiple form fields at once. fields: {selector: value}."""
    return _run_action(device_id, "fill_form", {"fields": fields}, expected_screen_version)


@mcp.tool()
def select_option(device_id: str, target: str, value: str) -> dict:
    """Select an option from a dropdown by value."""
    return _run_action(device_id, "select_option", {"target": target, "value": value})


@mcp.tool()
def scroll(device_id: str, direction: str = "down", amount: int = 300) -> dict:
    """Scroll the page. direction: up|down, amount in pixels."""
    return _run_action(device_id, "scroll", {"direction": direction, "amount": amount})


@mcp.tool()
def wait_for(device_id: str, condition: str, timeout_ms: int = 5000) -> dict:
    """Wait for a condition (CSS selector or text) to appear."""
    return _run_action(device_id, "wait_for", {"condition": condition, "timeout_ms": timeout_ms})


@mcp.tool()
def read_content(device_id: str, selector: str | None = None, format: str = "text") -> dict:
    """Read text content from the device. format: text|markdown|json."""
    return _run_action(device_id, "read_content", {"selector": selector, "format": format})


@mcp.tool()
def run_steps(
    device_id: str,
    steps: list[dict],
    abort_on_failure: bool = True,
    screen_version_guard: int | None = None,
) -> dict:
    """Execute multiple interaction steps in sequence. Reduces round trips by 5-10x."""
    import asyncio
    import uuid
    from app.core.db import engine
    from sqlmodel import Session
    from app.models import Step
    from app.services.interaction import run_steps as _run

    with Session(engine) as db:
        try:
            did = uuid.UUID(device_id)
        except ValueError:
            return {"error": "Invalid device_id"}
        step_objs = [Step(**s) for s in steps]
        result = asyncio.get_event_loop().run_until_complete(
            _run(db, did, step_objs, abort_on_failure, screen_version_guard)
        )
        return result.model_dump()


# ---------------------------------------------------------------------------
# Capability handshake
# ---------------------------------------------------------------------------

@mcp.tool()
def get_device_manifest(device_id: str, role: str = "observe") -> dict:
    """Return the filtered tool manifest for a device + client role combination."""
    import uuid
    from app.core.db import engine
    from sqlmodel import Session
    from app.models import Device
    from app.mcp.permissions import parse_role

    with Session(engine) as db:
        try:
            did = uuid.UUID(device_id)
        except ValueError:
            return {"error": "Invalid device_id"}
        device = db.get(Device, did)
        if not device:
            return {"error": "Device not found"}
        return build_manifest(device.family, device.state, parse_role(role))


def _run_action(
    device_id: str,
    action: str,
    params: dict,
    expected_screen_version: int | None = None,
) -> dict:
    import asyncio
    import uuid
    from app.core.db import engine
    from sqlmodel import Session
    from app.services.interaction import execute_action

    with Session(engine) as db:
        try:
            did = uuid.UUID(device_id)
        except ValueError:
            return {"success": False, "error": "Invalid device_id", "evidence_id": "", "before_screen_version": 0, "after_screen_version": 0}
        result = asyncio.get_event_loop().run_until_complete(
            execute_action(db, did, action, params, expected_screen_version=expected_screen_version)
        )
        return result.model_dump()


# Register tool extensions — importing the module is enough to register @mcp.tool() decorators
import app.mcp.tools.identity  # noqa: E402, F401
