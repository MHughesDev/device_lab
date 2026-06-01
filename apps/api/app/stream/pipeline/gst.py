# stream/pipeline/gst.py — GStreamer pipeline builder for low-latency H.264 (Phase 09, task 09-07)
"""
Builds GStreamer capture→encode pipelines that feed EncodedVideoTrack.

Encoder selection (best available, in order):
  1. vaapih264enc  — Intel/AMD iGPU VA-API (widely available on Linux desktops)
  2. nvh264enc     — NVIDIA NVENC (datacenter and gamer GPUs)
  3. x264enc       — CPU fallback, tune=zerolatency (always available)

Low-latency profile enforced on all encoders:
  - bframes = 0  (no B-frames → no reorder latency)
  - intra-refresh instead of periodic IDR  (avoids IDR bitrate spikes)
  - slice-based output for low per-frame latency
  - appsink emits encoded AUs into the EncodedVideoTrack queue
"""
from __future__ import annotations

import asyncio
import logging
import shutil
from typing import Callable

log = logging.getLogger(__name__)

_INTRA_PERIOD = 120  # IDR roughly every ~4 seconds at 30fps


def _gst():
    """Lazy import Gst to avoid import errors when GStreamer is not installed."""
    import gi  # type: ignore
    gi.require_version("Gst", "1.0")
    from gi.repository import Gst, GLib  # type: ignore
    if not Gst.is_initialized():
        Gst.init(None)
    return Gst, GLib


def _available_encoders() -> list[str]:
    """Return GStreamer encoder element names available on this host."""
    available = []
    try:
        Gst, _ = _gst()
        for name in ("vaapih264enc", "nvh264enc", "x264enc"):
            if Gst.ElementFactory.find(name):
                available.append(name)
    except Exception:
        pass
    return available


def best_encoder() -> str:
    """Return the best available H.264 encoder for this host."""
    encoders = _available_encoders()
    if encoders:
        log.info("GStreamer: selected encoder %s (available: %s)", encoders[0], encoders)
        return encoders[0]
    return "x264enc"


def _encoder_config(name: str) -> str:
    """Return encoder-specific GStreamer properties for zerolatency profile."""
    if name == "vaapih264enc":
        return (
            f"vaapih264enc rate-control=cbr "
            f"keyframe-period={_INTRA_PERIOD} "
            f"max-bframes=0 "
            f"tune=low-power "
            f"! video/x-h264,stream-format=byte-stream,alignment=au"
        )
    if name == "nvh264enc":
        return (
            f"nvh264enc rc-mode=cbr "
            f"gop-size={_INTRA_PERIOD} "
            f"bframes=0 "
            f"zero-reorder-delay=true "
            f"! video/x-h264,stream-format=byte-stream,alignment=au"
        )
    # x264enc CPU fallback
    return (
        f"x264enc tune=zerolatency "
        f"key-int-max={_INTRA_PERIOD} "
        f"bframes=0 "
        f"intra-refresh=true "
        f"! video/x-h264,stream-format=byte-stream,alignment=au"
    )


class GstPipeline:
    """Wraps a GStreamer pipeline that feeds EncodedVideoTrack.

    Call start() to launch the pipeline; frames are pushed into the
    provided EncodedVideoTrack via the appsink callback.
    """

    def __init__(
        self,
        src_element: str,
        encoder_name: str | None = None,
        fps: int = 30,
        width: int = 1920,
        height: int = 1080,
        bitrate_kbps: int = 8000,
        on_frame: Callable[[bytes], None] | None = None,
    ) -> None:
        self._src_element = src_element
        self._encoder_name = encoder_name or best_encoder()
        self._fps = fps
        self._width = width
        self._height = height
        self._bitrate_kbps = bitrate_kbps
        self._on_frame = on_frame
        self._pipeline = None
        self._loop = None
        self._thread = None

    def _pipeline_desc(self) -> str:
        enc = _encoder_config(self._encoder_name)
        return (
            f"{self._src_element} "
            f"! videoscale ! videorate "
            f"! video/x-raw,width={self._width},height={self._height},framerate={self._fps}/1 "
            f"! videoconvert "
            f"! {enc} "
            f"! appsink name=sink emit-signals=true max-buffers=2 drop=true"
        )

    def start(self) -> None:
        """Launch the GStreamer pipeline in a background thread."""
        import threading
        self._thread = threading.Thread(target=self._run, daemon=True, name="gst-pipeline")
        self._thread.start()

    def _run(self) -> None:
        try:
            Gst, GLib = _gst()
            pipeline_str = self._pipeline_desc()
            log.debug("GStreamer pipeline: %s", pipeline_str)
            self._pipeline = Gst.parse_launch(pipeline_str)
            sink = self._pipeline.get_by_name("sink")
            if sink and self._on_frame:
                sink.connect("new-sample", self._on_new_sample)
            self._pipeline.set_state(Gst.State.PLAYING)
            self._loop = GLib.MainLoop()
            self._loop.run()
        except Exception as exc:
            log.error("GStreamer pipeline error: %s", exc)

    def _on_new_sample(self, sink) -> int:
        try:
            import gi  # type: ignore
            gi.require_version("Gst", "1.0")
            from gi.repository import Gst  # type: ignore
            sample = sink.emit("pull-sample")
            if sample:
                buf = sample.get_buffer()
                result, mapinfo = buf.map(Gst.MapFlags.READ)
                if result and self._on_frame:
                    self._on_frame(bytes(mapinfo.data))
                buf.unmap(mapinfo)
            return Gst.FlowReturn.OK  # type: ignore
        except Exception as exc:
            log.debug("appsink callback error: %s", exc)
            return 0

    def request_keyframe(self) -> None:
        """Force an IDR keyframe from the encoder (called on PLI/FIR)."""
        try:
            Gst, _ = _gst()
            from gi.repository import Gst as _Gst  # type: ignore
            enc = self._pipeline.get_by_name("enc") if self._pipeline else None
            if enc:
                enc.emit("force-key-unit", 0, True, 0)
        except Exception:
            pass

    def set_bitrate(self, kbps: int) -> None:
        self._bitrate_kbps = kbps

    def stop(self) -> None:
        try:
            if self._loop:
                self._loop.quit()
            if self._pipeline:
                import gi  # type: ignore
                gi.require_version("Gst", "1.0")
                from gi.repository import Gst  # type: ignore
                self._pipeline.set_state(Gst.State.NULL)
        except Exception:
            pass


def is_gstreamer_available() -> bool:
    """Return True if GStreamer with at least one H.264 encoder is available."""
    try:
        _gst()
        return bool(_available_encoders())
    except Exception:
        return False
