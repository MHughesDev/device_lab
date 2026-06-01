# adapters/macos/stream_local.py — macOS MediaSource via SCK+VideoToolbox (Phase 09, task 09-12)
"""
Captures the macOS VM display via ScreenCaptureKit and encodes with VideoToolbox
(hardware H.264) through the vz sidecar process. The sidecar streams encoded
AUs over a local TCP callback port back to this MediaSource.

This path is Apple-gated (Apple Silicon only). On non-Apple hosts the factory
falls back to NullMediaSource and logs a warning.

Architecture:
  Python MediaSource → sidecar start_capture(vm_id, callback_port)
  → sidecar: SCK → VideoToolbox (vtenc_h264) → TCP → push_au(EncodedVideoTrack)
"""
from __future__ import annotations

import asyncio
import json
import logging

from app.stream.source import MediaSource

log = logging.getLogger(__name__)

_CALLBACK_PORT_RANGE = range(27200, 27300)
_DEFAULT_FPS = 30


class MacosLocalMediaSource(MediaSource):
    """MediaSource for local macOS VMs via ScreenCaptureKit + VideoToolbox."""

    def __init__(self, device: object) -> None:
        self._device = device
        ids: dict = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
        self._vm_id: str = ids.get("vm_id", "")
        self._sidecar_socket: str = ids.get("sidecar_socket", "")
        self._callback_port: int = 0
        self._video_track = None
        self._server: asyncio.AbstractServer | None = None
        self._reader_task: asyncio.Task | None = None
        self._sidecar_client = None
        self._started = False

    async def start(self) -> None:
        if self._started:
            return
        from app.stream.encoded_track import EncodedVideoTrack
        self._video_track = EncodedVideoTrack(
            keyframe_cb=self.request_keyframe, fps=_DEFAULT_FPS
        )

        if not self._vm_id or not self._sidecar_socket:
            log.warning("MacosLocalMediaSource: no vm_id/sidecar_socket — blank stream")
            self._started = True
            return

        # Bind a local TCP port for the sidecar to push encoded AUs into
        self._callback_port = await _find_free_port(_CALLBACK_PORT_RANGE)
        self._server = await asyncio.start_server(
            self._handle_sidecar_connection, "127.0.0.1", self._callback_port
        )

        # Tell the sidecar to start capturing and streaming to us
        try:
            from app.adapters.macos.vz_provision import VzSidecarClient
            self._sidecar_client = VzSidecarClient(self._sidecar_socket)
            await self._sidecar_client.connect()
            await self._sidecar_client.start_capture(self._vm_id, self._callback_port)
        except Exception as exc:
            log.warning("Cannot start vz sidecar capture: %s — blank stream", exc)

        self._started = True
        log.info("macOS SCK MediaSource started (vm=%s, port=%d)", self._vm_id, self._callback_port)

    async def _handle_sidecar_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Receive H.264 AUs from sidecar and push into the encoded track."""
        try:
            import struct
            while True:
                # Frame format from sidecar: length(4) + au(N)
                header = await reader.readexactly(4)
                length = struct.unpack(">I", header)[0]
                if length == 0:
                    continue
                data = await reader.readexactly(length)
                if self._video_track:
                    await self._video_track.push_au(data)
        except (asyncio.IncompleteReadError, asyncio.CancelledError):
            pass
        except Exception as exc:
            log.debug("macOS sidecar connection error: %s", exc)
        finally:
            writer.close()

    def track(self):
        return self._video_track

    async def audio_track(self):
        return None  # vz CoreAudio → Opus wired in Phase 09-16

    async def set_bitrate(self, bps: int) -> None:
        pass  # VideoToolbox bitrate is set at capture start; dynamic change is future work

    async def request_keyframe(self) -> None:
        pass  # sidecar KeyframeRequest future work

    async def stop(self) -> None:
        self._started = False
        if self._sidecar_client and self._vm_id:
            try:
                await self._sidecar_client.stop_capture(self._vm_id)
                await self._sidecar_client.close()
            except Exception:
                pass
        if self._server:
            self._server.close()
        log.info("macOS SCK MediaSource stopped")


async def _find_free_port(port_range: range) -> int:
    import socket
    for port in port_range:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise OSError("No free port in range for vz sidecar callback")
