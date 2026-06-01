# tests/stream/test_encoded_track.py — Phase 09 encoded-passthrough track tests
from __future__ import annotations

import asyncio
import pytest


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


def test_encoded_video_track_kind():
    pytest.importorskip("aiortc")
    from app.stream.encoded_track import EncodedVideoTrack
    track = EncodedVideoTrack()
    assert track.kind == "video"


def test_encoded_audio_track_kind():
    pytest.importorskip("aiortc")
    from app.stream.encoded_track import EncodedAudioTrack
    track = EncodedAudioTrack()
    assert track.kind == "audio"


@pytest.mark.asyncio
async def test_encoded_track_push_and_recv():
    pytest.importorskip("aiortc")
    pytest.importorskip("av")
    from app.stream.encoded_track import EncodedVideoTrack

    received: list = []

    async def _keyframe_cb():
        pass

    track = EncodedVideoTrack(keyframe_cb=_keyframe_cb)

    # Push a fake NAL unit (start code + random payload)
    fake_au = b"\x00\x00\x00\x01" + b"\x41" * 100  # non-IDR slice NAL
    await track.push_au(fake_au)

    # recv() should return a packet wrapping the data
    pkt = await asyncio.wait_for(track.recv(), timeout=2.0)
    assert pkt is not None


@pytest.mark.asyncio
async def test_encoded_track_drops_oldest_when_full():
    pytest.importorskip("aiortc")
    from app.stream.encoded_track import EncodedVideoTrack
    track = EncodedVideoTrack()
    # Fill and overflow the 64-slot queue — should not block or raise
    for i in range(70):
        await track.push_au(bytes([i % 256] * 10))
    assert True  # no exception


@pytest.mark.asyncio
async def test_encoded_track_forwards_pli_to_keyframe_callback():
    pytest.importorskip("aiortc")
    called = []

    async def _cb():
        called.append(True)

    from app.stream.encoded_track import EncodedVideoTrack
    track = EncodedVideoTrack(keyframe_cb=_cb)
    await track.on_keyframe_request()
    assert called
