# interaction.py — iOS Simulator interaction via SSM + AppleScript coordinate injection
from __future__ import annotations
import json
import time

import boto3

from app.adapters.spi import CapabilityUnsupportedError
from app.adapters.ios_sim.system_ops import SYSTEM_ACTIONS, MOBILE_ACTIONS, handle_system_action, handle_mobile_action

# right_click / mouse_move / cursor_position are desktop-only concepts; not exposed on sim
SUPPORTED_ACTIONS = {"click", "double_click", "drag", "scroll", "type", "key"} | SYSTEM_ACTIONS | MOBILE_ACTIONS


async def act_ios_sim(device: object, action: str, params: dict) -> dict:
    if action not in SUPPORTED_ACTIONS:
        raise CapabilityUnsupportedError(action, "ios_sim")
    if action in SYSTEM_ACTIONS:
        return await handle_system_action(device, action, params)
    if action in MOBILE_ACTIONS:
        return await handle_mobile_action(device, action, params)

    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    instance_id = ids.get("instance_id", "")
    sim_udid = ids.get("sim_udid", "")
    region = ids.get("region", "us-east-1")

    cmd = _build_command(action, sim_udid, params)
    ssm = boto3.client("ssm", region_name=region)
    ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": [cmd]},
    )
    return {"success": True, "action": action}


def _build_command(action: str, sim_udid: str, params: dict) -> str:
    x, y = params.get("x", 0), params.get("y", 0)

    if action == "click":
        # AppleScript coordinate tap in the Simulator window
        return (
            f"osascript -e 'tell application \"Simulator\" to activate' "
            f"-e 'tell application \"System Events\" to tell process \"Simulator\" "
            f"to click at {{{x}, {y}}}'"
        )
    elif action == "double_click":
        return (
            f"osascript -e 'tell application \"Simulator\" to activate' "
            f"-e 'tell application \"System Events\" to tell process \"Simulator\" "
            f"to double click at {{{x}, {y}}}'"
        )
    elif action == "drag":
        ex, ey = params.get("end_x", 0), params.get("end_y", 0)
        return (
            f"osascript -e 'tell application \"Simulator\" to activate' "
            f"-e 'tell application \"System Events\" to tell process \"Simulator\" "
            f"to drag from {{{x}, {y}}} to {{{ex}, {ey}}}'"
        )
    elif action == "scroll":
        direction = params.get("direction", "down")
        amount = int(params.get("amount", 3))
        key_map = {"down": "Page Down", "up": "Page Up", "left": "Left", "right": "Right"}
        key_name = key_map.get(direction, "Page Down")
        return (
            f"for i in $(seq 1 {amount}); do "
            f"osascript -e 'tell application \"System Events\" to key code "
            f"\"{key_name}\"'; done"
        )
    elif action == "type":
        text = params.get("text", "").replace("'", r"\'")
        return f"xcrun simctl io {sim_udid} sendkey type '{text}'"
    elif action == "key":
        key_val = params.get("key", "Return")
        return f"xcrun simctl io {sim_udid} sendkey {_map_key(key_val)}"
    return "true"


def _map_key(key: str) -> str:
    mapping = {
        "Return": "return", "Escape": "escape", "Tab": "tab",
        "BackSpace": "delete", "Delete": "forwarddelete",
        "Home": "home", "End": "end",
        "Up": "up", "Down": "down", "Left": "left", "Right": "right",
    }
    return mapping.get(key, key.lower())


async def screenshot_b64(device: object) -> str:
    """Capture iOS Simulator screenshot via simctl, return base64-encoded PNG."""
    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    instance_id = ids.get("instance_id", "")
    sim_udid = ids.get("sim_udid", "")
    region = ids.get("region", "us-east-1")

    ssm = boto3.client("ssm", region_name=region)
    resp = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": [
            f"xcrun simctl io {sim_udid} screenshot /tmp/devicelab-sim-shot.png",
            "base64 -i /tmp/devicelab-sim-shot.png",
        ]},
    )
    command_id = resp["Command"]["CommandId"]
    for _ in range(15):
        time.sleep(1)
        inv = ssm.get_command_invocation(CommandId=command_id, InstanceId=instance_id)
        if inv["Status"] in ("Success", "Failed"):
            return inv.get("StandardOutputContent", "").strip()
    return ""
