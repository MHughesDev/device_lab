# observation.py — Windows AX observation via windows_ax.py + SSM RunCommand
from __future__ import annotations
from datetime import UTC, datetime

from app.adapters.spi import CapabilityUnsupportedError
from app.models import ObservationEnvelope

_SUPPORTED_TIERS = {"ax_tree", "screenshot"}


async def observe_windows(device: object, tier: str) -> ObservationEnvelope:
    """
    tier='ax': run windows_ax.py via SSM RunCommand, parse JSON output.
    tier='screenshot': PowerShell screenshot via SSM, return base64 PNG.
    """
    if tier not in _SUPPORTED_TIERS:
        raise CapabilityUnsupportedError(tier, "windows")

    import json
    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    instance_id = ids.get("instance_id", "")
    region = ids.get("region", "us-east-1")

    if tier == "ax_tree":
        structured = await _run_ax_via_ssm(instance_id, region)
        return ObservationEnvelope(
            device_id=str(getattr(device, "id", "")),
            screen_version=getattr(device, "screen_version", 0),
            tier="ax",
            structured=structured,
            observed_at=datetime.now(UTC),
        )
    else:
        screenshot_ref = await _run_screenshot_via_ssm(instance_id, region)
        return ObservationEnvelope(
            device_id=str(getattr(device, "id", "")),
            screen_version=getattr(device, "screen_version", 0),
            tier="screenshot",
            screenshot_ref=screenshot_ref,
            observed_at=datetime.now(UTC),
        )


async def _run_ax_via_ssm(instance_id: str, region: str) -> dict:
    """Run windows_ax.py on instance via SSM and parse JSON output."""
    import boto3, json, time
    ssm = boto3.client("ssm", region_name=region)
    resp = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunPowerShellScript",
        Parameters={"commands": ["python C:\\devicelab\\windows_ax.py"]},
    )
    command_id = resp["Command"]["CommandId"]
    for _ in range(30):
        time.sleep(1)
        output = ssm.get_command_invocation(CommandId=command_id, InstanceId=instance_id)
        if output["Status"] in ("Success", "Failed"):
            try:
                return json.loads(output.get("StandardOutputContent", "{}"))
            except Exception:
                return {"nodes": [], "error": output.get("StandardOutputContent", "")}
    return {"nodes": [], "error": "SSM command timed out"}


async def _run_screenshot_via_ssm(instance_id: str, region: str) -> str:
    import boto3, base64, time
    ssm = boto3.client("ssm", region_name=region)
    cmd = (
        "$img = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds; "
        "$bmp = New-Object System.Drawing.Bitmap $img.Width,$img.Height; "
        "$g = [System.Drawing.Graphics]::FromImage($bmp); "
        "$g.CopyFromScreen(0,0,0,0,$bmp.Size); "
        "$ms = New-Object System.IO.MemoryStream; "
        "$bmp.Save($ms,'Png'); "
        "[Convert]::ToBase64String($ms.ToArray())"
    )
    resp = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunPowerShellScript",
        Parameters={"commands": [cmd]},
    )
    command_id = resp["Command"]["CommandId"]
    for _ in range(30):
        time.sleep(1)
        output = ssm.get_command_invocation(CommandId=command_id, InstanceId=instance_id)
        if output["Status"] == "Success":
            return output.get("StandardOutputContent", "").strip()
    return ""
