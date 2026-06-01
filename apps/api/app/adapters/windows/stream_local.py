# adapters/windows/stream_local.py — Windows MediaSource via VNC→GStreamer bridge (Phase 09, task 09-09)
"""
Streams a Windows QEMU VM by reading from the VNC framebuffer exposed on
127.0.0.1:<vnc_port>. The Phase 08 provisioner starts QEMU with:
  -display vnc=127.0.0.1:<vnc_port>

We use GStreamer's `rfbsrc` element (from gst-plugins-bad) to connect to the
VNC server and capture frames, then pipe through the standard H.264 encoder
chain (vaapih264enc → nvh264enc → x264enc).

If rfbsrc is unavailable we log a warning and emit a blank stream.
"""
from __future__ import annotations

import asyncio
import json
import logging

from app.stream.source import MediaSource

log = logging.getLogger(__name__)

_DEFAULT_FPS = 30
_DEFAULT_WIDTH = 1920
_DEFAULT_HEIGHT = 1080
_DEFAULT_BITRATE_KBPS = 8000


class WindowsLocalMediaSource(MediaSource):
    """MediaSource for local Windows QEMU VMs via VNC bridge."""

    def __init__(self, device: object) -> None:
        self._device = device
        ids: dict = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
        # vnc_port set by Phase 08 windows provisioner
        self._vnc_port: int = int(ids.get("vnc_port", 5900))
        self._fps = _DEFAULT_FPS
        self._width = _DEFAULT_WIDTH
        self._height = _DEFAULT_HEIGHT
        self._bitrate_kbps = _DEFAULT_BITRATE_KBPS
        self._video_track = None
        self._pipeline = None
        self._started = False

    async def start(self) -> None:
        if self._started:
            return
        from app.stream.encoded_track import EncodedVideoTrack
        from app.stream.pipeline.gst import GstPipeline, is_gstreamer_available

        self._video_track = EncodedVideoTrack(
            keyframe_cb=self.request_keyframe, fps=self._fps
        )

        if not is_gstreamer_available():
            log.warning("GStreamer not available — WindowsLocalMediaSource emitting blank stream")
            self._started = True
            return

        # rfbsrc connects to a VNC server and emits raw video frames
        src_element = (
            f"rfbsrc host=127.0.0.1 port={self._vnc_port} "
            f"shared=true view-only=true"
        )
        self._pipeline = GstPipeline(
            src_element=src_element,
            fps=self._fps,
            width=self._width,
            height=self._height,
            bitrate_kbps=self._bitrate_kbps,
            on_frame=self._on_frame,
        )
        self._pipeline.start()
        self._started = True
        log.info("Windows VNC MediaSource started (vnc_port=%d)", self._vnc_port)

    def _on_frame(self, data: bytes) -> None:
        if self._video_track:
            asyncio.get_event_loop().call_soon_threadsafe(
                lambda: asyncio.ensure_future(self._video_track.push_au(data))
            )

    def track(self):
        return self._video_track

    async def audio_track(self):
        return None  # Audio via QEMU SPICE wired in Phase 09-16

    async def set_bitrate(self, bps: int) -> None:
        self._bitrate_kbps = bps // 1000
        if self._pipeline:
            self._pipeline.set_bitrate(self._bitrate_kbps)

    async def request_keyframe(self) -> None:
        if self._pipeline:
            self._pipeline.request_keyframe()

    async def stop(self) -> None:
        self._started = False
        if self._pipeline:
            self._pipeline.stop()
            self._pipeline = None
        log.info("Windows VNC MediaSource stopped")
