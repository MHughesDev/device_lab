# interaction.py — Linux interaction via SSMChannel + xdotool (coordinate-based)
from __future__ import annotations
import json

from app.adapters.spi import CapabilityUnsupportedError
from app.adapters.linux.system_ops import SYSTEM_ACTIONS, handle_system_action
from app.transport.channel import ChannelFactory

SUPPORTED_ACTIONS = {
    "click", "double_click", "right_click", "mouse_move",
    "drag", "scroll", "cursor_position", "type", "key",
} | SYSTEM_ACTIONS


async def act_linux(device: object, action: str, params: dict) -> dict:
    if action in SYSTEM_ACTIONS:
        return await handle_system_action(device, action, params)
    if action not in SUPPORTED_ACTIONS:
        raise CapabilityUnsupportedError(action, "linux")

    channel = ChannelFactory.get(device)
    cmd = _build_xdotool_command(action, params)
    result = await channel.exec(f"DISPLAY=:0 {cmd}")

    if action == "cursor_position":
        raw = result.stdout.strip()
        # xdotool getmouselocation outputs: x:123 y:456 screen:0 window:789
        parts = dict(p.split(":") for p in raw.split() if ":" in p)
        return {
            "success": True,
            "x": int(parts.get("x", 0)),
            "y": int(parts.get("y", 0)),
        }

    return {"success": True, "action": action}


def _build_xdotool_command(action: str, params: dict) -> str:
    x, y = params.get("x", 0), params.get("y", 0)
    button_map = {"left": "1", "middle": "2", "right": "3"}

    if action == "click":
        btn = button_map.get(params.get("button", "left"), "1")
        return f"xdotool mousemove {x} {y} click {btn}"
    elif action == "double_click":
        return f"xdotool mousemove {x} {y} click --repeat 2 --delay 100 1"
    elif action == "right_click":
        return f"xdotool mousemove {x} {y} click 3"
    elif action == "mouse_move":
        return f"xdotool mousemove {x} {y}"
    elif action == "drag":
        ex, ey = params.get("end_x", 0), params.get("end_y", 0)
        return f"xdotool mousemove {x} {y} mousedown 1 mousemove {ex} {ey} mouseup 1"
    elif action == "scroll":
        direction = params.get("direction", "down")
        amount = int(params.get("amount", 3))
        btn = "4" if direction in ("up", "left") else "5"
        clicks = " ".join([f"click {btn}"] * amount)
        return f"xdotool mousemove {x} {y} {clicks}"
    elif action == "cursor_position":
        return "xdotool getmouselocation"
    elif action == "type":
        text = params.get("text", "").replace("'", r"\'")
        return f"xdotool type --clearmodifiers '{text}'"
    elif action == "key":
        key = params.get("key", "Return")
        return f"xdotool key {key}"
    return "true"


async def screenshot_b64(device: object) -> str:
    """Capture screenshot, return base64-encoded PNG string."""
    channel = ChannelFactory.get(device)
    result = await channel.exec([
        "DISPLAY=:0 scrot /tmp/devicelab-shot.png 2>/dev/null || "
        "DISPLAY=:0 import -window root -silent /tmp/devicelab-shot.png",
        "base64 -w 0 /tmp/devicelab-shot.png",
    ])
    return result.stdout.strip()
