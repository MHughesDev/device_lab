# system_ops.py — Linux system operations via SSM + standard Unix tools
from __future__ import annotations
import json
import time

import boto3

from app.adapters.spi import CapabilityUnsupportedError

SYSTEM_ACTIONS = {
    "run_shell", "get_clipboard", "set_clipboard", "launch_app", "wait_for",
    "read_file", "write_file", "list_directory",
    "list_windows", "focus_window", "resize_window",
    "list_processes", "kill_process", "get_screen_size",
    "key_down", "key_up",
}


async def handle_system_action(device: object, action: str, params: dict) -> dict:
    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    instance_id = ids.get("instance_id", "")
    region = ids.get("region", "us-east-1")
    ssm = boto3.client("ssm", region_name=region)

    cmd = _build_cmd(action, params)
    if cmd is None:
        raise CapabilityUnsupportedError(action, "linux")

    resp = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": [cmd]},
    )
    out = _poll(ssm, resp["Command"]["CommandId"], instance_id)

    if action == "run_shell":
        return {"success": True, "stdout": out.get("stdout", ""), "stderr": out.get("stderr", ""), "exit_code": out.get("exit_code", 0)}
    if action == "get_clipboard":
        return {"success": True, "text": out.get("stdout", "").strip()}
    if action == "list_windows":
        lines = [l for l in out.get("stdout", "").splitlines() if l.strip()]
        windows = []
        for line in lines:
            parts = line.split(None, 4)
            if len(parts) >= 5:
                windows.append({"id": parts[0], "desktop": parts[1], "x": parts[2], "y": parts[3], "title": parts[4]})
        return {"success": True, "windows": windows}
    if action == "list_processes":
        lines = out.get("stdout", "").strip().splitlines()
        procs = []
        for line in lines[1:]:  # skip header
            parts = line.split(None, 3)
            if len(parts) >= 4:
                procs.append({"pid": parts[0], "cpu": parts[1], "mem": parts[2], "name": parts[3]})
        return {"success": True, "processes": procs}
    if action == "get_screen_size":
        raw = out.get("stdout", "").strip()  # e.g. "1920x1080"
        if "x" in raw:
            w, h = raw.split("x", 1)
            return {"success": True, "width": int(w.strip()), "height": int(h.strip())}
        return {"success": True, "raw": raw}
    if action == "list_directory":
        lines = [l for l in out.get("stdout", "").splitlines() if l.strip()]
        return {"success": True, "entries": lines}
    if action == "read_file":
        return {"success": True, "content": out.get("stdout", "")}
    if action == "wait_for":
        found = out.get("stdout", "").strip() == "1"
        return {"success": True, "found": found}
    return {"success": True, "action": action, "output": out.get("stdout", "")}


def _build_cmd(action: str, params: dict) -> str | None:
    if action == "run_shell":
        cmd = params.get("command", "")
        return f"bash -c {json.dumps(cmd)} 2>&1"
    elif action == "get_clipboard":
        return "DISPLAY=:0 xclip -selection clipboard -o 2>/dev/null || xsel --clipboard --output 2>/dev/null || echo ''"
    elif action == "set_clipboard":
        text = params.get("text", "").replace("'", "'\\''")
        return f"echo '{text}' | DISPLAY=:0 xclip -selection clipboard 2>/dev/null || echo '{text}' | xsel --clipboard --input 2>/dev/null"
    elif action == "launch_app":
        app = params.get("app", "")
        return f"DISPLAY=:0 nohup {app} >/tmp/app-launch.log 2>&1 &"
    elif action == "wait_for":
        condition = params.get("condition", "").replace("'", "'\\''")
        timeout_ms = int(params.get("timeout_ms", 10000))
        timeout_s = timeout_ms // 1000
        return (
            f"END=$((SECONDS+{timeout_s})); "
            f"while [ $SECONDS -lt $END ]; do "
            f"  TEXT=$(DISPLAY=:0 xdotool getactivewindow getwindowname 2>/dev/null); "
            f"  if echo \"$TEXT\" | grep -q '{condition}'; then echo 1; exit 0; fi; "
            f"  sleep 0.5; "
            f"done; echo 0"
        )
    elif action == "read_file":
        path = params.get("path", "")
        return f"cat {json.dumps(path)}"
    elif action == "write_file":
        path = params.get("path", "")
        content = params.get("content", "")
        # Write via heredoc
        return f"cat > {json.dumps(path)} << 'DEVICELAB_EOF'\n{content}\nDEVICELAB_EOF"
    elif action == "list_directory":
        path = params.get("path", ".")
        return f"ls -la {json.dumps(path)} 2>&1"
    elif action == "list_windows":
        return "wmctrl -l 2>/dev/null || echo 'wmctrl not installed'"
    elif action == "focus_window":
        title = params.get("title", "").replace("'", "'\\''")
        return f"DISPLAY=:0 wmctrl -a '{title}' 2>/dev/null"
    elif action == "resize_window":
        title = params.get("title", "").replace("'", "'\\''")
        w, h = params.get("width", 800), params.get("height", 600)
        return f"DISPLAY=:0 wmctrl -r '{title}' -e 0,-1,-1,{w},{h} 2>/dev/null"
    elif action == "list_processes":
        return "ps aux --no-headers -o pid,pcpu,pmem,comm 2>/dev/null | head -50"
    elif action == "kill_process":
        pid_or_name = params.get("pid_or_name", "")
        if pid_or_name.isdigit():
            return f"kill {pid_or_name} 2>&1"
        else:
            return f"pkill -f {json.dumps(pid_or_name)} 2>&1"
    elif action == "get_screen_size":
        return "DISPLAY=:0 xdpyinfo 2>/dev/null | awk '/dimensions/{print $2}' | head -1"
    elif action == "key_down":
        key = params.get("key", "")
        return f"DISPLAY=:0 xdotool keydown {key}"
    elif action == "key_up":
        key = params.get("key", "")
        return f"DISPLAY=:0 xdotool keyup {key}"
    return None


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
    return {"stdout": "", "stderr": "Timeout waiting for SSM command", "exit_code": -1}
