# tests/adapters/test_android_stream_input.py — Phase 09 Android stream/input tests
from __future__ import annotations

import asyncio
import struct
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class _FakeDevice:
    family = "android"
    location = "local"
    provider_ids_json = '{"adb_serial": "emulator-5554"}'


# --- AndroidInputSink ---

def test_encode_pointer_down():
    from app.adapters.android.input import _encode_control_message
    from app.stream.source import InputEvent
    ev = InputEvent(kind="pointer_down", x=100, y=200)
    msg = _encode_control_message(ev, 1080, 1920)
    assert msg is not None
    assert msg[0] == 2  # _MSG_INJECT_TOUCH


def test_encode_pointer_up():
    from app.adapters.android.input import _encode_control_message
    from app.stream.source import InputEvent
    ev = InputEvent(kind="pointer_up", x=100, y=200)
    msg = _encode_control_message(ev, 1080, 1920)
    assert msg is not None


def test_encode_scroll():
    from app.adapters.android.input import _encode_control_message
    from app.stream.source import InputEvent
    ev = InputEvent(kind="scroll", x=500, y=500, dx=0, dy=-3)
    msg = _encode_control_message(ev, 1080, 1920)
    assert msg is not None
    assert msg[0] == 3  # _MSG_INJECT_SCROLL


def test_encode_text():
    from app.adapters.android.input import _encode_control_message
    from app.stream.source import InputEvent
    ev = InputEvent(kind="text", text="hello")
    msg = _encode_control_message(ev, 1080, 1920)
    assert msg is not None
    assert msg[0] == 1  # _MSG_INJECT_TEXT
    assert b"hello" in msg


def test_encode_key_down():
    from app.adapters.android.input import _encode_control_message
    from app.stream.source import InputEvent
    ev = InputEvent(kind="key_down", key="Return")
    msg = _encode_control_message(ev, 1080, 1920)
    assert msg is not None
    assert msg[0] == 0  # _MSG_INJECT_KEYCODE


def test_android_keycode_return():
    from app.adapters.android.input import _android_keycode
    assert _android_keycode("Return") == 66


def test_android_keycode_backspace():
    from app.adapters.android.input import _android_keycode
    assert _android_keycode("BackSpace") == 67


def test_encode_returns_none_for_unknown():
    from app.adapters.android.input import _encode_control_message
    from app.stream.source import InputEvent
    ev = InputEvent(kind="unknown_event")
    msg = _encode_control_message(ev, 1080, 1920)
    assert msg is None


# --- AndroidLocalMediaSource ---

@pytest.mark.asyncio
async def test_android_source_stop_without_start():
    from app.adapters.android.stream_local import AndroidLocalMediaSource
    src = AndroidLocalMediaSource(_FakeDevice())
    await src.stop()  # should not raise


@pytest.mark.asyncio
async def test_android_source_start_creates_track():
    from app.adapters.android.stream_local import AndroidLocalMediaSource
    pytest.importorskip("aiortc")

    src = AndroidLocalMediaSource(_FakeDevice())

    with patch.object(src, "_start_scrcpy_server", new=AsyncMock()):
        with patch("asyncio.create_task", return_value=MagicMock()):
            await src.start()

    assert src.track() is not None
    assert src._started
    src._started = False
