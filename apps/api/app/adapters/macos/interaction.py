# interaction.py — macOS interaction via SSMChannel + cliclick (coordinate-based)
from __future__ import annotations

from app.adapters.spi import CapabilityUnsupportedError
from app.adapters.macos.system_ops import SYSTEM_ACTIONS, handle_system_action
from app.transport.channel import ChannelFactory

SUPPORTED_ACTIONS = {
    "click", "double_click", "right_click", "mouse_move",
    "drag", "scroll", "cursor_position", "type", "key",
} | SYSTEM_ACTIONS


async def act_macos(device: object, action: str, params: dict) -> dict:
    if action in SYSTEM_ACTIONS:
        return await handle_system_action(device, action, params)
    if action not in SUPPORTED_ACTIONS:
        raise CapabilityUnsupportedError(action, "macos")

    channel = ChannelFactory.get(device)
    cmd = _build_command(action, params)
    result = await channel.exec(cmd)

    if action == "cursor_position":
        # cliclick -p outputs: 123,456
        raw = result.stdout.strip()
        parts = raw.split(",")
        return {
            "success": True,
            "x": int(parts[0]) if parts else 0,
            "y": int(parts[1]) if len(parts) > 1 else 0,
        }

    return {"success": True, "action": action}


def _build_command(action: str, params: dict) -> str:
    x, y = params.get("x", 0), params.get("y", 0)

    if action == "click":
        button = params.get("button", "left")
        flag = "c" if button == "left" else ("rc" if button == "right" else "mc")
        return f"cliclick {flag}:{x},{y}"
    elif action == "double_click":
        return f"cliclick dc:{x},{y}"
    elif action == "right_click":
        return f"cliclick rc:{x},{y}"
    elif action == "mouse_move":
        return f"cliclick m:{x},{y}"
    elif action == "drag":
        ex, ey = params.get("end_x", 0), params.get("end_y", 0)
        return f"cliclick dd:{x},{y} du:{ex},{ey}"
    elif action == "scroll":
        direction = params.get("direction", "down")
        return f"cliclick kp:scroll-{direction} -- {x},{y}"
    elif action == "cursor_position":
        return "cliclick -p"
    elif action == "type":
        text = params.get("text", "").replace("'", r"\'")
        return f"cliclick t:'{text}'"
    elif action == "key":
        key = params.get("key", "Return")
        return f"osascript -e 'tell application \"System Events\" to keystroke \"{_map_key(key)}\"'"
    return "true"


def _map_key(key: str) -> str:
    mapping = {
        "Return": "\r", "Escape": "\x1b", "Tab": "\t",
        "BackSpace": "\x08", "Delete": "\x7f",
        "ctrl+c": "\x03", "ctrl+v": "\x16", "ctrl+z": "\x1a",
        "cmd+c": "\x03", "cmd+v": "\x16",
    }
    return mapping.get(key, key)


async def screenshot_b64(device: object) -> str:
    """Capture screenshot via screencapture, return base64-encoded PNG."""
    channel = ChannelFactory.get(device)
    result = await channel.exec([
        "screencapture -x /tmp/devicelab-shot.png",
        "base64 -i /tmp/devicelab-shot.png",
    ])
    return result.stdout.strip()
