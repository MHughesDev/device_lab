# adapters/android/stream_local.py — Android MediaSource via scrcpy H.264 passthrough (Phase 09, task 09-05)
"""
Streams Android screen via scrcpy-server running on the device. scrcpy encodes with
MediaCodec (device GPU) and streams raw H.264 access units over an adb-forwarded TCP
socket. We feed them directly into EncodedVideoTrack (no re-encode).

References:
  - https://github.com/Genymobile/scrcpy (scrcpy protocol)
  - scrcpy-server.jar binary in adapters/android/vendor/
"""
from __future__ import annotations

import asyncio
import json
import logging
import struct

from app.stream.source import MediaSource

log = logging.getLogger(__name__)

_SCRCPY_SERVER_DEVICE_PATH = "/data/local/tmp/scrcpy-server.jar"
_SCRCPY_PORT_LOCAL = 27183  # host-side port after adb forward
_SCRCPY_CONTROL_PORT_LOCAL = 27184
_DEFAULT_BITRATE = 8_000_000  # 8 Mbps
_DEFAULT_MAX_SIZE = 1920
_DEFAULT_FPS = 30

# scrcpy server startup command on device
_SCRCPY_SERVER_CMD = (
    "CLASSPATH={jar} app_process / com.genymobile.scrcpy.Server "
    "2.3 tunnel_forward=true video_bit_rate={bps} max_size={max_size} max_fps={fps} "
    "send_device_meta=false send_frame_meta=false audio=true"
)


class AndroidLocalMediaSource(MediaSource):
    """MediaSource for local Android devices via scrcpy."""

    def __init__(self, device: object) -> None:
        self._device = device
        ids: dict = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
        self._adb_serial: str = ids.get("adb_serial", "emulator-5554")
        self._bitrate = _DEFAULT_BITRATE
        self._max_size = _DEFAULT_MAX_SIZE
        self._fps = _DEFAULT_FPS
        self._track = None
        self._server_proc: asyncio.subprocess.Process | None = None
        self._reader_task: asyncio.Task | None = None
        self._started = False

    async def start(self) -> None:
        if self._started:
            return
        from app.stream.encoded_track import EncodedVideoTrack
        self._video_track = EncodedVideoTrack(
            keyframe_cb=self.request_keyframe, fps=self._fps
        )
        await self._start_scrcpy_server()
        self._reader_task = asyncio.create_task(
            self._read_h264_stream(), name="android-scrcpy-reader"
        )
        self._started = True
        log.info("Android scrcpy MediaSource started for %s", self._adb_serial)

    def track(self):
        return self._video_track

    async def audio_track(self):
        return None  # scrcpy audio wired in Phase 09-16

    async def set_bitrate(self, bps: int) -> None:
        self._bitrate = bps
        # Live bitrate adjustment requires a scrcpy control message; no-op for now

    async def request_keyframe(self) -> None:
        # scrcpy control: send IDR request via control socket (Phase 09-06 wires this)
        pass

    async def stop(self) -> None:
        self._started = False
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
        await self._stop_scrcpy_server()
        log.info("Android scrcpy MediaSource stopped for %s", self._adb_serial)

    async def _start_scrcpy_server(self) -> None:
        """Push scrcpy-server.jar to device and launch it, forwarding the port."""
        import subprocess
        # Push server jar if not present
        subprocess.run(
            ["adb", "-s", self._adb_serial, "push",
             _SCRCPY_SERVER_DEVICE_PATH, _SCRCPY_SERVER_DEVICE_PATH],
            capture_output=True,
        )
        # Forward TCP port
        subprocess.run(
            ["adb", "-s", self._adb_serial, "forward",
             f"tcp:{_SCRCPY_PORT_LOCAL}", "localabstract:scrcpy"],
            check=True, capture_output=True,
        )
        # Start server on device
        server_cmd = _SCRCPY_SERVER_CMD.format(
            jar=_SCRCPY_SERVER_DEVICE_PATH,
            bps=self._bitrate,
            max_size=self._max_size,
            fps=self._fps,
        )
        self._server_proc = await asyncio.create_subprocess_exec(
            "adb", "-s", self._adb_serial, "shell", server_cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        # Give server a moment to bind
        await asyncio.sleep(0.5)

    async def _stop_scrcpy_server(self) -> None:
        import subprocess
        if self._server_proc:
            try:
                self._server_proc.terminate()
                await asyncio.wait_for(self._server_proc.wait(), timeout=3)
            except Exception:
                pass
        subprocess.run(
            ["adb", "-s", self._adb_serial, "forward", "--remove", f"tcp:{_SCRCPY_PORT_LOCAL}"],
            capture_output=True,
        )

    async def _read_h264_stream(self) -> None:
        """Connect to the scrcpy socket and push H.264 AUs into the encoded track."""
        try:
            reader, _ = await asyncio.open_connection("127.0.0.1", _SCRCPY_PORT_LOCAL)
        except OSError as exc:
            log.error("Cannot connect to scrcpy socket: %s", exc)
            return

        try:
            while True:
                # scrcpy H.264 stream: raw NAL units, no length prefix in tunnel_forward mode
                # We read in 65536-byte chunks and push as-is (access units are self-delimiting
                # for the aiortc H.264 depacketizer when start codes are present)
                data = await reader.read(65536)
                if not data:
                    break
                if self._video_track:
                    await self._video_track.push_au(data)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            log.error("scrcpy H.264 reader error: %s", exc)
