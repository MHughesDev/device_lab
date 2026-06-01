# tests/adapters/test_linux_stream_input.py — Phase 09 Linux stream/input tests
from __future__ import annotations

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class _FakeDevice:
    family = "linux"
    location = "local"
    provider_ids_json = '{"container_id": "abc123", "display": ":0"}'


# --- LinuxInputSink ---

def test_build_xdotool_pointer_move():
    from app.adapters.linux.input import _build_xdotool_cmd
    from app.stream.source import InputEvent
    ev = InputEvent(kind="pointer_move", x=100, y=200)
    cmd = _build_xdotool_cmd(ev, ":0")
    assert cmd is not None
    assert "xdotool" in cmd
    assert "mousemove" in cmd


def test_build_xdotool_key_down():
    from app.adapters.linux.input import _build_xdotool_cmd
    from app.stream.source import InputEvent
    ev = InputEvent(kind="key_down", key="Return")
    cmd = _build_xdotool_cmd(ev, ":0")
    assert cmd is not None
    assert "keydown" in cmd
    assert "Return" in cmd


def test_build_xdotool_text():
    from app.adapters.linux.input import _build_xdotool_cmd
    from app.stream.source import InputEvent
    ev = InputEvent(kind="text", text="hello world")
    cmd = _build_xdotool_cmd(ev, ":0")
    assert cmd is not None
    assert "type" in cmd


def test_build_xdotool_scroll_down():
    from app.adapters.linux.input import _build_xdotool_cmd
    from app.stream.source import InputEvent
    ev = InputEvent(kind="scroll", x=0, y=0, dy=-2)
    cmd = _build_xdotool_cmd(ev, ":0")
    assert cmd is not None
    assert "5" in cmd  # scroll down = button 5


def test_build_xdotool_unknown_event():
    from app.adapters.linux.input import _build_xdotool_cmd
    from app.stream.source import InputEvent
    ev = InputEvent(kind="nonexistent")
    cmd = _build_xdotool_cmd(ev, ":0")
    assert cmd is None


# --- LinuxLocalMediaSource ---

@pytest.mark.asyncio
async def test_linux_source_start_no_gst():
    pytest.importorskip("aiortc")
    from app.adapters.linux.stream_local import LinuxLocalMediaSource

    with patch("app.adapters.linux.stream_local.is_gstreamer_available", return_value=False):
        src = LinuxLocalMediaSource(_FakeDevice())
        await src.start()
        assert src._started
        assert src.track() is not None  # blank track still returned
        src._started = False


@pytest.mark.asyncio
async def test_linux_source_stop_without_start():
    from app.adapters.linux.stream_local import LinuxLocalMediaSource
    src = LinuxLocalMediaSource(_FakeDevice())
    await src.stop()  # should not raise
