"""
DeviceLab MCP gateway — FastMCP server mounted at /mcp.
Computer-use tools follow the Anthropic computer-use / OpenAI CUA standard:
coordinate-based pointer, keyboard, and inline screenshot returns.
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
        devices = db.exec(select(Device).where(Device.workspace_id == ws.id)).all()
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
        return [
            {
                "id": str(t.id),
                "family": t.family,
                "name": t.name,
                "description": t.description,
            }
            for t in _list(db)
            if not family or t.family == family
        ]


@mcp.tool()
def get_evidence(evidence_id: str) -> dict:
    """Retrieve an evidence record by ID."""
    from app.core.db import engine
    from sqlmodel import Session
    from app.services.evidence import get_evidence as _get

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


@mcp.tool()
def get_device_manifest(device_id: str, role: str = "observe") -> dict:
    """Return the filtered tool manifest for a device + client role combination."""
    from app.core.db import engine
    from sqlmodel import Session
    from app.models import Device

    with Session(engine) as db:
        try:
            did = uuid.UUID(device_id)
        except ValueError:
            return {"error": "Invalid device_id"}
        device = db.get(Device, did)
        if not device:
            return {"error": "Device not found"}
        return build_manifest(device.family, device.state, parse_role(role))


# ---------------------------------------------------------------------------
# Observation — screenshot (inline) + accessibility tree
# ---------------------------------------------------------------------------

@mcp.tool()
def screenshot(device_id: str) -> dict:
    """
    Take a screenshot of the device screen.

    Returns base64-encoded PNG in the 'image' field and mime_type 'image/png'.
    The image is returned inline so the model can act on it immediately.
    """
    import asyncio
    from app.core.db import engine
    from sqlmodel import Session
    from app.models import Device

    with Session(engine) as db:
        try:
            did = uuid.UUID(device_id)
        except ValueError:
            return {"error": "Invalid device_id"}
        device = db.get(Device, did)
        if not device:
            return {"error": "Device not found"}
        b64 = asyncio.get_event_loop().run_until_complete(_screenshot_b64(device))
        if not b64:
            return {"error": "Screenshot capture failed or returned empty"}
        return {
            "image": b64,
            "mime_type": "image/png",
            "device_id": device_id,
            "family": device.family,
        }


@mcp.tool()
def get_accessibility_tree(device_id: str) -> dict:
    """
    Return the accessibility tree (AX tree) for the device's current screen.

    Use this to identify element coordinates before calling click/type/key.
    Each node contains role, name, bounds {x, y, width, height}, and children.
    """
    import asyncio
    from app.core.db import engine
    from sqlmodel import Session
    from app.models import Device
    from app.services.observation import _observe_ax  # type: ignore[attr-defined]

    with Session(engine) as db:
        try:
            did = uuid.UUID(device_id)
        except ValueError:
            return {"error": "Invalid device_id"}
        device = db.get(Device, did)
        if not device:
            return {"error": "Device not found"}
        tree = asyncio.get_event_loop().run_until_complete(_observe_ax(device))
        return tree


# ---------------------------------------------------------------------------
# Computer-use interaction tools (coordinate-based)
# ---------------------------------------------------------------------------

@mcp.tool()
def click(device_id: str, x: int, y: int, button: str = "left") -> dict:
    """
    Click at screen coordinates. button: left (default) | right | middle.

    Use get_accessibility_tree or screenshot first to identify target coordinates.
    """
    return _run_action(device_id, "click", {"x": x, "y": y, "button": button})


@mcp.tool()
def double_click(device_id: str, x: int, y: int) -> dict:
    """Double-click at screen coordinates."""
    return _run_action(device_id, "double_click", {"x": x, "y": y})


@mcp.tool()
def right_click(device_id: str, x: int, y: int) -> dict:
    """Right-click at screen coordinates (opens context menus)."""
    return _run_action(device_id, "right_click", {"x": x, "y": y})


@mcp.tool()
def mouse_move(device_id: str, x: int, y: int) -> dict:
    """Move the mouse cursor to coordinates without clicking (triggers hover states)."""
    return _run_action(device_id, "mouse_move", {"x": x, "y": y})


@mcp.tool()
def drag(device_id: str, start_x: int, start_y: int, end_x: int, end_y: int) -> dict:
    """Click-and-drag from (start_x, start_y) to (end_x, end_y)."""
    return _run_action(device_id, "drag", {
        "x": start_x, "y": start_y, "end_x": end_x, "end_y": end_y,
    })


@mcp.tool()
def scroll(device_id: str, x: int, y: int, direction: str = "down", amount: int = 3) -> dict:
    """
    Scroll at coordinates. direction: up | down | left | right.
    amount is in scroll ticks (default 3).
    """
    return _run_action(device_id, "scroll", {
        "x": x, "y": y, "direction": direction, "amount": amount,
    })


@mcp.tool()
def cursor_position(device_id: str) -> dict:
    """Return the current cursor/pointer position as {x, y}."""
    return _run_action(device_id, "cursor_position", {})


@mcp.tool()
def type(device_id: str, text: str) -> dict:
    """Type text at the current focused element."""
    return _run_action(device_id, "type", {"text": text})


@mcp.tool()
def key(device_id: str, key: str) -> dict:
    """
    Press a key or key combination.
    Examples: 'Return', 'Escape', 'Tab', 'ctrl+c', 'ctrl+v', 'cmd+tab',
              'BackSpace', 'Delete', 'ctrl+z', 'F5'.
    """
    return _run_action(device_id, "key", {"key": key})


# ---------------------------------------------------------------------------
# Shared dispatch helper
# ---------------------------------------------------------------------------

def _run_action(device_id: str, action: str, params: dict) -> dict:
    import asyncio
    from app.core.db import engine
    from sqlmodel import Session
    from app.models import Device
    from app.adapters.registry import AdapterRegistry
    from app.adapters.spi import CapabilityUnsupportedError

    with Session(engine) as db:
        try:
            did = uuid.UUID(device_id)
        except ValueError:
            return {"success": False, "error": "Invalid device_id"}
        device = db.get(Device, did)
        if not device:
            return {"success": False, "error": "Device not found"}
        try:
            adapter_cls = AdapterRegistry.get(device.family)
        except KeyError:
            return {"success": False, "error": f"No adapter registered for family '{device.family}'"}
        try:
            result = asyncio.get_event_loop().run_until_complete(
                adapter_cls().act(device, action, params)
            )
        except CapabilityUnsupportedError as exc:
            return {"success": False, "error": str(exc)}
        except Exception as exc:
            return {"success": False, "error": str(exc)}
        if isinstance(result, dict):
            return result
        return {"success": True, "action": action}


async def _screenshot_b64(device: object) -> str:
    family = device.family  # type: ignore[attr-defined]
    if family == "linux":
        from app.adapters.linux.interaction import screenshot_b64
    elif family == "macos":
        from app.adapters.macos.interaction import screenshot_b64  # type: ignore[no-redef]
    elif family == "windows":
        from app.adapters.windows.interaction import screenshot_b64  # type: ignore[no-redef]
    elif family == "android":
        from app.adapters.android.interaction import screenshot_b64  # type: ignore[no-redef]
    elif family == "ios_sim":
        from app.adapters.ios_sim.interaction import screenshot_b64  # type: ignore[no-redef]
    elif family == "browser":
        from app.adapters.browser.interaction import screenshot_b64  # type: ignore[no-redef]
    else:
        return ""
    return await screenshot_b64(device)


# Register tool extensions — importing the module is enough to register @mcp.tool() decorators
import app.mcp.tools.identity  # noqa: E402, F401
import app.mcp.tools.screen_recording  # noqa: E402, F401
