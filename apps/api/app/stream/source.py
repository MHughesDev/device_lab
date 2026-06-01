# source.py — MediaSource / InputSink SPI (Phase 09, task 09-01)
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class InputEvent:
    """Unified input event injected into a device via InputSink.inject()."""
    kind: str  # pointer_move | pointer_down | pointer_up | key_down | key_up | scroll | text
    x: int | None = None
    y: int | None = None
    button: int | None = None       # 0=left, 1=middle, 2=right
    key: str | None = None          # XKB key name or Android keycode string
    text: str | None = None         # text injection (clipboard-less typing)
    dx: int | None = None           # scroll delta x (pixels or notches)
    dy: int | None = None           # scroll delta y
    # Pointer moves are cheap & lossy; key/click events must be delivered reliably.
    reliable: bool = field(default_factory=lambda: False)

    def __post_init__(self) -> None:
        if self.kind in ("pointer_down", "pointer_up", "key_down", "key_up", "text"):
            object.__setattr__(self, "reliable", True)


class MediaSource(ABC):
    """Abstract media source: captures and encodes a device's display."""

    @abstractmethod
    async def start(self) -> None:
        """Begin capture/encode. Must be idempotent."""

    @abstractmethod
    def track(self):
        """Return the aiortc MediaStreamTrack to add to the RTCPeerConnection."""

    async def audio_track(self):
        """Return an optional audio MediaStreamTrack (None = no audio for this source)."""
        return None

    async def set_bitrate(self, bps: int) -> None:
        """Request a bitrate change (cloud ABR). No-op for local sources."""

    async def request_keyframe(self) -> None:
        """Request an IDR/keyframe from the encoder (called on PLI/FIR)."""

    @abstractmethod
    async def stop(self) -> None:
        """Tear down capture/encode cleanly."""


class InputSink(ABC):
    """Abstract input sink: injects pointer/key/text events into a device."""

    @abstractmethod
    async def inject(self, ev: InputEvent) -> None:
        """Inject a single input event."""

    async def start(self) -> None:
        """Optional startup (e.g. open control socket). Default is no-op."""

    async def stop(self) -> None:
        """Optional teardown. Default is no-op."""


class NullMediaSource(MediaSource):
    """Placeholder source used before a real source is wired (headless mode)."""

    async def start(self) -> None:
        pass

    def track(self):
        from app.stream.peer import _BlankVideoTrack
        return _BlankVideoTrack()

    async def stop(self) -> None:
        pass


class NullInputSink(InputSink):
    """Placeholder sink used when input is not supported or not yet wired."""

    async def inject(self, ev: InputEvent) -> None:
        pass
