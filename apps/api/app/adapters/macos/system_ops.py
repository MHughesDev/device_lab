# system_ops.py — macOS system operations via SSMChannel + cliclick/osascript/standard tools
from __future__ import annotations
import json

from app.adapters.spi import CapabilityUnsupportedError
from app.transport.channel import ChannelFactory

SYSTEM_ACTIONS = {
    "run_shell", "get_clipboard", "set_clipboard", "launch_app", "wait_for",
    "read_file", "write_file", "list_directory",
    "list_windows", "focus_window", "resize_window",
    "list_processes", "kill_process", "get_screen_size",
    "key_down", "key_up",
}


async def handle_system_action(device: object, action: str, params: dict) -> dict:
    cmd = _build_cmd(action, params)
    if cmd is None:
        raise CapabilityUnsupportedError(action, "macos")

    channel = ChannelFactory.get(device)
    result = await channel.exec(cmd)
    out = {"stdout": result.stdout, "stderr": result.stderr, "exit_code": result.exit_code}

    if action == "run_shell":
        return {"success": True, "stdout": out["stdout"], "stderr": out["stderr"], "exit_code": out["exit_code"]}
    if action == "get_clipboard":
        return {"success": True, "text": out["stdout"].strip()}
    if action == "list_windows":
        raw = out["stdout"].strip()
        windows = [{"title": line} for line in raw.splitlines() if line.strip()]
        return {"success": True, "windows": windows}
    if action == "list_processes":
        lines = out["stdout"].strip().splitlines()
        procs = []
        for line in lines[1:]:
            parts = line.split(None, 3)
            if len(parts) >= 4:
                procs.append({"pid": parts[0], "cpu": parts[1], "mem": parts[2], "name": parts[3]})
        return {"success": True, "processes": procs}
    if action == "get_screen_size":
        raw = out["stdout"].strip()
        # Format: "1920 x 1080" or "1920x1080"
        raw = raw.replace(" x ", "x").replace("x", " ").split()
        if len(raw) >= 2:
            return {"success": True, "width": int(raw[0]), "height": int(raw[1])}
        return {"success": True, "raw": out["stdout"]}
    if action == "list_directory":
        lines = [l for l in out["stdout"].splitlines() if l.strip()]
        return {"success": True, "entries": lines}
    if action == "read_file":
        return {"success": True, "content": out["stdout"]}
    if action == "wait_for":
        found = out["stdout"].strip() == "1"
        return {"success": True, "found": found}
    return {"success": True, "action": action, "output": out["stdout"]}


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
