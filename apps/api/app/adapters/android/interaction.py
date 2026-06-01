# interaction.py — Android interaction via adb (coordinate-based)
from __future__ import annotations
import base64
import json
import subprocess

from app.adapters.spi import CapabilityUnsupportedError

SUPPORTED_ACTIONS = {
    "click", "double_click", "drag", "scroll", "type", "key",
    # right_click, mouse_move, cursor_position not applicable on touchscreen
}


async def act_android(device: object, action: str, params: dict) -> dict:
    if action not in SUPPORTED_ACTIONS:
        raise CapabilityUnsupportedError(action, "android")

    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    adb_serial = ids.get("adb_serial", "emulator-5554")

    x, y = params.get("x", 0), params.get("y", 0)

    if action == "click":
        subprocess.run(["adb", "-s", adb_serial, "shell", "input", "tap", str(x), str(y)],
                       capture_output=True, check=False)
    elif action == "double_click":
        subprocess.run(["adb", "-s", adb_serial, "shell", "input", "tap", str(x), str(y)],
                       capture_output=True, check=False)
        subprocess.run(["adb", "-s", adb_serial, "shell", "input", "tap", str(x), str(y)],
                       capture_output=True, check=False)
    elif action == "drag":
        ex, ey = params.get("end_x", 0), params.get("end_y", 0)
        duration_ms = params.get("duration_ms", 300)
        subprocess.run(
            ["adb", "-s", adb_serial, "shell", "input", "swipe",
             str(x), str(y), str(ex), str(ey), str(duration_ms)],
            capture_output=True, check=False,
        )
    elif action == "scroll":
        direction = params.get("direction", "down")
        amount = int(params.get("amount", 3)) * 100
        # Translate scroll direction into swipe deltas
        if direction == "down":
            ex, ey = x, y - amount
        elif direction == "up":
            ex, ey = x, y + amount
        elif direction == "right":
            ex, ey = x - amount, y
        else:  # left
            ex, ey = x + amount, y
        subprocess.run(
            ["adb", "-s", adb_serial, "shell", "input", "swipe",
             str(x), str(y), str(ex), str(ey), "200"],
            capture_output=True, check=False,
        )
    elif action == "type":
        # adb input text doesn't handle spaces well; use URL encoding
        text = params.get("text", "").replace(" ", "%s")
        subprocess.run(["adb", "-s", adb_serial, "shell", "input", "text", text],
                       capture_output=True, check=False)
    elif action == "key":
        keycode = _to_android_keycode(params.get("key", "Return"))
        subprocess.run(["adb", "-s", adb_serial, "shell", "input", "keyevent", keycode],
                       capture_output=True, check=False)

    return {"success": True, "action": action}


def _to_android_keycode(key: str) -> str:
    mapping = {
        "Return": "KEYCODE_ENTER", "Escape": "KEYCODE_ESCAPE",
        "BackSpace": "KEYCODE_DEL", "Delete": "KEYCODE_FORWARD_DEL",
        "Tab": "KEYCODE_TAB", "Home": "KEYCODE_HOME",
        "Back": "KEYCODE_BACK", "Menu": "KEYCODE_MENU",
        "ctrl+c": "KEYCODE_COPY", "ctrl+v": "KEYCODE_PASTE",
        "ctrl+z": "KEYCODE_UNDO", "ctrl+a": "KEYCODE_SELECT_ALL",
        "Up": "KEYCODE_DPAD_UP", "Down": "KEYCODE_DPAD_DOWN",
        "Left": "KEYCODE_DPAD_LEFT", "Right": "KEYCODE_DPAD_RIGHT",
    }
    return mapping.get(key, key)


async def screenshot_b64(device: object) -> str:
    """Capture screenshot via adb exec-out, return base64-encoded PNG."""
    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    adb_serial = ids.get("adb_serial", "emulator-5554")
    result = subprocess.run(
        ["adb", "-s", adb_serial, "exec-out", "screencap", "-p"],
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        return base64.b64encode(result.stdout).decode()
    return ""
