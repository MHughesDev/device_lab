"""
Mobile-specific MCP tools — touch gestures and hardware buttons.
Only applicable to family='android' and family='ios_sim' devices.
"""
from __future__ import annotations

from app.mcp.gateway import mcp
from app.mcp.dispatch import run_action


@mcp.tool()
def long_press(device_id: str, x: int, y: int, duration_ms: int = 800) -> dict:
    """
    Long-press at coordinates for duration_ms milliseconds.
    Used to trigger context menus, text selection handles, and drag-to-rearrange.
    """
    return run_action(device_id, "long_press", {"x": x, "y": y, "duration_ms": duration_ms})


@mcp.tool()
def pinch(device_id: str, x: int, y: int, scale: float) -> dict:
    """
    Pinch gesture centred on (x, y).
    scale < 1.0 = pinch in (zoom out), scale > 1.0 = spread (zoom in).
    Example: scale=0.5 zooms out by 50%, scale=2.0 doubles the zoom.
    """
    return run_action(device_id, "pinch", {"x": x, "y": y, "scale": scale})


@mcp.tool()
def press_button(device_id: str, button: str) -> dict:
    """
    Press a hardware or system button.
    Android buttons: home, back, menu, volume_up, volume_down, power, recent_apps
    iOS Simulator buttons: home, lock, side_button, apple_pay, rotate_left, rotate_right
    """
    return run_action(device_id, "press_button", {"button": button})
