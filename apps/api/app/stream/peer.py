# peer.py — WebRTC stream peer: real MediaSource/InputSink wired (Phase 09, task 09-03)
"""
WebRTC stream peer — wraps aiortc RTCPeerConnection with split video+audio tracks
and an input data channel routed to InputSink.inject().

Phase 09 replaces _BlankVideoTrack with the real MediaSource.track() resolved from
the (family, location) factory. Input events decoded from the binary wire protocol
are coalesced (pointer-moves) and forwarded to InputSink.inject().
"""
from __future__ import annotations

import asyncio
import fractions
import json
import logging
import struct
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

from aiortc import RTCDataChannel, RTCPeerConnection, RTCSessionDescription  # type: ignore
from aiortc.mediastreams import MediaStreamTrack  # type: ignore
from av import VideoFrame  # type: ignore

if TYPE_CHECKING:
    from app.stream.source import InputSink, MediaSource

log = logging.getLogger(__name__)


def _emit_peer_event(device_id: str, event: str, fields: dict | None = None) -> None:
    if not device_id:
        return
    try:
        from app.services.device_log_bus import get_log_bus
        get_log_bus().emit(
            device_id,
            level="info",
            source="stream",
            message=f"Stream peer event: {event}",
            fields={"event": event, **(fields or {})},
        )
    except Exception:
        pass


class _BlankVideoTrack(MediaStreamTrack):
    """Minimal video track that emits a blank frame — used as fallback in headless mode."""
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


def _decode_input_wire(message: str | bytes) -> "list[dict]":
    """Decode a data-channel input message into a list of InputEvent dicts.

    Wire protocol (binary): 1-byte kind + payload. Falls back to JSON for
    text-mode messages (compatibility with the Phase 04 test harness).

    kind values (binary):
      0x01  pointer_move  — reliable=False  [kind(1), x(2), y(2)]
      0x02  pointer_down  — reliable=True   [kind(1), x(2), y(2), btn(1)]
      0x03  pointer_up    — reliable=True   [kind(1), x(2), y(2), btn(1)]
      0x04  key_down      — reliable=True   [kind(1), key_len(1), key(N)]
      0x05  key_up        — reliable=True   [kind(1), key_len(1), key(N)]
      0x06  scroll        — reliable=False  [kind(1), x(2), y(2), dx(2), dy(2)]
      0x07  text          — reliable=True   [kind(1), text_len(2), text(N, UTF-8)]
    """
    if isinstance(message, str):
        try:
            return [json.loads(message)]
        except json.JSONDecodeError:
            return []

    if len(message) < 1:
        return []

    kind_byte = message[0]
    _KIND_MAP = {
        0x01: "pointer_move",
        0x02: "pointer_down",
        0x03: "pointer_up",
        0x04: "key_down",
        0x05: "key_up",
        0x06: "scroll",
        0x07: "text",
    }
    kind = _KIND_MAP.get(kind_byte)
    if kind is None:
        return []

    try:
        if kind in ("pointer_move",):
            x, y = struct.unpack_from(">HH", message, 1)
            return [{"kind": kind, "x": x, "y": y, "reliable": False}]
        if kind in ("pointer_down", "pointer_up"):
            x, y, btn = struct.unpack_from(">HHB", message, 1)
            return [{"kind": kind, "x": x, "y": y, "button": btn, "reliable": True}]
        if kind in ("key_down", "key_up"):
            key_len = message[1]
            key = message[2:2 + key_len].decode("utf-8", errors="replace")
            return [{"kind": kind, "key": key, "reliable": True}]
        if kind == "scroll":
            x, y, dx, dy = struct.unpack_from(">HHhh", message, 1)
            return [{"kind": kind, "x": x, "y": y, "dx": dx, "dy": dy, "reliable": False}]
        if kind == "text":
            text_len = struct.unpack_from(">H", message, 1)[0]
            text = message[3:3 + text_len].decode("utf-8", errors="replace")
            return [{"kind": kind, "text": text, "reliable": True}]
    except struct.error:
        return []

    return []


