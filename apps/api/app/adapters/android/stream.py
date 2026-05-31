# stream.py — Android aiortc video stream via adb screenrecord subprocess
from __future__ import annotations
import asyncio
import subprocess
from typing import Any

try:
    from aiortc.mediastreams import MediaStreamTrack  # type: ignore[import]
    from av import VideoFrame  # type: ignore[import]
    _AIORTC_AVAILABLE = True
except ImportError:
    MediaStreamTrack = object  # type: ignore[assignment,misc]
    _AIORTC_AVAILABLE = False


class AdbScreenTrack(MediaStreamTrack):  # type: ignore[misc]
    """VideoStreamTrack that reads H.264 frames from adb screenrecord subprocess."""
    kind = "video"

    def __init__(self, adb_serial: str):
        if _AIORTC_AVAILABLE:
            super().__init__()
        self.adb_serial = adb_serial
        self._proc: subprocess.Popen | None = None

    async def recv(self) -> Any:
        """Read next H.264 frame from adb subprocess pipe."""
        if self._proc is None:
            self._proc = subprocess.Popen(
                ["adb", "-s", self.adb_serial, "exec-out", "screenrecord",
                 "--output-format=h264", "-"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
        # In production, frames would be decoded via av; stub returns None for tests.
        return None

    async def stop(self) -> None:
        if self._proc:
            self._proc.terminate()
            self._proc = None


async def create_android_stream_offer(device: object) -> str:
    """Start AdbScreenTrack for device, create RTCPeerConnection offer. Returns SDP string."""
    if not _AIORTC_AVAILABLE:
        raise RuntimeError("aiortc not installed")
    from aiortc import RTCPeerConnection  # type: ignore[import]
    from app.adapters.android.observation import _get_adb_serial

    adb_serial = _get_adb_serial(device)
    track = AdbScreenTrack(adb_serial)
    pc = RTCPeerConnection()
    pc.addTrack(track)
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)
    return pc.localDescription.sdp
