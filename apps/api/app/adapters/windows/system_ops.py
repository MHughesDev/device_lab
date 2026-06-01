# system_ops.py — Windows system operations via SSMChannel (PowerShell)
from __future__ import annotations

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
        raise CapabilityUnsupportedError(action, "windows")

    channel = ChannelFactory.get(device)
    result = await channel.exec(cmd)
    out = {"stdout": result.stdout, "stderr": result.stderr, "exit_code": result.exit_code}

    if action == "run_shell":
        return {"success": True, "stdout": out["stdout"], "stderr": out["stderr"], "exit_code": out["exit_code"]}
    if action == "get_clipboard":
        return {"success": True, "text": out["stdout"].strip()}
    if action == "list_windows":
        lines = [l.strip() for l in out["stdout"].splitlines() if l.strip()]
        return {"success": True, "windows": [{"title": l} for l in lines]}
    if action == "list_processes":
        import csv, io
        reader = csv.DictReader(io.StringIO(out["stdout"]))
        procs = [{"pid": r.get("Id", ""), "name": r.get("ProcessName", ""), "cpu": r.get("CPU", "")} for r in reader]
        return {"success": True, "processes": procs}
    if action == "get_screen_size":
        raw = out["stdout"].strip()
        if "," in raw:
            w, h = raw.split(",", 1)
            return {"success": True, "width": int(w.strip()), "height": int(h.strip())}
        return {"success": True, "raw": raw}
    if action == "list_directory":
        lines = [l.strip() for l in out["stdout"].splitlines() if l.strip()]
        return {"success": True, "entries": lines}
    if action == "read_file":
        return {"success": True, "content": out["stdout"]}
    if action == "wait_for":
        found = "1" in out["stdout"]
        return {"success": True, "found": found}
    return {"success": True, "action": action, "output": out["stdout"]}


_FORMS = "Add-Type -AssemblyName System.Windows.Forms; "
_DRAWING = "Add-Type -AssemblyName System.Drawing; "


def _build_cmd(action: str, params: dict) -> str | None:
    if action == "run_shell":
        cmd = params.get("command", "").replace("'", "''")
        return f"Invoke-Expression '{cmd}' 2>&1"
    elif action == "get_clipboard":
        return f"{_FORMS}[System.Windows.Forms.Clipboard]::GetText()"
    elif action == "set_clipboard":
        text = params.get("text", "").replace("'", "''")
        return f"{_FORMS}[System.Windows.Forms.Clipboard]::SetText('{text}')"
    elif action == "launch_app":
        app = params.get("app", "").replace("'", "''")
        return f"Start-Process '{app}'"
    elif action == "wait_for":
        condition = params.get("condition", "").replace("'", "''")
        timeout_ms = int(params.get("timeout_ms", 10000))
        return (
            f"$end = (Get-Date).AddMilliseconds({timeout_ms}); "
            f"while ((Get-Date) -lt $end) {{ "
            f"  $w = (Get-Process | Where-Object {{$_.MainWindowTitle -like '*{condition}*'}}); "
            f"  if ($w) {{ Write-Output 1; exit 0 }}; "
            f"  Start-Sleep -Milliseconds 500 "
            f"}}; Write-Output 0"
        )
    elif action == "read_file":
        path = params.get("path", "").replace("'", "''")
        return f"Get-Content -Path '{path}' -Raw"
    elif action == "write_file":
        path = params.get("path", "").replace("'", "''")
        content = params.get("content", "").replace("'", "''")
        return f"Set-Content -Path '{path}' -Value '{content}'"
    elif action == "list_directory":
        path = params.get("path", ".").replace("'", "''")
        return f"Get-ChildItem -Path '{path}' | Select-Object -ExpandProperty Name"
    elif action == "list_windows":
        return "Get-Process | Where-Object {$_.MainWindowTitle} | Select-Object -ExpandProperty MainWindowTitle"
    elif action == "focus_window":
        title = params.get("title", "").replace("'", "''")
        return (
            "Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; "
            "public class WinAPI { [DllImport(\"user32.dll\")] public static extern bool SetForegroundWindow(IntPtr hWnd); }'; "
            f"$p = Get-Process | Where-Object {{$_.MainWindowTitle -like '*{title}*'}} | Select-Object -First 1; "
            f"if ($p) {{ [WinAPI]::SetForegroundWindow($p.MainWindowHandle) }}"
        )
    elif action == "resize_window":
        title = params.get("title", "").replace("'", "''")
        w, h = params.get("width", 800), params.get("height", 600)
        return (
            "Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; "
            "public class WinAPI2 { "
            "[DllImport(\"user32.dll\")] public static extern bool MoveWindow(IntPtr h, int x, int y, int w, int h2, bool r); "
            "}'; "
            f"$p = Get-Process | Where-Object {{$_.MainWindowTitle -like '*{title}*'}} | Select-Object -First 1; "
            f"if ($p) {{ [WinAPI2]::MoveWindow($p.MainWindowHandle, 0, 0, {w}, {h}, $true) }}"
        )
    elif action == "list_processes":
        return "Get-Process | Select-Object Id,ProcessName,CPU | ConvertTo-Csv -NoTypeInformation"
    elif action == "kill_process":
        p = params.get("pid_or_name", "")
        if p.isdigit():
            return f"Stop-Process -Id {p} -Force -ErrorAction SilentlyContinue"
        return f"Stop-Process -Name '{p}' -Force -ErrorAction SilentlyContinue"
    elif action == "get_screen_size":
        return f"{_DRAWING}$b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds; Write-Output \"$($b.Width),$($b.Height)\""
    elif action == "key_down":
        key = params.get("key", "").replace("'", "''")
        return (
            "Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; "
            "public class KbAPI { [DllImport(\"user32.dll\")] public static extern void keybd_event(byte k, byte s, uint f, UIntPtr e); }'; "
            f"[KbAPI]::keybd_event([System.Windows.Forms.Keys]::'{key}', 0, 0, [UIntPtr]::Zero)"
        )
    elif action == "key_up":
        key = params.get("key", "").replace("'", "''")
        return (
            "Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; "
            "public class KbAPI2 { [DllImport(\"user32.dll\")] public static extern void keybd_event(byte k, byte s, uint f, UIntPtr e); }'; "
            f"[KbAPI2]::keybd_event([System.Windows.Forms.Keys]::'{key}', 0, 0x0002, [UIntPtr]::Zero)"
        )
    return None
