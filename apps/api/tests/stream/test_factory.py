# tests/stream/test_factory.py — Phase 09 MediaSource/InputSink factory tests
"""
Tests for the (family, location) registry in stream/factory.py.
"""
from __future__ import annotations

import pytest

from app.stream.factory import (
    _SOURCE_REGISTRY,
    _SINK_REGISTRY,
    media_source_for,
    input_sink_for,
    register_source,
    register_sink,
    registered_pairs,
)
from app.stream.source import NullMediaSource, NullInputSink, InputEvent


class _FakeDevice:
    def __init__(self, family: str, location: str = "local"):
        self.family = family
        self.location = location
        self.provider_ids_json = "{}"


def test_unknown_pair_returns_null_source():
    device = _FakeDevice("unknown_xyz", "local")
    src = media_source_for(device)
    assert isinstance(src, NullMediaSource)


def test_unknown_pair_returns_null_sink():
    device = _FakeDevice("unknown_xyz", "local")
    sink = input_sink_for(device)
    assert isinstance(sink, NullInputSink)


def test_register_and_dispatch():
    from app.stream.source import MediaSource

    class _TestSource(MediaSource):
        def __init__(self, device):
            self._device = device
        async def start(self): pass
        def track(self): return None
        async def audio_track(self): return None
        async def set_bitrate(self, bps): pass
        async def request_keyframe(self): pass
        async def stop(self): pass

    register_source("test_family", "test_loc", _TestSource)
    device = _FakeDevice("test_family", "test_loc")
    src = media_source_for(device)
    assert isinstance(src, _TestSource)

    # cleanup
    _SOURCE_REGISTRY.pop(("test_family", "test_loc"), None)


def test_registered_pairs_is_union():
    from app.stream.source import MediaSource, InputSink

    class _S(MediaSource):
        def __init__(self, device): pass
        async def start(self): pass
        def track(self): return None
        async def audio_track(self): return None
        async def set_bitrate(self, bps): pass
        async def request_keyframe(self): pass
        async def stop(self): pass

    class _I(InputSink):
        def __init__(self, device): pass
        async def inject(self, ev): pass
        async def start(self): pass
        async def stop(self): pass

    register_source("paired_family", "local", _S)
    register_sink("paired_family", "local", _I)
    pairs = registered_pairs()
    assert ("paired_family", "local") in pairs

    # cleanup
    _SOURCE_REGISTRY.pop(("paired_family", "local"), None)
    _SINK_REGISTRY.pop(("paired_family", "local"), None)


def test_android_local_registered():
    """Android local source and sink must be registered after factory module loads."""
    # factory._register_all() is called at import time
    assert ("android", "local") in _SOURCE_REGISTRY
    assert ("android", "local") in _SINK_REGISTRY


def test_linux_local_registered():
    assert ("linux", "local") in _SOURCE_REGISTRY
    assert ("linux", "local") in _SINK_REGISTRY


def test_inputevent_pointer_move_unreliable_by_default():
    ev = InputEvent(kind="pointer_move", x=100, y=200)
    assert ev.reliable is False


def test_inputevent_pointer_down_reliable():
    ev = InputEvent(kind="pointer_down", x=100, y=200, reliable=True)
    assert ev.reliable is True
