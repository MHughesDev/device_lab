# interaction.py — Windows interaction via SSM RunCommand (PowerShell + pywinauto)
from __future__ import annotations
from app.adapters.spi import CapabilityUnsupportedError

SUPPORTED_ACTIONS = {"click", "type", "key", "scroll"}


async def act_windows(device: object, action: str, params: dict) -> dict:
    """Execute action via SSM RunCommand. Raises CapabilityUnsupportedError for unsupported."""
    if action not in SUPPORTED_ACTIONS:
        raise CapabilityUnsupportedError(action, "windows")

    import json, boto3
    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    instance_id = ids.get("instance_id", "")
    region = ids.get("region", "us-east-1")

    command = _build_ps_command(action, params)
    ssm = boto3.client("ssm", region_name=region)
    ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunPowerShellScript",
        Parameters={"commands": [command]},
    )
    return {"success": True, "action": action}


def _build_ps_command(action: str, params: dict) -> str:
    if action == "click":
        x, y = params.get("x", 0), params.get("y", 0)
        return f"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point({x},{y}); $sig = '[DllImport(\"user32.dll\")] public static extern void mouse_event(int f, int x, int y, int c, int e);'; Add-Type -MemberDefinition $sig -Name U32 -Namespace U; [U.U32]::mouse_event(6,0,0,0,0)"
    elif action == "type":
        text = params.get("text", "").replace("'", "''")
        return f"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('{text}')"
    elif action == "key":
        key = params.get("keycode", "ENTER")
        return f"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('%{{{key}}}')"
    elif action == "scroll":
        steps = params.get("steps", 3)
        return f"Add-Type -AssemblyName System.Windows.Forms; for ($i=0; $i -lt {steps}; $i++) {{ [System.Windows.Forms.SendKeys]::SendWait('{{PGDN}}') }}"
    return ""
