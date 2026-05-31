# observation.py — macOS AX observation via macos_ax.py + SSM RunCommand
from __future__ import annotations
import json
from datetime import UTC, datetime

from app.adapters.spi import CapabilityUnsupportedError
from app.models import ObservationEnvelope

_SUPPORTED_TIERS = {"ax_tree", "screenshot"}


async def observe_macos(device: object, tier: str) -> ObservationEnvelope:
    """
    tier='ax': run macos_ax.py on device via SSM, parse JSON into ObservationEnvelope.
    tier='screenshot': screencapture -t png via SSM RunCommand.
    """
    if tier not in _SUPPORTED_TIERS:
        raise CapabilityUnsupportedError(tier, "macos")

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
    import boto3, time
    ssm = boto3.client("ssm", region_name=region)
    resp = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": ["python3 /opt/devicelab/macos_ax.py"]},
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
    resp = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": [
            "screencapture -t png /tmp/dl_screenshot.png && base64 /tmp/dl_screenshot.png"
        ]},
    )
    command_id = resp["Command"]["CommandId"]
    for _ in range(30):
        time.sleep(1)
        output = ssm.get_command_invocation(CommandId=command_id, InstanceId=instance_id)
        if output["Status"] == "Success":
            return output.get("StandardOutputContent", "").strip()
    return ""
