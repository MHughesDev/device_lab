"""Shared adapter dispatch helpers for MCP tool modules."""
from __future__ import annotations
import asyncio
import uuid


def run_action(device_id: str, action: str, params: dict) -> dict:
    """Resolve device → adapter → act(). Used by all MCP interaction tools."""
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
            return {"success": False, "error": f"No adapter for family '{device.family}'"}
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


def get_device_and_family(device_id: str):
    """Return (device, family) or raise ValueError."""
    from app.core.db import engine
    from sqlmodel import Session
    from app.models import Device
    try:
        did = uuid.UUID(device_id)
    except ValueError:
        raise ValueError("Invalid device_id")
    with Session(engine) as db:
        device = db.get(Device, did)
        if not device:
            raise ValueError("Device not found")
        return device, device.family


async def screenshot_b64_for_device(device_id: str) -> str:
    """Take a screenshot of a device and return base64 PNG string."""
    device, family = get_device_and_family(device_id)
    if family == "linux":
        from app.adapters.linux.interaction import screenshot_b64
    elif family == "macos":
        from app.adapters.macos.interaction import screenshot_b64
    elif family == "windows":
        from app.adapters.windows.interaction import screenshot_b64
    elif family == "android":
        from app.adapters.android.interaction import screenshot_b64
    elif family == "ios_sim":
        from app.adapters.ios_sim.interaction import screenshot_b64
    else:
        return ""
    return await screenshot_b64(device)
