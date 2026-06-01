# interaction.py — Browser interaction via Playwright (coordinate-based)
from __future__ import annotations
import base64

from app.adapters.spi import CapabilityUnsupportedError

SUPPORTED_ACTIONS = {
    "click", "double_click", "right_click", "mouse_move",
    "drag", "scroll", "cursor_position", "type", "key",
}


async def act_browser(device: object, action: str, params: dict) -> dict:
    if action not in SUPPORTED_ACTIONS:
        raise CapabilityUnsupportedError(action, "browser")

    from app.adapters.browser.adapter import _sessions
    device_id = str(device.id)  # type: ignore[attr-defined]
    session = _sessions.get(device_id)
    if not session or session._page is None:  # type: ignore[attr-defined]
        return {"success": False, "error": "No active browser session"}

    page = session._page  # type: ignore[attr-defined]
    x, y = params.get("x", 0), params.get("y", 0)

    if action == "click":
        button = params.get("button", "left")
        await page.mouse.click(x, y, button=button)
    elif action == "double_click":
        await page.mouse.dblclick(x, y)
    elif action == "right_click":
        await page.mouse.click(x, y, button="right")
    elif action == "mouse_move":
        await page.mouse.move(x, y)
    elif action == "drag":
        ex, ey = params.get("end_x", 0), params.get("end_y", 0)
        await page.mouse.move(x, y)
        await page.mouse.down()
        await page.mouse.move(ex, ey)
        await page.mouse.up()
    elif action == "scroll":
        direction = params.get("direction", "down")
        amount = int(params.get("amount", 3)) * 100
        delta_x = -amount if direction == "left" else (amount if direction == "right" else 0)
        delta_y = -amount if direction == "up" else (amount if direction == "down" else 0)
        await page.mouse.wheel(delta_x, delta_y)
    elif action == "cursor_position":
        pos = await page.evaluate("() => ({x: window._dlMouseX || 0, y: window._dlMouseY || 0})")
        return {"success": True, "x": pos.get("x", 0), "y": pos.get("y", 0)}
    elif action == "type":
        await page.keyboard.type(params.get("text", ""))
    elif action == "key":
        await page.keyboard.press(_normalize_key(params.get("key", "Enter")))

    return {"success": True, "action": action}


def _normalize_key(key: str) -> str:
    """Map xdotool/Anthropic computer-use key names to Playwright key names."""
    mapping = {
        "Return": "Enter", "BackSpace": "Backspace",
        "ctrl+c": "Control+c", "ctrl+v": "Control+v",
        "ctrl+z": "Control+z", "ctrl+a": "Control+a",
        "cmd+c": "Meta+c", "cmd+v": "Meta+v",
        "cmd+tab": "Meta+Tab", "ctrl+tab": "Control+Tab",
        "super": "Meta",
    }
    return mapping.get(key, key)


async def screenshot_b64(device: object) -> str:
    """Take a Playwright screenshot, return base64-encoded PNG."""
    from app.adapters.browser.adapter import _sessions
    device_id = str(device.id)  # type: ignore[attr-defined]
    session = _sessions.get(device_id)
    if not session or session._page is None:  # type: ignore[attr-defined]
        return ""
    png_bytes = await session._page.screenshot(full_page=False)  # type: ignore[attr-defined]
    return base64.b64encode(png_bytes).decode()
