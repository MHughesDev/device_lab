"""Minimal smoke test for the WebRTC stream peer module."""
from __future__ import annotations

import pytest


def test_stream_peer_imports():
    """Import StreamPeer — skipped if aiortc is not installed."""
    aiortc = pytest.importorskip("aiortc", reason="aiortc not installed")
    from app.stream.peer import StreamPeer  # noqa: F401
    assert StreamPeer is not None


def test_blank_video_track_kind():
    """_BlankVideoTrack.kind is 'video'."""
    pytest.importorskip("aiortc", reason="aiortc not installed")
    from app.stream.peer import _BlankVideoTrack
    track = _BlankVideoTrack()
    assert track.kind == "video"
