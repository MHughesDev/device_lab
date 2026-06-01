# system_ops.py — Android system operations via adb + mobile gestures
from __future__ import annotations
import json
import subprocess

from app.adapters.spi import CapabilityUnsupportedError

SYSTEM_ACTIONS = {
    "run_shell", "read_file", "write_file", "list_directory",
    "list_processes", "kill_process", "get_screen_size",
    "key_down", "key_up",
    # clipboard, launch_app, wait_for, list/focus/resize_windows not applicable
}

MOBILE_ACTIONS = {"long_press", "pinch", "press_button"}


async def handle_system_action(device: object, action: str, params: dict) -> dict:
    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    adb_serial = ids.get("adb_serial", "emulator-5554")

    if action == "run_shell":
        cmd = params.get("command", "")
        result = subprocess.run(
            ["adb", "-s", adb_serial, "shell", cmd],
            capture_output=True, text=True, timeout=30,
        )
        return {"success": True, "stdout": result.stdout, "stderr": result.stderr, "exit_code": result.returncode}

    elif action == "read_file":
        path = params.get("path", "")
        result = subprocess.run(
            ["adb", "-s", adb_serial, "shell", "cat", path],
            capture_output=True, text=True,
        )
        return {"success": result.returncode == 0, "content": result.stdout, "error": result.stderr or None}

    elif action == "write_file":
        import tempfile, os
        path = params.get("path", "")
        content = params.get("content", "")
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".tmp") as f:
            f.write(content)
            tmp = f.name
        result = subprocess.run(["adb", "-s", adb_serial, "push", tmp, path], capture_output=True)
        os.unlink(tmp)
        return {"success": result.returncode == 0}

    elif action == "list_directory":
        path = params.get("path", "/sdcard")
        result = subprocess.run(
            ["adb", "-s", adb_serial, "shell", "ls", "-la", path],
            capture_output=True, text=True,
        )
        lines = [l for l in result.stdout.splitlines() if l.strip()]
        return {"success": True, "entries": lines}

    elif action == "list_processes":
        result = subprocess.run(
            ["adb", "-s", adb_serial, "shell", "ps", "-A"],
            capture_output=True, text=True,
        )
        lines = result.stdout.splitlines()
        procs = []
        for line in lines[1:]:
            parts = line.split()
            if len(parts) >= 9:
                procs.append({"user": parts[0], "pid": parts[1], "name": parts[-1]})
        return {"success": True, "processes": procs}

    elif action == "kill_process":
        p = params.get("pid_or_name", "")
        if p.isdigit():
            subprocess.run(["adb", "-s", adb_serial, "shell", "kill", p], capture_output=True)
        else:
            subprocess.run(["adb", "-s", adb_serial, "shell", "am", "force-stop", p], capture_output=True)
        return {"success": True}

    elif action == "get_screen_size":
        result = subprocess.run(
            ["adb", "-s", adb_serial, "shell", "wm", "size"],
            capture_output=True, text=True,
        )
        # Output: "Physical size: 1080x2340"
        raw = result.stdout.strip()
        if "x" in raw:
            dims = raw.split(":")[-1].strip()
            w, h = dims.split("x")
            return {"success": True, "width": int(w), "height": int(h)}
        return {"success": True, "raw": raw}

    elif action == "key_down":
        # Android doesn't have true key-hold; send keyevent with LONG_PRESS flag
        key = _to_android_keycode(params.get("key", ""))
        subprocess.run(["adb", "-s", adb_serial, "shell", "input", "keyevent", "--longpress", key], capture_output=True)
        return {"success": True}

    elif action == "key_up":
        # No distinct key_up on Android; just return success (key_down handles the event)
        return {"success": True, "note": "key_up is a no-op on Android; use key() for single presses"}

    raise CapabilityUnsupportedError(action, "android")


async def handle_mobile_action(device: object, action: str, params: dict) -> dict:
    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    adb_serial = ids.get("adb_serial", "emulator-5554")

    if action == "long_press":
        x, y = params.get("x", 0), params.get("y", 0)
        duration_ms = int(params.get("duration_ms", 800))
        # adb swipe with same start/end coords = long press
        subprocess.run(
            ["adb", "-s", adb_serial, "shell", "input", "swipe",
             str(x), str(y), str(x), str(y), str(duration_ms)],
            capture_output=True,
        )
        return {"success": True, "action": "long_press"}

    elif action == "pinch":
        x, y = params.get("x", 0), params.get("y", 0)
        scale = float(params.get("scale", 1.0))
        # Simulate pinch via two-pointer swipe using sendevent or input
        # Use adb shell input swipe for two-finger approximation
        offset = int(100 * abs(1 - scale))
        if scale < 1.0:  # pinch in: fingers move toward center
            subprocess.run(["adb", "-s", adb_serial, "shell",
                "input", "swipe", str(x - offset), str(y), str(x), str(y), "200"], capture_output=True)
            subprocess.run(["adb", "-s", adb_serial, "shell",
                "input", "swipe", str(x + offset), str(y), str(x), str(y), "200"], capture_output=True)
        else:  # spread: fingers move apart
            subprocess.run(["adb", "-s", adb_serial, "shell",
                "input", "swipe", str(x), str(y), str(x - offset), str(y), "200"], capture_output=True)
            subprocess.run(["adb", "-s", adb_serial, "shell",
                "input", "swipe", str(x), str(y), str(x + offset), str(y), "200"], capture_output=True)
        return {"success": True, "action": "pinch", "scale": scale}

    elif action == "press_button":
        button = params.get("button", "home")
        keycode = {
            "home": "KEYCODE_HOME",
            "back": "KEYCODE_BACK",
            "menu": "KEYCODE_MENU",
            "recent_apps": "KEYCODE_APP_SWITCH",
            "power": "KEYCODE_POWER",
            "volume_up": "KEYCODE_VOLUME_UP",
            "volume_down": "KEYCODE_VOLUME_DOWN",
        }.get(button, f"KEYCODE_{button.upper()}")
        subprocess.run(["adb", "-s", adb_serial, "shell", "input", "keyevent", keycode], capture_output=True)
        return {"success": True, "button": button}

    raise CapabilityUnsupportedError(action, "android")


def _to_android_keycode(key: str) -> str:
    mapping = {
        "Return": "KEYCODE_ENTER", "Escape": "KEYCODE_ESCAPE",
        "BackSpace": "KEYCODE_DEL", "Tab": "KEYCODE_TAB",
    }
    return mapping.get(key, key)
