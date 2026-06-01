# system_ops.py — iOS Simulator system operations via SSMChannel + xcrun simctl
from __future__ import annotations
import json

from app.adapters.spi import CapabilityUnsupportedError
from app.transport.channel import ChannelFactory

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
    sim_udid = ids.get("sim_udid", "")

    cmd = _build_cmd(action, params, sim_udid)
    if cmd is None:
        raise CapabilityUnsupportedError(action, "ios_sim")

    channel = ChannelFactory.get(device)
    result = await channel.exec(cmd)
    out = {"stdout": result.stdout, "stderr": result.stderr, "exit_code": result.exit_code}

    if action == "run_shell":
        return {"success": True, "stdout": out["stdout"], "stderr": out["stderr"], "exit_code": out["exit_code"]}
    if action == "read_file":
        return {"success": True, "content": out["stdout"]}
    if action == "list_directory":
        lines = [l for l in out["stdout"].splitlines() if l.strip()]
        return {"success": True, "entries": lines}
    if action == "list_processes":
        lines = out["stdout"].strip().splitlines()
        procs = [{"line": l} for l in lines if l.strip()]
        return {"success": True, "processes": procs}
    if action == "get_screen_size":
        raw = out["stdout"].strip()
        if "x" in raw:
            w, h = raw.split("x")
            return {"success": True, "width": int(w.strip()), "height": int(h.strip())}
        return {"success": True, "raw": raw}
    return {"success": True, "action": action, "output": out["stdout"]}


def _build_cmd(action: str, params: dict, sim_udid: str) -> str | None:
    if action == "run_shell":
        cmd = params.get("command", "")
        return f"xcrun simctl spawn {sim_udid} bash -c {json.dumps(cmd)} 2>&1"
    elif action == "launch_app":
        bundle_id = params.get("app", "")
        return f"xcrun simctl launch {sim_udid} {bundle_id} 2>&1"
    elif action == "read_file":
        path = params.get("path", "")
        return f"xcrun simctl spawn {sim_udid} cat {json.dumps(path)} 2>&1"
    elif action == "list_directory":
        path = params.get("path", "/")
        return f"xcrun simctl spawn {sim_udid} ls -la {json.dumps(path)} 2>&1"
    elif action == "list_processes":
        return f"xcrun simctl spawn {sim_udid} ps aux 2>&1 | head -30"
    elif action == "get_screen_size":
        return f"xcrun simctl list devices | grep {sim_udid} | head -1"
    elif action == "key_down":
        key = params.get("key", "")
        return f"xcrun simctl io {sim_udid} sendkey {key}"
    elif action == "key_up":
        return "true"  # simctl has no separate key_up
    return None


async def handle_mobile_action(device: object, action: str, params: dict) -> dict:
    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    sim_udid = ids.get("sim_udid", "")

    if action == "long_press":
        x, y = params.get("x", 0), params.get("y", 0)
        duration_ms = int(params.get("duration_ms", 800))
        cmd = (
            f"osascript -e 'tell application \"Simulator\" to activate' "
            f"-e 'tell application \"System Events\" to tell process \"Simulator\" "
            f"to click at {{{x}, {y}}} with delay {duration_ms / 1000:.2f}'"
        )
        channel = ChannelFactory.get(device)
        await channel.exec(cmd)
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
        channel = ChannelFactory.get(device)
        await channel.exec(cmd)
        return {"success": True, "button": button}

    raise CapabilityUnsupportedError(action, "ios_sim")
