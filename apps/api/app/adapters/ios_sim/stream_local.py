# adapters/ios_sim/stream_local.py — iOS Simulator MediaSource via ScreenCaptureKit (Phase 09, task 09-13)
"""
Captures the iOS Simulator window via ScreenCaptureKit (window filter by bundle ID
"com.apple.iphonesimulator") and encodes with VideoToolbox through the vz sidecar.

Architecture mirrors macOS stream_local.py but uses a Simulator-window filter
instead of a full display capture.

Apple-gated: hard-refused on non-macOS hosts; the factory returns NullMediaSource.
"""
from __future__ import annotations

import asyncio
import json
import logging

from app.stream.source import MediaSource

log = logging.getLogger(__name__)

_DEFAULT_FPS = 30
_CALLBACK_PORT_RANGE = range(27300, 27400)


class IosSimMediaSource(MediaSource):
    """MediaSource for iOS Simulator via ScreenCaptureKit window capture."""

    def __init__(self, device: object) -> None:
        self._device = device
        ids: dict = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
        self._udid: str = ids.get("udid", "")
        self._sidecar_socket: str = ids.get("sidecar_socket", "")
        self._callback_port: int = 0
        self._video_track = None
        self._server: asyncio.AbstractServer | None = None
        self._sidecar_client = None
        self._started = False

    async def start(self) -> None:
        if self._started:
            return
        from app.stream.encoded_track import EncodedVideoTrack
        self._video_track = EncodedVideoTrack(
            keyframe_cb=self.request_keyframe, fps=_DEFAULT_FPS
        )

        if not self._sidecar_socket:
            log.warning("IosSimMediaSource: no sidecar_socket — blank stream")
            self._started = True
            return

        self._callback_port = await _find_free_port(_CALLBACK_PORT_RANGE)
        self._server = await asyncio.start_server(
            self._handle_connection, "127.0.0.1", self._callback_port
        )

        try:
            from app.adapters.macos.vz_provision import VzSidecarClient
            self._sidecar_client = VzSidecarClient(self._sidecar_socket)
            await self._sidecar_client.connect()
            # Use a simulator-specific capture RPC with udid as the vm_id
            await self._sidecar_client.start_capture(self._udid, self._callback_port)
        except Exception as exc:
            log.warning("Cannot start iOS sim capture via sidecar: %s — blank stream", exc)

        self._started = True
        log.info("iOS Simulator SCK MediaSource started (udid=%s)", self._udid)

    async def _handle_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        try:
            import struct
            while True:
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
            log.debug("iOS sim sidecar connection error: %s", exc)
        finally:
            writer.close()

    def track(self):
        return self._video_track

    async def audio_track(self):
        return None  # SCK audio stream → Opus wired in Phase 09-16

    async def set_bitrate(self, bps: int) -> None:
        pass

    async def request_keyframe(self) -> None:
        pass

    async def stop(self) -> None:
        self._started = False
        if self._sidecar_client and self._udid:
            try:
                await self._sidecar_client.stop_capture(self._udid)
                await self._sidecar_client.close()
            except Exception:
                pass
        if self._server:
            self._server.close()
        log.info("iOS Simulator SCK MediaSource stopped")


async def _find_free_port(port_range: range) -> int:
    import socket
    for port in port_range:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise OSError("No free port for iOS sim sidecar callback")
