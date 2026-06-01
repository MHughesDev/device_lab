# interaction.py — Windows interaction via SSM PowerShell (coordinate-based)
from __future__ import annotations
import json
import time

import boto3

from app.adapters.spi import CapabilityUnsupportedError

SUPPORTED_ACTIONS = {
    "click", "double_click", "right_click", "mouse_move",
    "drag", "scroll", "cursor_position", "type", "key",
}


async def act_windows(device: object, action: str, params: dict) -> dict:
    if action not in SUPPORTED_ACTIONS:
        raise CapabilityUnsupportedError(action, "windows")

    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    instance_id = ids.get("instance_id", "")
    region = ids.get("region", "us-east-1")

    cmd = _build_ps_command(action, params)
    ssm = boto3.client("ssm", region_name=region)
    resp = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunPowerShellScript",
        Parameters={"commands": [cmd]},
    )

    if action == "cursor_position":
        command_id = resp["Command"]["CommandId"]
        for _ in range(10):
            time.sleep(1)
            inv = ssm.get_command_invocation(CommandId=command_id, InstanceId=instance_id)
            if inv["Status"] in ("Success", "Failed"):
                raw = inv.get("StandardOutputContent", "").strip()
                # Output format: "x,y"
                parts = raw.split(",")
                return {
                    "success": True,
                    "x": int(parts[0]) if parts else 0,
                    "y": int(parts[1]) if len(parts) > 1 else 0,
                }

    return {"success": True, "action": action}


# Shared preamble for mouse_event P/Invoke
_MOUSE_SIG = (
    "Add-Type -AssemblyName System.Windows.Forms; "
    "Add-Type -AssemblyName System.Drawing; "
    "$sig = '[DllImport(\"user32.dll\")] public static extern void mouse_event(int f, int x, int y, int c, int e);'; "
    "Add-Type -MemberDefinition $sig -Name U32 -Namespace U; "
)

_MOUSE_LEFTDOWN = 0x0002
_MOUSE_LEFTUP = 0x0004
_MOUSE_RIGHTDOWN = 0x0008
_MOUSE_RIGHTUP = 0x0010
_MOUSE_MIDDLEDOWN = 0x0020
_MOUSE_MIDDLEUP = 0x0040


def _move_and(x: int, y: int, extra: str) -> str:
    return (
        f"{_MOUSE_SIG}"
        f"[System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point({x},{y}); "
        f"{extra}"
    )


