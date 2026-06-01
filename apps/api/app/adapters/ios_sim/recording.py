# recording.py — iOS Simulator screen recording via xcrun simctl io recordVideo over SSMChannel
from __future__ import annotations
import json

from app.transport.channel import ChannelFactory


async def start(device: object, recording_id: str) -> str:
    """Start xcrun simctl recordVideo via SSMChannel. Returns remote PID."""
    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    sim_udid = ids.get("sim_udid", "")

    out_path = f"/tmp/devicelab-rec-{recording_id}.mp4"
    log_path = f"/tmp/devicelab-rec-{recording_id}.log"
    cmd = (
        f"xcrun simctl io {sim_udid} recordVideo {out_path} "
        f">{log_path} 2>&1 & echo $!"
    )
    channel = ChannelFactory.get(device)
    result = await channel.exec(cmd)
    return result.stdout.strip()


async def stop(device: object, session: object) -> str:
    """SIGINT the recordVideo process, optionally upload to S3."""
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
