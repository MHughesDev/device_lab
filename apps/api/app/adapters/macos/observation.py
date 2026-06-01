# observation.py — macOS AX observation via macos_ax.py + SSMChannel
from __future__ import annotations
import json
from datetime import UTC, datetime

from app.adapters.spi import CapabilityUnsupportedError
from app.models import ObservationEnvelope
from app.transport.channel import ChannelFactory

_SUPPORTED_TIERS = {"ax_tree", "screenshot"}


async def observe_macos(device: object, tier: str) -> ObservationEnvelope:
    if tier not in _SUPPORTED_TIERS:
        raise CapabilityUnsupportedError(tier, "macos")

    if tier == "ax_tree":
        structured = await _run_ax(device)
        return ObservationEnvelope(
            device_id=str(getattr(device, "id", "")),
            screen_version=getattr(device, "screen_version", 0),
            tier="ax",
            structured=structured,
            observed_at=datetime.now(UTC),
        )
    else:
        screenshot_ref = await _run_screenshot(device)
        return ObservationEnvelope(
            device_id=str(getattr(device, "id", "")),
            screen_version=getattr(device, "screen_version", 0),
            tier="screenshot",
            screenshot_ref=screenshot_ref,
            observed_at=datetime.now(UTC),
        )


async def _run_ax(device: object) -> dict:
    channel = ChannelFactory.get(device)
    result = await channel.exec("python3 /opt/devicelab/macos_ax.py")
    try:
        return json.loads(result.stdout or "{}")
    except Exception:
        return {"nodes": [], "error": result.stdout}


async def _run_screenshot(device: object) -> str:
    channel = ChannelFactory.get(device)
    result = await channel.exec("screencapture -t png /tmp/dl_screenshot.png && base64 /tmp/dl_screenshot.png")
    return result.stdout.strip()
