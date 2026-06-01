# observation.py — Windows AX observation via windows_ax.py + SSMChannel
from __future__ import annotations
import json
from datetime import UTC, datetime

from app.adapters.spi import CapabilityUnsupportedError
from app.models import ObservationEnvelope
from app.transport.channel import ChannelFactory

_SUPPORTED_TIERS = {"ax_tree", "screenshot"}


async def observe_windows(device: object, tier: str) -> ObservationEnvelope:
    if tier not in _SUPPORTED_TIERS:
        raise CapabilityUnsupportedError(tier, "windows")

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
    result = await channel.exec("python C:\\devicelab\\windows_ax.py")
    try:
        return json.loads(result.stdout or "{}")
    except Exception:
        return {"nodes": [], "error": result.stdout}


async def _run_screenshot(device: object) -> str:
    cmd = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "Add-Type -AssemblyName System.Drawing; "
        "$img = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds; "
        "$bmp = New-Object System.Drawing.Bitmap $img.Width,$img.Height; "
        "$g = [System.Drawing.Graphics]::FromImage($bmp); "
        "$g.CopyFromScreen(0,0,0,0,$bmp.Size); "
        "$ms = New-Object System.IO.MemoryStream; "
        "$bmp.Save($ms,'Png'); "
        "[Convert]::ToBase64String($ms.ToArray())"
    )
    channel = ChannelFactory.get(device)
    result = await channel.exec(cmd)
    return result.stdout.strip()
