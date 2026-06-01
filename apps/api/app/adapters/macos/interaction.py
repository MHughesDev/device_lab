# interaction.py — macOS interaction via SSM + cliclick (coordinate-based)
from __future__ import annotations
import json
import time

import boto3

from app.adapters.spi import CapabilityUnsupportedError
from app.adapters.macos.system_ops import SYSTEM_ACTIONS, handle_system_action

SUPPORTED_ACTIONS = {
    "click", "double_click", "right_click", "mouse_move",
    "drag", "scroll", "cursor_position", "type", "key",
} | SYSTEM_ACTIONS


async def act_macos(device: object, action: str, params: dict) -> dict:
    if action in SYSTEM_ACTIONS:
        return await handle_system_action(device, action, params)
    if action not in SUPPORTED_ACTIONS:
        raise CapabilityUnsupportedError(action, "macos")

    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    instance_id = ids.get("instance_id", "")
    region = ids.get("region", "us-east-1")

    cmd = _build_command(action, params)
    ssm = boto3.client("ssm", region_name=region)
    resp = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": [cmd]},
    )

    if action == "cursor_position":
        command_id = resp["Command"]["CommandId"]
        for _ in range(10):
            time.sleep(1)
            inv = ssm.get_command_invocation(CommandId=command_id, InstanceId=instance_id)
            if inv["Status"] in ("Success", "Failed"):
                # cliclick -p outputs: 123,456
                raw = inv.get("StandardOutputContent", "").strip()
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
        amount = int(params.get("amount", 3))
        # cliclick scroll: positive = down, negative = up
        delta = -amount if direction == "up" else amount
        return f"cliclick kp:scroll-{direction} -- {x},{y}"
    elif action == "cursor_position":
        return "cliclick -p"
    elif action == "type":
        text = params.get("text", "").replace("'", r"\'")
        return f"cliclick t:'{text}'"
    elif action == "key":
        # Map standard key names to AppleScript key codes via osascript
        key = params.get("key", "Return")
        return f"osascript -e 'tell application \"System Events\" to keystroke \"{_map_key(key)}\"'"
    return "true"


def _map_key(key: str) -> str:
    """Map common key names to osascript-compatible strings."""
    mapping = {
        "Return": "\r", "Escape": "\x1b", "Tab": "\t",
        "BackSpace": "\x08", "Delete": "\x7f",
        "ctrl+c": "\x03", "ctrl+v": "\x16", "ctrl+z": "\x1a",
        "cmd+c": "\x03", "cmd+v": "\x16",
    }
    return mapping.get(key, key)


async def screenshot_b64(device: object) -> str:
    """Capture screenshot via screencapture, return base64-encoded PNG."""
    import time
    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    instance_id = ids.get("instance_id", "")
    region = ids.get("region", "us-east-1")

    ssm = boto3.client("ssm", region_name=region)
    resp = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": [
            "screencapture -x /tmp/devicelab-shot.png",
            "base64 -i /tmp/devicelab-shot.png",
        ]},
    )
    command_id = resp["Command"]["CommandId"]
    for _ in range(15):
        time.sleep(1)
        inv = ssm.get_command_invocation(CommandId=command_id, InstanceId=instance_id)
        if inv["Status"] in ("Success", "Failed"):
            return inv.get("StandardOutputContent", "").strip()
    return ""
