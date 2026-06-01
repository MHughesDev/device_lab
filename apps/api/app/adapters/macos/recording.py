# recording.py — macOS screen recording via ffmpeg avfoundation over SSMChannel
from __future__ import annotations
import json

from app.transport.channel import ChannelFactory


async def start(device: object, recording_id: str) -> str:
    """Launch ffmpeg avfoundation capture via SSMChannel. Returns remote PID."""
    out_path = f"/tmp/devicelab-rec-{recording_id}.mp4"
    log_path = f"/tmp/devicelab-rec-{recording_id}.log"
    # avfoundation input "1" = first screen; "-capture_cursor 1" for cursor overlay
    cmd = (
        f"ffmpeg -f avfoundation -capture_cursor 1 -i '1' "
        f"-r 25 -codec:v libx264 -preset ultrafast {out_path} "
        f">{log_path} 2>&1 & echo $!"
    )
    channel = ChannelFactory.get(device)
    result = await channel.exec(cmd)
    return result.stdout.strip()


async def stop(device: object, session: object) -> str:
    """Send SIGINT to ffmpeg, optionally upload to S3."""
    from app.core.config import settings

    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    recording_id = session.recording_id  # type: ignore[attr-defined]
    pid = session.remote_handle  # type: ignore[attr-defined]
    out_path = f"/tmp/devicelab-rec-{recording_id}.mp4"

    channel = ChannelFactory.get(device)
    await channel.exec(f"kill -SIGINT {pid} 2>/dev/null; sleep 2")

    bucket = getattr(settings, "ARTIFACT_BUCKET", None)
    if bucket:
        s3_key = f"recordings/{recording_id}.mp4"
        await channel.exec(f"aws s3 cp {out_path} s3://{bucket}/{s3_key} && rm -f {out_path}")
        return f"s3://{bucket}/{s3_key}"

    return f"local:{out_path}@{ids.get('instance_id', '')}"
