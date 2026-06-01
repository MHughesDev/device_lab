# stream/profiles.py — Display & quality profiles (Phase 09, task 09-15)
"""
Quality profiles for the WebRTC stream. Two named profiles:

  smooth      — 30–60fps, motion-optimised (default for interactive sessions)
  sharp_text  — 10–15fps, higher per-frame quality (read-heavy agent work)

Freeze-drop: when consecutive frames are identical (static screen), the
pipeline drops to ~1fps and snaps back on motion. This saves CPU/bandwidth
in idle sessions without dropping the connection.

Local sessions pin high CBR (bandwidth is free, latency is the priority).
Cloud sessions use capped CRF + transport-cc ABR via set_bitrate().
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class QualityProfile:
    name: str
    fps: int
    bitrate_kbps: int
    width: int = 1920
    height: int = 1080
    freeze_drop_fps: int = 1           # fps when screen is static
    freeze_threshold_frames: int = 5   # consecutive identical frames before dropping
    crf: int | None = None             # None → CBR (local); set for cloud CRF mode


SMOOTH = QualityProfile(
    name="smooth",
    fps=30,
    bitrate_kbps=8000,
    freeze_drop_fps=1,
    freeze_threshold_frames=5,
)

SHARP_TEXT = QualityProfile(
    name="sharp_text",
    fps=12,
    bitrate_kbps=4000,
    freeze_drop_fps=1,
    freeze_threshold_frames=3,
)

_PROFILES: dict[str, QualityProfile] = {
    "smooth": SMOOTH,
    "sharp_text": SHARP_TEXT,
}

DEFAULT_PROFILE = SMOOTH


def get_profile(name: str) -> QualityProfile:
    """Return a named QualityProfile; falls back to DEFAULT_PROFILE."""
    return _PROFILES.get(name, DEFAULT_PROFILE)


class FreezeDetector:
    """Track consecutive identical frames and signal freeze-drop."""

    def __init__(self, profile: QualityProfile) -> None:
        self._profile = profile
        self._consecutive: int = 0
        self._last_hash: int | None = None
        self.frozen: bool = False

    def update(self, frame_data: bytes) -> bool:
        """Update with new frame data; return True if fps should be dropped to freeze_drop_fps."""
        h = hash(frame_data)
        if h == self._last_hash:
            self._consecutive += 1
        else:
            self._consecutive = 0
            self.frozen = False
        self._last_hash = h
        if self._consecutive >= self._profile.freeze_threshold_frames:
            self.frozen = True
        return self.frozen

    def reset(self) -> None:
        self._consecutive = 0
        self._last_hash = None
        self.frozen = False

    @property
    def effective_fps(self) -> int:
        return self._profile.freeze_drop_fps if self.frozen else self._profile.fps
