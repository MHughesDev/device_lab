# tests/adapters/test_windows_stream_input.py — Phase 09 Windows stream/input tests
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch


class _FakeDevice:
    family = "windows"
    location = "local"
    provider_ids_json = '{"container_id": "win01", "vnc_port": 5901, "qmp_socket": "/tmp/qmp-win01.sock"}'


# --- WindowsInputSink QMP ---

def test_qmp_abs_pointer_scaled():
    from app.adapters.windows.input import _qmp_abs_pointer
    cmd = _qmp_abs_pointer(500, 500)
    # 500/1000 * 32767 = 16383
    events = cmd["arguments"]["events"]
    x_val = next(e["data"]["value"] for e in events if e["data"]["axis"] == "x")
    assert x_val == int(500 * 32767 / 1000)


def test_qmp_button_left():
    from app.adapters.windows.input import _qmp_button
    assert _qmp_button(0) == "left"


def test_qmp_button_right():
    from app.adapters.windows.input import _qmp_button
    assert _qmp_button(2) == "right"


def test_build_qmp_events_pointer_move():
    from app.adapters.windows.input import _build_qmp_events
    from app.stream.source import InputEvent
    ev = InputEvent(kind="pointer_move", x=100, y=200)
    events = _build_qmp_events(ev)
    assert len(events) == 1
    assert events[0]["execute"] == "input-send-event"


def test_build_qmp_events_key_down():
    from app.adapters.windows.input import _build_qmp_events
    from app.stream.source import InputEvent
    ev = InputEvent(kind="key_down", key="Return")
    events = _build_qmp_events(ev)
    assert len(events) == 1
    assert events[0]["arguments"]["events"][0]["data"]["down"] is True


def test_build_qmp_events_key_up():
    from app.adapters.windows.input import _build_qmp_events
    from app.stream.source import InputEvent
    ev = InputEvent(kind="key_up", key="Return")
    events = _build_qmp_events(ev)
    assert events[0]["arguments"]["events"][0]["data"]["down"] is False


def test_qcode_return():
    from app.adapters.windows.input import _qcode
    assert _qcode("Return") == "ret"


def test_qcode_escape():
    from app.adapters.windows.input import _qcode
    assert _qcode("Escape") == "esc"


# --- WindowsLocalMediaSource ---

@pytest.mark.asyncio
async def test_windows_source_start_no_gst():
    pytest.importorskip("aiortc")
    from app.adapters.windows.stream_local import WindowsLocalMediaSource

    with patch("app.adapters.windows.stream_local.is_gstreamer_available", return_value=False):
        src = WindowsLocalMediaSource(_FakeDevice())
        await src.start()
        assert src._started
        src._started = False


@pytest.mark.asyncio
async def test_windows_source_stop_without_start():
    from app.adapters.windows.stream_local import WindowsLocalMediaSource
    src = WindowsLocalMediaSource(_FakeDevice())
    await src.stop()
