# interaction.py — Linux interaction via SSM + xdotool (coordinate-based)
from __future__ import annotations
import json
import time

import boto3

from app.adapters.spi import CapabilityUnsupportedError

SUPPORTED_ACTIONS = {
    "click", "double_click", "right_click", "mouse_move",
    "drag", "scroll", "cursor_position", "type", "key",
}


async def act_linux(device: object, action: str, params: dict) -> dict:
    if action not in SUPPORTED_ACTIONS:
        raise CapabilityUnsupportedError(action, "linux")

    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    instance_id = ids.get("instance_id", "")
    region = ids.get("region", "us-east-1")

    cmd = _build_xdotool_command(action, params)
    ssm = boto3.client("ssm", region_name=region)
    resp = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": [f"DISPLAY=:0 {cmd}"]},
    )

    if action == "cursor_position":
        command_id = resp["Command"]["CommandId"]
        for _ in range(10):
            time.sleep(1)
            inv = ssm.get_command_invocation(CommandId=command_id, InstanceId=instance_id)
            if inv["Status"] in ("Success", "Failed"):
                raw = inv.get("StandardOutputContent", "")
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
        # Normalize: ctrl+c → ctrl+c (xdotool accepts this format)
        return f"xdotool key {key}"
    return "true"


async def screenshot_b64(device: object) -> str:
    """Capture screenshot, return base64-encoded PNG string."""
    import time
    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    instance_id = ids.get("instance_id", "")
    region = ids.get("region", "us-east-1")

    ssm = boto3.client("ssm", region_name=region)
    resp = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": [
            "DISPLAY=:0 scrot /tmp/devicelab-shot.png 2>/dev/null || "
            "DISPLAY=:0 import -window root -silent /tmp/devicelab-shot.png",
            "base64 -w 0 /tmp/devicelab-shot.png",
        ]},
    )
    command_id = resp["Command"]["CommandId"]
    for _ in range(15):
        time.sleep(1)
        inv = ssm.get_command_invocation(CommandId=command_id, InstanceId=instance_id)
        if inv["Status"] in ("Success", "Failed"):
            return inv.get("StandardOutputContent", "").strip()
    return ""
