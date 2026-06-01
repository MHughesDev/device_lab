# recording.py — Windows screen recording via ffmpeg gdigrab over SSM PowerShell
from __future__ import annotations
import json


async def start(device: object, recording_id: str) -> str:
    """Launch ffmpeg gdigrab via SSM PowerShell. Returns remote PID as string."""
    import boto3
    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    instance_id = ids.get("instance_id", "")
    region = ids.get("region", "us-east-1")

    out_path = f"C:\\Windows\\Temp\\devicelab-rec-{recording_id}.mp4"
    # Start-Process returns PID; -WindowStyle Hidden prevents a console window
    ps_cmd = (
        f"$p = Start-Process -FilePath ffmpeg "
        f"-ArgumentList '-f','gdigrab','-framerate','25','-i','desktop',"
        f"'-codec:v','libx264','-preset','ultrafast','{out_path}' "
        f"-WindowStyle Hidden -PassThru; $p.Id"
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


async def stop(device: object, session: object) -> str:
    """Stop ffmpeg via Stop-Process, optionally upload to S3."""
    import boto3
    from app.core.config import settings

    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    instance_id = ids.get("instance_id", "")
    region = ids.get("region", "us-east-1")
    recording_id = session.recording_id  # type: ignore[attr-defined]
    pid = session.remote_handle  # type: ignore[attr-defined]
    out_path = f"C:\\Windows\\Temp\\devicelab-rec-{recording_id}.mp4"

    ssm = boto3.client("ssm", region_name=region)
    stop_cmd = f"Stop-Process -Id {pid} -ErrorAction SilentlyContinue; Start-Sleep 2"
    ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunPowerShellScript",
        Parameters={"commands": [stop_cmd]},
    )

    bucket = getattr(settings, "ARTIFACT_BUCKET", None)
    if bucket:
        s3_key = f"recordings/{recording_id}.mp4"
        upload_cmd = (
            f"aws s3 cp \"{out_path}\" s3://{bucket}/{s3_key}; "
            f"Remove-Item \"{out_path}\" -ErrorAction SilentlyContinue"
        )
        ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunPowerShellScript",
            Parameters={"commands": [upload_cmd]},
        )
        return f"s3://{bucket}/{s3_key}"

    return f"local:{out_path}@{instance_id}"
