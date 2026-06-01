# recording.py — iOS Simulator screen recording via xcrun simctl io recordVideo over SSM
from __future__ import annotations
import json


async def start(device: object, recording_id: str) -> str:
    """Start xcrun simctl recordVideo via SSM. Returns remote PID."""
    import boto3
    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    instance_id = ids.get("instance_id", "")
    sim_udid = ids.get("sim_udid", "")
    region = ids.get("region", "us-east-1")

    out_path = f"/tmp/devicelab-rec-{recording_id}.mp4"
    log_path = f"/tmp/devicelab-rec-{recording_id}.log"
    cmd = (
        f"xcrun simctl io {sim_udid} recordVideo {out_path} "
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
    """SIGINT the recordVideo process, optionally upload to S3."""
    import boto3
    from app.core.config import settings

    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    instance_id = ids.get("instance_id", "")
    region = ids.get("region", "us-east-1")
    recording_id = session.recording_id  # type: ignore[attr-defined]
    pid = session.remote_handle  # type: ignore[attr-defined]
    out_path = f"/tmp/devicelab-rec-{recording_id}.mp4"

    ssm = boto3.client("ssm", region_name=region)
    kill_cmd = f"kill -SIGINT {pid} 2>/dev/null; sleep 2"
    ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": [kill_cmd]},
    )

    bucket = getattr(settings, "ARTIFACT_BUCKET", None)
    if bucket:
        s3_key = f"recordings/{recording_id}.mp4"
        upload_cmd = f"aws s3 cp {out_path} s3://{bucket}/{s3_key} && rm -f {out_path}"
        ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={"commands": [upload_cmd]},
        )
        return f"s3://{bucket}/{s3_key}"

    return f"local:{out_path}@{instance_id}"