class StreamPeer:
    """WebRTC peer with real MediaSource + InputSink (Phase 09).

    Pass ``device`` to wire a concrete MediaSource and InputSink via the factory.
    Omit it for headless/test mode (blank track + null sink).
    """

    def __init__(self, device: object | None = None) -> None:
        from app.stream.ice import rtc_configuration_for
        from aiortc import RTCConfiguration, RTCIceServer  # type: ignore

        location = getattr(device, "location", "local") if device else "local"
        ice_cfg = rtc_configuration_for(location)
        ice_servers = [
            RTCIceServer(urls=s["urls"], username=s.get("username"), credential=s.get("credential"))
            for s in ice_cfg.get("iceServers", [])
        ]
        self.pc: RTCPeerConnection = RTCPeerConnection(
            RTCConfiguration(iceServers=ice_servers)
        )
        self._device = device
        self._input_channel: RTCDataChannel | None = None
        self._input_events: asyncio.Queue[dict] = asyncio.Queue(maxsize=256)
        self._media_source: MediaSource | None = None
        self._input_sink: InputSink | None = None
        self._last_pointer: dict | None = None  # for pointer-move coalescing
        self._input_pump_task: asyncio.Task | None = None

    def _wire_ice_events(self) -> None:
        """Emit log-bus events on ICE state transitions."""
        device_id = str(getattr(self._device, "id", "")) if self._device else ""

        @self.pc.on("iceconnectionstatechange")  # type: ignore
        def on_ice_state() -> None:
            state = self.pc.iceConnectionState
            log.debug("ICE state → %s (device=%s)", state, device_id)
            _emit_peer_event(device_id, "ice_state", {"state": state})

        @self.pc.on("connectionstatechange")  # type: ignore
        def on_conn_state() -> None:
            state = self.pc.connectionState
            log.debug("Connection state → %s (device=%s)", state, device_id)
            _emit_peer_event(device_id, "connection_state", {"state": state})

    async def _setup_media(self) -> None:
        """Resolve and start MediaSource; add track(s) to PeerConnection."""
        self._wire_ice_events()

        if self._device is None:
            self.pc.addTrack(_BlankVideoTrack())
            return

        from app.stream.factory import media_source_for
        self._media_source = media_source_for(self._device)
        await self._media_source.start()

        track = self._media_source.track()
        self.pc.addTrack(track)
        _emit_peer_event(
            str(getattr(self._device, "id", "")), "track_added",
            {"kind": getattr(track, "kind", "video")}
        )

        audio = await self._media_source.audio_track()
        if audio is not None:
            self.pc.addTrack(audio)

    async def _setup_input(self) -> None:
        """Resolve InputSink and wire the data channel → inject loop."""
        if self._device is None:
            return

        from app.stream.factory import input_sink_for
        self._input_sink = input_sink_for(self._device)
        await self._input_sink.start()

        self._input_pump_task = asyncio.create_task(self._input_pump(), name="input-pump")

    async def _input_pump(self) -> None:
        """Dequeue input events and inject them, coalescing pointer_moves."""
        while True:
            try:
                ev = await self._input_events.get()
            except asyncio.CancelledError:
                break

            kind = ev.get("kind", "")

            # Coalesce: consume all queued pointer_moves, keep only the latest
            if kind == "pointer_move":
                latest = ev
                while True:
                    try:
                        next_ev = self._input_events.get_nowait()
                        if next_ev.get("kind") == "pointer_move":
                            latest = next_ev
                        else:
                            # Non-move event behind us — put it back and process latest
                            await self._input_events.put(next_ev)
                            break
                    except asyncio.QueueEmpty:
                        break
                ev = latest

            if self._input_sink:
                from app.stream.source import InputEvent
                try:
                    ie = InputEvent(
                        kind=ev.get("kind", ""),
                        x=ev.get("x"),
                        y=ev.get("y"),
                        button=ev.get("button"),
                        key=ev.get("key"),
                        text=ev.get("text"),
                        dx=ev.get("dx"),
                        dy=ev.get("dy"),
                    )
                    await self._input_sink.inject(ie)
                except Exception as exc:
                    log.debug("InputSink.inject error: %s", exc)

    async def _setup_offer_answer(self, sdp_offer: str) -> str:
        """Set remote offer, set up media+input, create and return answer SDP."""
        from aiortc import RTCSessionDescription  # type: ignore
        remote = RTCSessionDescription(sdp=sdp_offer, type="offer")
        await self.pc.setRemoteDescription(remote)
        await self._setup_media()
        self._input_channel = self.pc.createDataChannel("input")
        self._wire_input_channel()
        answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(answer)
        await self._setup_input()
        return self.pc.localDescription.sdp  # type: ignore

    def _wire_input_channel(self) -> None:
        if self._input_channel is None:
            return

        @self._input_channel.on("message")  # type: ignore
        def on_message(message: str | bytes) -> None:
            events = _decode_input_wire(message)
            for ev in events:
                try:
                    self._input_events.put_nowait(ev)
                except asyncio.QueueFull:
                    pass

    async def create_offer(self) -> RTCSessionDescription:
        await self._setup_media()
        self._input_channel = self.pc.createDataChannel("input")
        self._wire_input_channel()
        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)
        await self._setup_input()
        return self.pc.localDescription  # type: ignore

    async def set_answer(self, sdp: str, sdp_type: str = "answer") -> None:
        answer = RTCSessionDescription(sdp=sdp, type=sdp_type)
        await self.pc.setRemoteDescription(answer)

    async def send_input_event(self, event: dict) -> None:
        if self._input_channel and self._input_channel.readyState == "open":
            self._input_channel.send(json.dumps(event))

    async def input_events(self) -> AsyncIterator[dict]:
        while True:
            yield await self._input_events.get()

    async def close(self) -> None:
        if self._input_pump_task:
            self._input_pump_task.cancel()
            try:
                await self._input_pump_task
            except asyncio.CancelledError:
                pass
        if self._input_sink:
            await self._input_sink.stop()
        if self._media_source:
            await self._media_source.stop()
        await self.pc.close()
