# recording.py — Linux screen recording via ffmpeg x11grab over SSMChannel
from __future__ import annotations
import json

from app.transport.channel import ChannelFactory


async def start(device: object, recording_id: str) -> str:
    """Launch ffmpeg x11grab on the EC2 instance via SSMChannel. Returns the remote PID."""
    out_path = f"/tmp/devicelab-rec-{recording_id}.mp4"
    log_path = f"/tmp/devicelab-rec-{recording_id}.log"
    cmd = (
        f"DISPLAY=:0 ffmpeg -f x11grab -r 25 "
        f"-s $(xdpyinfo | awk '/dimensions/{{print $2}}') "
        f"-i :0.0 -codec:v libx264 -preset ultrafast {out_path} "
        f">{log_path} 2>&1 & echo $!"
    )
    channel = ChannelFactory.get(device)
    result = await channel.exec(cmd)
    return result.stdout.strip()


async def stop(device: object, session: object) -> str:
    """Kill ffmpeg, pull the file to S3 (or return local path if no bucket configured)."""
    from app.core.config import settings

    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    region = ids.get("region", "us-east-1")
    recording_id = session.recording_id  # type: ignore[attr-defined]
    pid = session.remote_handle  # type: ignore[attr-defined]
    out_path = f"/tmp/devicelab-rec-{recording_id}.mp4"

    channel = ChannelFactory.get(device)
    await channel.exec(f"kill -SIGINT {pid} 2>/dev/null; sleep 2; test -f {out_path} && echo ok || echo missing")

    bucket = getattr(settings, "ARTIFACT_BUCKET", None)
    if bucket:
        s3_key = f"recordings/{recording_id}.mp4"
        await channel.exec(f"aws s3 cp {out_path} s3://{bucket}/{s3_key} --region {region} && rm -f {out_path}")
        return f"s3://{bucket}/{s3_key}"

    return f"local:{out_path}@{ids.get('instance_id', '')}"
