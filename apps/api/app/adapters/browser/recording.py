# recording.py — Browser screen recording via MediaRecorder API injected into the page
from __future__ import annotations
import os
import tempfile


async def start(device: object, recording_id: str) -> str:
    """Inject MediaRecorder into the page to capture a WebM stream."""
    from app.adapters.browser.adapter import BrowserAdapter

    device_id = str(device.id)  # type: ignore[attr-defined]
    adapter_session = BrowserAdapter().get_session(device_id)
    if not adapter_session:
        raise ValueError(f"No active browser session for device {device_id}")

    page = adapter_session._page  # type: ignore[attr-defined]
    # Inject MediaRecorder; chunks are stored in window._dlRecChunks
    await page.evaluate("""() => {
        window._dlRecChunks = [];
        const stream = await navigator.mediaDevices.getDisplayMedia({
            video: { mediaSource: 'screen' }, audio: false
        }).catch(() => null);
        if (!stream) return;
        window._dlRecorder = new MediaRecorder(stream, { mimeType: 'video/webm;codecs=vp9' });
        window._dlRecorder.ondataavailable = e => { if (e.data.size > 0) window._dlRecChunks.push(e.data); };
        window._dlRecorder.start(1000);
    }""")
    return f"browser:{device_id}"


async def stop(device: object, session: object) -> str:
    """Stop MediaRecorder, collect chunks, save to disk (or S3)."""
    from app.adapters.browser.adapter import BrowserAdapter
    from app.core.config import settings

    device_id = str(device.id)  # type: ignore[attr-defined]
    recording_id = session.recording_id  # type: ignore[attr-defined]
    adapter_session = BrowserAdapter().get_session(device_id)
    if not adapter_session:
        return ""

    page = adapter_session._page  # type: ignore[attr-defined]
    raw_bytes: bytes = await page.evaluate("""async () => {
        if (!window._dlRecorder) return null;
        window._dlRecorder.stop();
        await new Promise(r => setTimeout(r, 500));
        const blob = new Blob(window._dlRecChunks, { type: 'video/webm' });
        const buf = await blob.arrayBuffer();
        return Array.from(new Uint8Array(buf));
    }""")

    if not raw_bytes:
        return ""

    local_path = os.path.join(tempfile.gettempdir(), f"devicelab-rec-{recording_id}.webm")
    with open(local_path, "wb") as fh:
        fh.write(bytes(raw_bytes))

    bucket = getattr(settings, "ARTIFACT_BUCKET", None)
    if bucket:
        import boto3
        s3_key = f"recordings/{recording_id}.webm"
        boto3.client("s3").upload_file(local_path, bucket, s3_key)
        os.unlink(local_path)
        return f"s3://{bucket}/{s3_key}"

    return f"local:{local_path}"
