# system_ops.py — iOS Simulator system operations via SSM + xcrun simctl
from __future__ import annotations
import json
import time

import boto3

from app.adapters.spi import CapabilityUnsupportedError

SYSTEM_ACTIONS = {
    "run_shell", "launch_app", "read_file", "list_directory",
    "list_processes", "get_screen_size",
    "key_down", "key_up",
    # clipboard, write_file, focus/list/resize_windows not supported
}

MOBILE_ACTIONS = {"long_press", "press_button"}
# pinch is not supported on iOS Sim via simctl without XCTest


async def handle_system_action(device: object, action: str, params: dict) -> dict:
    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    instance_id = ids.get("instance_id", "")
    sim_udid = ids.get("sim_udid", "")
    region = ids.get("region", "us-east-1")
    ssm = boto3.client("ssm", region_name=region)

    cmd = _build_cmd(action, params, sim_udid)
    if cmd is None:
        raise CapabilityUnsupportedError(action, "ios_sim")

    resp = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": [cmd]},
    )
    out = _poll(ssm, resp["Command"]["CommandId"], instance_id)

    if action == "run_shell":
        return {"success": True, "stdout": out.get("stdout", ""), "stderr": out.get("stderr", ""), "exit_code": out.get("exit_code", 0)}
    if action == "read_file":
        return {"success": True, "content": out.get("stdout", "")}
    if action == "list_directory":
        lines = [l for l in out.get("stdout", "").splitlines() if l.strip()]
        return {"success": True, "entries": lines}
    if action == "list_processes":
        lines = out.get("stdout", "").strip().splitlines()
        procs = [{"line": l} for l in lines if l.strip()]
        return {"success": True, "processes": procs}
    if action == "get_screen_size":
        raw = out.get("stdout", "").strip()
        if "x" in raw:
            w, h = raw.split("x")
            return {"success": True, "width": int(w.strip()), "height": int(h.strip())}
        return {"success": True, "raw": raw}
    return {"success": True, "action": action, "output": out.get("stdout", "")}


def _build_cmd(action: str, params: dict, sim_udid: str) -> str | None:
    if action == "run_shell":
        cmd = params.get("command", "")
        return f"xcrun simctl spawn {sim_udid} bash -c {json.dumps(cmd)} 2>&1"
    elif action == "launch_app":
        bundle_id = params.get("app", "")
        return f"xcrun simctl launch {sim_udid} {bundle_id} 2>&1"
    elif action == "read_file":
        # Access simulator's app data container — use the macOS host path
        path = params.get("path", "")
        return f"xcrun simctl spawn {sim_udid} cat {json.dumps(path)} 2>&1"
    elif action == "list_directory":
        path = params.get("path", "/")
        return f"xcrun simctl spawn {sim_udid} ls -la {json.dumps(path)} 2>&1"
    elif action == "list_processes":
        return f"xcrun simctl spawn {sim_udid} ps aux 2>&1 | head -30"
    elif action == "get_screen_size":
        # Get from device type info
        return f"xcrun simctl list devices | grep {sim_udid} | head -1"
    elif action == "key_down":
        key = params.get("key", "")
        return f"xcrun simctl io {sim_udid} sendkey {key}"
    elif action == "key_up":
        return "true"  # simctl has no separate key_up
    return None


async def handle_mobile_action(device: object, action: str, params: dict) -> dict:
    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    instance_id = ids.get("instance_id", "")
    sim_udid = ids.get("sim_udid", "")
    region = ids.get("region", "us-east-1")
    ssm = boto3.client("ssm", region_name=region)

    if action == "long_press":
        x, y = params.get("x", 0), params.get("y", 0)
        duration_ms = int(params.get("duration_ms", 800))
        cmd = (
            f"osascript -e 'tell application \"Simulator\" to activate' "
            f"-e 'tell application \"System Events\" to tell process \"Simulator\" "
            f"to click at {{{x}, {y}}} with delay {duration_ms / 1000:.2f}'"
        )
        ssm.send_command(InstanceIds=[instance_id], DocumentName="AWS-RunShellScript",
                         Parameters={"commands": [cmd]})
        return {"success": True, "action": "long_press"}

    elif action == "press_button":
        button = params.get("button", "home")
        button_map = {
            "home": "home",
            "lock": "lock",
            "side_button": "sideButton",
            "apple_pay": "applePay",
            "rotate_left": "rotateLeft",
            "rotate_right": "rotateRight",
        }
        simctl_button = button_map.get(button, button)
        cmd = f"xcrun simctl io {sim_udid} button {simctl_button}"
        ssm.send_command(InstanceIds=[instance_id], DocumentName="AWS-RunShellScript",
                         Parameters={"commands": [cmd]})
        return {"success": True, "button": button}

    raise CapabilityUnsupportedError(action, "ios_sim")


def _poll(ssm, command_id: str, instance_id: str, retries: int = 30) -> dict:
    for _ in range(retries):
        time.sleep(1)
        inv = ssm.get_command_invocation(CommandId=command_id, InstanceId=instance_id)
        if inv["Status"] in ("Success", "Failed", "Cancelled", "TimedOut"):
            return {
                "stdout": inv.get("StandardOutputContent", ""),
                "stderr": inv.get("StandardErrorContent", ""),
                "exit_code": inv.get("ResponseCode", 0),
            }
    return {"stdout": "", "stderr": "Timeout", "exit_code": -1}
