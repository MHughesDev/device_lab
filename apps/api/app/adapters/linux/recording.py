# recording.py — Linux screen recording via ffmpeg x11grab over SSM
from __future__ import annotations
import json


async def start(device: object, recording_id: str) -> str:
    """Launch ffmpeg x11grab on the EC2 instance via SSM. Returns the remote PID."""
    import boto3
    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    instance_id = ids.get("instance_id", "")
    region = ids.get("region", "us-east-1")

    out_path = f"/tmp/devicelab-rec-{recording_id}.mp4"
    log_path = f"/tmp/devicelab-rec-{recording_id}.log"
    cmd = (
        f"DISPLAY=:0 ffmpeg -f x11grab -r 25 "
        f"-s $(xdpyinfo | awk '/dimensions/{{print $2}}') "
        f"-i :0.0 -codec:v libx264 -preset ultrafast {out_path} "
        f">{log_path} 2>&1 & echo $!"
    )

    ssm = boto3.client("ssm", region_name=region)
    resp = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": [cmd]},
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
    """Kill ffmpeg, pull the file to S3 (or return local path if no bucket configured)."""
    import boto3
    from app.core.config import settings

    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    instance_id = ids.get("instance_id", "")
    region = ids.get("region", "us-east-1")
    recording_id = session.recording_id  # type: ignore[attr-defined]
    pid = session.remote_handle  # type: ignore[attr-defined]
    out_path = f"/tmp/devicelab-rec-{recording_id}.mp4"

    ssm = boto3.client("ssm", region_name=region)
    kill_cmd = f"kill -SIGINT {pid} 2>/dev/null; sleep 2; test -f {out_path} && echo ok || echo missing"
    ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": [kill_cmd]},
    )

    bucket = getattr(settings, "ARTIFACT_BUCKET", None)
    if bucket:
        s3_key = f"recordings/{recording_id}.mp4"
        upload_cmd = f"aws s3 cp {out_path} s3://{bucket}/{s3_key} --region {region} && rm -f {out_path}"
        ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={"commands": [upload_cmd]},
        )
        return f"s3://{bucket}/{s3_key}"

    return f"local:{out_path}@{instance_id}"
