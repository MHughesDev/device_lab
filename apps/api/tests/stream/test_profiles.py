# tests/stream/test_profiles.py — Phase 09 quality profile tests
from __future__ import annotations

import pytest

from app.stream.profiles import (
    SMOOTH,
    SHARP_TEXT,
    DEFAULT_PROFILE,
    FreezeDetector,
    get_profile,
)


def test_smooth_profile_fps():
    assert SMOOTH.fps == 30


def test_sharp_text_lowers_fps():
    assert SHARP_TEXT.fps < SMOOTH.fps


def test_sharp_text_raises_quality_via_lower_bitrate():
    # sharp_text trades fps for higher per-frame quality (lower bitrate + lower fps)
    assert SHARP_TEXT.bitrate_kbps <= SMOOTH.bitrate_kbps


def test_get_profile_unknown_returns_default():
    profile = get_profile("nonexistent_profile_xyz")
    assert profile == DEFAULT_PROFILE


def test_get_profile_by_name():
    assert get_profile("smooth") is SMOOTH
    assert get_profile("sharp_text") is SHARP_TEXT


def test_freeze_detector_not_frozen_initially():
    fd = FreezeDetector(SMOOTH)
    assert not fd.frozen


def test_freeze_detector_freezes_after_threshold():
    fd = FreezeDetector(SMOOTH)
    frame = b"\x00" * 100
    for _ in range(SMOOTH.freeze_threshold_frames):
        fd.update(frame)
    assert fd.frozen


def test_freeze_detector_unfreezes_on_motion():
    fd = FreezeDetector(SMOOTH)
    frame = b"\x00" * 100
    for _ in range(SMOOTH.freeze_threshold_frames + 2):
        fd.update(frame)
    assert fd.frozen

    fd.update(b"\xFF" * 100)
    assert not fd.frozen


def test_freeze_detector_reduces_effective_fps():
    fd = FreezeDetector(SMOOTH)
    frame = b"\x00" * 100
    for _ in range(SMOOTH.freeze_threshold_frames + 1):
        fd.update(frame)
    assert fd.effective_fps == SMOOTH.freeze_drop_fps


def test_freeze_detector_reset():
    fd = FreezeDetector(SMOOTH)
    frame = b"\x00" * 100
    for _ in range(SMOOTH.freeze_threshold_frames + 1):
        fd.update(frame)
    fd.reset()
    assert not fd.frozen
