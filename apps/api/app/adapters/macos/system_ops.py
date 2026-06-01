# system_ops.py — macOS system operations via SSM + cliclick/osascript/standard tools
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
        raise CapabilityUnsupportedError(action, "macos")

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
        raw = out.get("stdout", "").strip()
        windows = [{"title": line} for line in raw.splitlines() if line.strip()]
        return {"success": True, "windows": windows}
    if action == "list_processes":
        lines = out.get("stdout", "").strip().splitlines()
        procs = []
        for line in lines[1:]:
            parts = line.split(None, 3)
            if len(parts) >= 4:
                procs.append({"pid": parts[0], "cpu": parts[1], "mem": parts[2], "name": parts[3]})
        return {"success": True, "processes": procs}
    if action == "get_screen_size":
        raw = out.get("stdout", "").strip()
        # Format: "1920 x 1080" or "1920x1080"
        raw = raw.replace(" x ", "x").replace("x", " ").split()
        if len(raw) >= 2:
            return {"success": True, "width": int(raw[0]), "height": int(raw[1])}
        return {"success": True, "raw": out.get("stdout", "")}
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
        return "pbpaste"
    elif action == "set_clipboard":
        text = params.get("text", "").replace("'", "'\\''")
        return f"echo '{text}' | pbcopy"
    elif action == "launch_app":
        app = params.get("app", "")
        # Try as app name first, then as path
        return f"open -a {json.dumps(app)} 2>/dev/null || open {json.dumps(app)} 2>/dev/null || nohup {json.dumps(app)} &"
    elif action == "wait_for":
        condition = params.get("condition", "").replace("'", "'\\''")
        timeout_ms = int(params.get("timeout_ms", 10000))
        timeout_s = timeout_ms // 1000
        return (
            f"END=$((SECONDS+{timeout_s})); "
            f"while [ $SECONDS -lt $END ]; do "
            f"  TEXT=$(osascript -e 'tell application \"System Events\" to get name of first window of (first application process whose frontmost is true)' 2>/dev/null); "
            f"  if echo \"$TEXT\" | grep -qi '{condition}'; then echo 1; exit 0; fi; "
            f"  sleep 0.5; "
            f"done; echo 0"
        )
    elif action == "read_file":
        return f"cat {json.dumps(params.get('path', ''))}"
    elif action == "write_file":
        path = params.get("path", "")
        content = params.get("content", "")
        return f"cat > {json.dumps(path)} << 'DEVICELAB_EOF'\n{content}\nDEVICELAB_EOF"
    elif action == "list_directory":
        return f"ls -la {json.dumps(params.get('path', '.'))}"
    elif action == "list_windows":
        return "osascript -e 'tell application \"System Events\" to get name of every window of every application process'"
    elif action == "focus_window":
        title = params.get("title", "")
        return f"osascript -e 'tell application \"{title}\" to activate'"
    elif action == "resize_window":
        title = params.get("title", "")
        w, h = params.get("width", 800), params.get("height", 600)
        return (
            f"osascript -e 'tell application \"{title}\" to activate' "
            f"-e 'tell application \"System Events\" to set size of first window of (first application process whose name is \"{title}\") to {{{w}, {h}}}'"
        )
    elif action == "list_processes":
        return "ps aux --no-headers -o pid,pcpu,pmem,comm 2>/dev/null | head -50"
    elif action == "kill_process":
        p = params.get("pid_or_name", "")
        if p.isdigit():
            return f"kill {p} 2>&1"
        return f"pkill -f {json.dumps(p)} 2>&1"
    elif action == "get_screen_size":
        return "system_profiler SPDisplaysDataType 2>/dev/null | grep Resolution | head -1 | awk '{print $2, $4}'"
    elif action == "key_down":
        key = params.get("key", "")
        return f"cliclick kd:{key} 2>/dev/null"
    elif action == "key_up":
        key = params.get("key", "")
        return f"cliclick ku:{key} 2>/dev/null"
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
    return {"stdout": "", "stderr": "Timeout", "exit_code": -1}
