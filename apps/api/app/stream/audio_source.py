# stream/audio_source.py — Opus audio track sources (Phase 09, task 09-16)
"""
AudioSource SPI and per-family capture stub registry.

Audio is always on in interactive mode (not a separate toggle). Each family
captures device audio and delivers Opus frames via EncodedAudioTrack.

Per-family capture paths:
  Linux (Docker)   — PulseAudio/ALSA virtual sink → GStreamer pulsesrc/alsasrc → Opus
  Android          — scrcpy audio channel (enabled via send_device_meta=false audio=true)
  Windows (QEMU)   — VirtIO audio → host PulseAudio/PipeWire → GStreamer → Opus
  macOS (vz)       — VZVirtioSoundDevice → host CoreAudio → AVAudioEngine → Opus
  iOS Sim          — ScreenCaptureKit audio stream → AVAudioEngine → Opus

All concrete sources are stubs in this phase; they return a NullAudioSource that
emits silence until full per-family audio is wired up.
"""
from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Callable

log = logging.getLogger(__name__)


class AudioSource(ABC):
    """SPI for per-family audio capture."""

    @abstractmethod
    async def start(self) -> None: ...

    @abstractmethod
    def track(self): ...

    @abstractmethod
    async def stop(self) -> None: ...


class NullAudioSource(AudioSource):
    """Silence source — placeholder until per-family audio is wired."""

    def __init__(self) -> None:
        self._track = None

    async def start(self) -> None:
        from app.stream.encoded_track import EncodedAudioTrack
        self._track = EncodedAudioTrack()

    def track(self):
        return self._track

    async def stop(self) -> None:
        self._track = None


# Registry keyed on (family, location) — populated by per-family modules
_AUDIO_REGISTRY: dict[tuple[str, str], type[AudioSource]] = {}


def register_audio(family: str, location: str, cls: type[AudioSource]) -> None:
    _AUDIO_REGISTRY[(family, location)] = cls


def audio_source_for(device: object) -> AudioSource:
    """Return the AudioSource for a device's (family, location) pair."""
    family = getattr(device, "family", "unknown")
    location = getattr(device, "location", "local")
    cls = _AUDIO_REGISTRY.get((family, location))
    if cls is None:
        log.debug("No AudioSource for (%s, %s) — using NullAudioSource", family, location)
        return NullAudioSource()
    return cls(device)  # type: ignore[call-arg]
