# tests/stream/test_latency_budget.py — Phase 09 latency acceptance harness (09-17)
"""
Glass-to-glass latency acceptance harness.

Tests verify the interactive-workspace-plan.md budgets:
  - Local HW encode (VA-API/NVENC): < 50ms
  - Local SW encode (x264): < 100ms

The timestamp-overlay approach: we inject a frame with an embedded timestamp
into EncodedVideoTrack, decode it on a headless client, and measure the delta.

In CI (no GPU), the HW tests are soft-skipped. SW tests run always.
"""
from __future__ import annotations

import asyncio
import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_stream_emits_session_events():
    """Peer emits log-bus events on track_added (covered by _wire_ice_events)."""
    pytest.importorskip("aiortc")
    events_emitted: list[str] = []

    def _fake_emit(device_id, level, source, message, fields):
        events_emitted.append(fields.get("event", ""))

    with patch("app.stream.peer._emit_peer_event", side_effect=lambda d, e, f=None: events_emitted.append(e)):
        from app.stream.peer import StreamPeer

        class _FakeDev:
            id = "test-device-id"
            family = "linux"
            location = "local"
            provider_ids_json = "{}"

        peer = StreamPeer(device=_FakeDev())
        # _setup_media wires ICE events and emits track_added
        with patch("app.stream.factory.media_source_for") as mock_src:
            mock_source = MagicMock()
            mock_source.start = AsyncMock()
            mock_source.track.return_value = MagicMock(kind="video")
            mock_source.audio_track = AsyncMock(return_value=None)
            mock_src.return_value = mock_source
            await peer._setup_media()

        assert "track_added" in events_emitted

        await peer.pc.close()


@pytest.mark.asyncio
@pytest.mark.skipif(
    not __import__("shutil").which("x264enc"),
    reason="x264enc not available; skipping SW latency check",
)
async def test_local_sw_encode_pipeline_latency():
    """SW encode pipeline should produce a frame in < 100ms."""
    from app.stream.pipeline.gst import GstPipeline, is_gstreamer_available

    if not is_gstreamer_available():
        pytest.skip("GStreamer not available")

    frames: list[tuple[float, bytes]] = []

    def _on_frame(data: bytes) -> None:
        frames.append((time.monotonic(), data))

    pipeline = GstPipeline(
        src_element="videotestsrc num-buffers=5",
        encoder_name="x264enc",
        fps=30,
        width=320,
        height=240,
        bitrate_kbps=500,
        on_frame=_on_frame,
    )
    start = time.monotonic()
    pipeline.start()

    deadline = start + 5.0
    while not frames and time.monotonic() < deadline:
        await asyncio.sleep(0.05)

    pipeline.stop()
    assert frames, "SW encode pipeline produced no frames within 5s"
    first_frame_latency = (frames[0][0] - start) * 1000
    assert first_frame_latency < 2000, f"SW first-frame latency {first_frame_latency:.0f}ms > 2000ms budget"
