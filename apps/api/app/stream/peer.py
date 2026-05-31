"""
WebRTC stream peer — wraps aiortc RTCPeerConnection with split video+input channel.
Pattern from aiortc/examples/server and aiortc/examples/datachannel-cli.
"""
from __future__ import annotations

import asyncio
import fractions
from collections.abc import AsyncIterator

from aiortc import RTCDataChannel, RTCPeerConnection, RTCSessionDescription  # type: ignore
from aiortc.mediastreams import MediaStreamTrack  # type: ignore
from av import VideoFrame  # type: ignore


class _BlankVideoTrack(MediaStreamTrack):
    """Minimal video track that emits a blank frame — replaced by runtime agent feed in Phase 05+."""
    kind = "video"

    def __init__(self) -> None:
        super().__init__()
        self._timestamp = 0

    async def recv(self) -> VideoFrame:
        pts, time_base = await self.next_timestamp()
        frame = VideoFrame(width=1280, height=720)
        frame.pts = pts
        frame.time_base = time_base
        await asyncio.sleep(1 / 30)
        return frame

    async def next_timestamp(self) -> tuple[int, fractions.Fraction]:
        time_base = fractions.Fraction(1, 90000)
        self._timestamp += int(90000 / 30)
        return self._timestamp, time_base


class StreamPeer:
    def __init__(self) -> None:
        self.pc: RTCPeerConnection = RTCPeerConnection()
        self._input_channel: RTCDataChannel | None = None
        self._input_events: asyncio.Queue[dict] = asyncio.Queue(maxsize=256)

    async def create_offer(self) -> RTCSessionDescription:
        self.pc.addTrack(_BlankVideoTrack())
        self._input_channel = self.pc.createDataChannel("input")

        @self._input_channel.on("message")  # type: ignore
        def on_message(message: str | bytes) -> None:
            import json
            try:
                event = json.loads(message) if isinstance(message, (str, bytes)) else {}
                self._input_events.put_nowait(event)
            except Exception:
                pass

        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)
        return self.pc.localDescription  # type: ignore

    async def set_answer(self, sdp: str, sdp_type: str = "answer") -> None:
        answer = RTCSessionDescription(sdp=sdp, type=sdp_type)
        await self.pc.setRemoteDescription(answer)

    async def send_input_event(self, event: dict) -> None:
        if self._input_channel and self._input_channel.readyState == "open":
            import json
            self._input_channel.send(json.dumps(event))

    async def input_events(self) -> AsyncIterator[dict]:
        while True:
            yield await self._input_events.get()

    async def close(self) -> None:
        await self.pc.close()
