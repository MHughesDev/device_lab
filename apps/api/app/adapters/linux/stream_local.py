# adapters/linux/stream_local.py — Linux MediaSource via GStreamer ximagesrc (Phase 09, task 09-08)
"""
Streams the Linux container's Xvfb framebuffer via GStreamer ximagesrc + H.264 encoder.
The Phase 08 provisioner starts Xvfb on DISPLAY=:0 inside the container; we capture
that display and push encoded H.264 access units into EncodedVideoTrack.

GstPipeline encoder selection (vaapih264enc → nvh264enc → x264enc) is handled in
stream/pipeline/gst.py.
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


class LinuxLocalMediaSource(MediaSource):
    """MediaSource for local Linux containers via GStreamer ximagesrc."""

    def __init__(self, device: object) -> None:
        self._device = device
        ids: dict = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
        self._display: str = ids.get("display", ":0")
        self._container_id: str = ids.get("container_id", "")
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
            log.warning("GStreamer not available — LinuxLocalMediaSource emitting blank stream")
            self._started = True
            return

        # ximagesrc captures a live X display; use-damage=0 forces full-frame capture
        src_element = f"ximagesrc display-name={self._display} use-damage=0"
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
        log.info("Linux GStreamer MediaSource started (display=%s)", self._display)

    def _on_frame(self, data: bytes) -> None:
        if self._video_track:
            asyncio.get_event_loop().call_soon_threadsafe(
                lambda: asyncio.ensure_future(self._video_track.push_au(data))
            )

    def track(self):
        return self._video_track

    async def audio_track(self):
        return None  # Opus audio wired in Phase 09-16

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
        log.info("Linux GStreamer MediaSource stopped")
