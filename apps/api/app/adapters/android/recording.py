# recording.py — Android screen recording via adb screenrecord
# Note: Android's screenrecord has a 3-minute hard limit per file.
from __future__ import annotations
import json
import subprocess


async def start(device: object, recording_id: str) -> str:
    """Start adb screenrecord on the emulator. Returns the background process handle."""
    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    adb_serial = ids.get("adb_serial", "emulator-5554")
    remote_path = f"/sdcard/devicelab-rec-{recording_id}.mp4"

    # --time-limit 180 = Android's max per-file; agent can chain if needed
    proc = subprocess.Popen(
        ["adb", "-s", adb_serial, "shell", "screenrecord", "--time-limit", "180", remote_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # Return "pid:remote_path" so stop() knows both
    return f"{proc.pid}:{remote_path}"


async def stop(device: object, session: object) -> str:
    """Signal screenrecord to stop, pull the file, return local path."""
    import os
    import tempfile
    from app.core.config import settings

    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    adb_serial = ids.get("adb_serial", "emulator-5554")
    recording_id = session.recording_id  # type: ignore[attr-defined]
    handle = session.remote_handle or ""  # type: ignore[attr-defined]

    pid_str, _, remote_path = handle.partition(":")
    if not remote_path:
        remote_path = f"/sdcard/devicelab-rec-{recording_id}.mp4"

    # SIGINT causes screenrecord to finalize and close the file gracefully
    subprocess.run(
        ["adb", "-s", adb_serial, "shell", "kill", "-SIGINT", f"$(pidof screenrecord)"],
        capture_output=True,
    )

    import time
    time.sleep(2)

    bucket = getattr(settings, "ARTIFACT_BUCKET", None)
    local_path = os.path.join(tempfile.gettempdir(), f"devicelab-rec-{recording_id}.mp4")
    subprocess.run(["adb", "-s", adb_serial, "pull", remote_path, local_path], capture_output=True)
    subprocess.run(["adb", "-s", adb_serial, "shell", "rm", "-f", remote_path], capture_output=True)

    if bucket:
        import boto3
        s3_key = f"recordings/{recording_id}.mp4"
        boto3.client("s3").upload_file(local_path, bucket, s3_key)
        os.unlink(local_path)
        return f"s3://{bucket}/{s3_key}"

    return f"local:{local_path}"
