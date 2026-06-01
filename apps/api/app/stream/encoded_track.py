# encoded_track.py — aiortc H.264 encoded-passthrough track (Phase 09, task 09-02)
"""
Feed pre-encoded H.264 access units from scrcpy / MediaCodec / GStreamer appsink /
VideoToolbox directly into an aiortc RTP sender — no re-encoding.

Architecture: we subclass MediaStreamTrack (kind="video") and override recv() to
return an av.Packet wrapping the raw H.264 NAL unit. aiortc's H264Encoder path
normally re-encodes VideoFrame → we bypass that by registering as a "codec-specific"
track so the RTP packetizer receives our pre-encoded AUs directly.

PLI / FIR / keyframe requests are forwarded back to the MediaSource so the encoder
(device-side for scrcpy, GStreamer for Linux/Windows) can emit a fresh IDR.

If this approach proves infeasible the ADR (adr-0004-streaming-media-pipeline.md)
records the fallback to GStreamer webrtcbin for the media path only.
"""
from __future__ import annotations

import asyncio
import fractions
import logging
from collections import deque
from collections.abc import Callable

from aiortc.mediastreams import MediaStreamTrack  # type: ignore

log = logging.getLogger(__name__)

# RTP clock rate for H.264
_H264_CLOCK = 90000
_DEFAULT_FPS = 30


class EncodedVideoTrack(MediaStreamTrack):
    """MediaStreamTrack that emits pre-encoded H.264 access units.

    Usage:
        track = EncodedVideoTrack(keyframe_cb=source.request_keyframe)
        peer.addTrack(track)
        # from encoder thread/task:
        await track.push_au(h264_bytes, pts_90khz)
    """

    kind = "video"

    def __init__(self, keyframe_cb: Callable | None = None, fps: int = _DEFAULT_FPS) -> None:
        super().__init__()
        self._keyframe_cb = keyframe_cb
        self._fps = fps
        self._clock = _H264_CLOCK
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=64)
        self._pts: int = 0
        self._time_base = fractions.Fraction(1, self._clock)

    async def push_au(self, data: bytes, pts: int | None = None) -> None:
        """Push a pre-encoded H.264 access unit (one frame / AU).

        pts is in 90 kHz clock ticks. If None, auto-increments at _fps.
        Non-blocking: drops the oldest frame if the queue is full (low-latency policy).
        """
        if pts is None:
            self._pts += int(self._clock / self._fps)
            pts = self._pts
        try:
            self._queue.put_nowait((data, pts))
        except asyncio.QueueFull:
            try:
                self._queue.get_nowait()
                self._queue.put_nowait((data, pts))
            except (asyncio.QueueEmpty, asyncio.QueueFull):
                pass

    async def recv(self):
        """Called by aiortc's RTP layer to get the next packet."""
        import av  # type: ignore
        data, pts = await self._queue.get()
        packet = av.Packet(data)
        packet.pts = pts
        packet.dts = pts
        packet.time_base = self._time_base
        return packet

    async def on_keyframe_request(self) -> None:
        """Called when a PLI/FIR is received from the remote peer."""
        if self._keyframe_cb is not None:
            try:
                if asyncio.iscoroutinefunction(self._keyframe_cb):
                    await self._keyframe_cb()
                else:
                    self._keyframe_cb()
            except Exception as exc:
                log.warning("Keyframe request callback failed: %s", exc)


class EncodedAudioTrack(MediaStreamTrack):
    """MediaStreamTrack that emits pre-encoded Opus frames.

    Usage:
        track = EncodedAudioTrack()
        peer.addTrack(track)
        await track.push_frame(opus_bytes)
    """

    kind = "audio"
    _SAMPLE_RATE = 48000
    _FRAME_SAMPLES = 960  # 20ms at 48 kHz

    def __init__(self) -> None:
        super().__init__()
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=64)
        self._pts: int = 0
        self._time_base = fractions.Fraction(1, self._SAMPLE_RATE)

    async def push_frame(self, data: bytes) -> None:
        self._pts += self._FRAME_SAMPLES
        try:
            self._queue.put_nowait((data, self._pts))
        except asyncio.QueueFull:
            try:
                self._queue.get_nowait()
                self._queue.put_nowait((data, self._pts))
            except (asyncio.QueueEmpty, asyncio.QueueFull):
                pass

    async def recv(self):
        import av  # type: ignore
        data, pts = await self._queue.get()
        frame = av.AudioFrame(format="s16", layout="stereo")
        frame.pts = pts
        frame.time_base = self._time_base
        packet = av.Packet(data)
        packet.pts = pts
        packet.dts = pts
        packet.time_base = self._time_base
        return packet
