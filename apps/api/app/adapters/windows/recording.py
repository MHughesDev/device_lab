# recording.py — Windows screen recording via ffmpeg gdigrab over SSMChannel (PowerShell)
from __future__ import annotations
import json

from app.transport.channel import ChannelFactory


async def start(device: object, recording_id: str) -> str:
    """Launch ffmpeg gdigrab via SSMChannel. Returns remote PID as string."""
    out_path = f"C:\\Windows\\Temp\\devicelab-rec-{recording_id}.mp4"
    # Start-Process returns PID; -WindowStyle Hidden prevents a console window
    ps_cmd = (
        f"$p = Start-Process -FilePath ffmpeg "
        f"-ArgumentList '-f','gdigrab','-framerate','25','-i','desktop',"
        f"'-codec:v','libx264','-preset','ultrafast','{out_path}' "
        f"-WindowStyle Hidden -PassThru; $p.Id"
    )
    channel = ChannelFactory.get(device)
    result = await channel.exec(ps_cmd)
    return result.stdout.strip()


async def stop(device: object, session: object) -> str:
    """Stop ffmpeg via Stop-Process, optionally upload to S3."""
    from app.core.config import settings

    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    recording_id = session.recording_id  # type: ignore[attr-defined]
    pid = session.remote_handle  # type: ignore[attr-defined]
    out_path = f"C:\\Windows\\Temp\\devicelab-rec-{recording_id}.mp4"

    channel = ChannelFactory.get(device)
    await channel.exec(f"Stop-Process -Id {pid} -ErrorAction SilentlyContinue; Start-Sleep 2")

    bucket = getattr(settings, "ARTIFACT_BUCKET", None)
    if bucket:
        s3_key = f"recordings/{recording_id}.mp4"
        await channel.exec(
            f"aws s3 cp \"{out_path}\" s3://{bucket}/{s3_key}; "
            f"Remove-Item \"{out_path}\" -ErrorAction SilentlyContinue"
        )
        return f"s3://{bucket}/{s3_key}"

    return f"local:{out_path}@{ids.get('instance_id', '')}"