def _build_ps_command(action: str, params: dict) -> str:
    x, y = params.get("x", 0), params.get("y", 0)
    button = params.get("button", "left")
    down_flag = {"left": _MOUSE_LEFTDOWN, "right": _MOUSE_RIGHTDOWN, "middle": _MOUSE_MIDDLEDOWN}
    up_flag = {"left": _MOUSE_LEFTUP, "right": _MOUSE_RIGHTUP, "middle": _MOUSE_MIDDLEUP}

    if action == "click":
        df, uf = down_flag.get(button, _MOUSE_LEFTDOWN), up_flag.get(button, _MOUSE_LEFTUP)
        return _move_and(x, y, f"[U.U32]::mouse_event({df},0,0,0,0); [U.U32]::mouse_event({uf},0,0,0,0)")
    elif action == "double_click":
        ldown, lup = _MOUSE_LEFTDOWN, _MOUSE_LEFTUP
        return _move_and(x, y,
            f"[U.U32]::mouse_event({ldown},0,0,0,0); [U.U32]::mouse_event({lup},0,0,0,0); "
            f"Start-Sleep -Milliseconds 80; "
            f"[U.U32]::mouse_event({ldown},0,0,0,0); [U.U32]::mouse_event({lup},0,0,0,0)")
    elif action == "right_click":
        return _move_and(x, y,
            f"[U.U32]::mouse_event({_MOUSE_RIGHTDOWN},0,0,0,0); "
            f"[U.U32]::mouse_event({_MOUSE_RIGHTUP},0,0,0,0)")
    elif action == "mouse_move":
        return (
            f"{_MOUSE_SIG}"
            f"[System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point({x},{y})"
        )
    elif action == "drag":
        ex, ey = params.get("end_x", 0), params.get("end_y", 0)
        return _move_and(x, y,
            f"[U.U32]::mouse_event({_MOUSE_LEFTDOWN},0,0,0,0); "
            f"[System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point({ex},{ey}); "
            f"[U.U32]::mouse_event({_MOUSE_LEFTUP},0,0,0,0)")
    elif action == "scroll":
        direction = params.get("direction", "down")
        amount = int(params.get("amount", 3)) * 120  # WHEEL_DELTA = 120
        delta = -amount if direction == "down" else amount
        _WHEEL = 0x0800
        return _move_and(x, y, f"[U.U32]::mouse_event({_WHEEL},0,0,{delta},0)")
    elif action == "cursor_position":
        return (
            "Add-Type -AssemblyName System.Windows.Forms; "
            "$p = [System.Windows.Forms.Cursor]::Position; Write-Output \"$($p.X),$($p.Y)\""
        )
    elif action == "type":
        text = params.get("text", "").replace("'", "''")
        return (
            "Add-Type -AssemblyName System.Windows.Forms; "
            f"[System.Windows.Forms.SendKeys]::SendWait('{text}')"
        )
    elif action == "key":
        key = params.get("key", "Return")
        sendkeys = _to_sendkeys(key)
        return (
            "Add-Type -AssemblyName System.Windows.Forms; "
            f"[System.Windows.Forms.SendKeys]::SendWait('{sendkeys}')"
        )
    return ""


def _to_sendkeys(key: str) -> str:
    """Map standard key names to SendKeys format."""
    mapping = {
        "Return": "{ENTER}", "Escape": "{ESC}", "Tab": "{TAB}",
        "BackSpace": "{BACKSPACE}", "Delete": "{DELETE}",
        "ctrl+c": "^c", "ctrl+v": "^v", "ctrl+z": "^z", "ctrl+a": "^a",
        "ctrl+x": "^x", "ctrl+s": "^s", "ctrl+w": "^w",
        "alt+F4": "%{F4}", "alt+Tab": "%{TAB}",
        "F1": "{F1}", "F2": "{F2}", "F5": "{F5}",
        "Left": "{LEFT}", "Right": "{RIGHT}", "Up": "{UP}", "Down": "{DOWN}",
        "Home": "{HOME}", "End": "{END}",
    }
    return mapping.get(key, f"{{{key}}}")


async def screenshot_b64(device: object) -> str:
    """Capture full-desktop screenshot via PowerShell, return base64-encoded PNG."""
    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    instance_id = ids.get("instance_id", "")
    region = ids.get("region", "us-east-1")

    ps_cmd = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "Add-Type -AssemblyName System.Drawing; "
        "$b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds; "
        "$bmp = New-Object System.Drawing.Bitmap($b.Width, $b.Height); "
        "$g = [System.Drawing.Graphics]::FromImage($bmp); "
        "$g.CopyFromScreen($b.Location, [System.Drawing.Point]::Empty, $b.Size); "
        "$g.Dispose(); "
        "$ms = New-Object System.IO.MemoryStream; "
        "$bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png); "
        "[Convert]::ToBase64String($ms.ToArray())"
    )

    ssm = boto3.client("ssm", region_name=region)
    resp = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunPowerShellScript",
        Parameters={"commands": [ps_cmd]},
    )
    command_id = resp["Command"]["CommandId"]
    import time
    for _ in range(15):
        time.sleep(1)
        inv = ssm.get_command_invocation(CommandId=command_id, InstanceId=instance_id)
        if inv["Status"] in ("Success", "Failed"):
            return inv.get("StandardOutputContent", "").strip()
    return ""
