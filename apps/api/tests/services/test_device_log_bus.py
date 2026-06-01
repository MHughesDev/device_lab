# test_device_log_bus.py — Tests for DeviceLogBus (Phase 08, task 08-10)
from __future__ import annotations
import asyncio
import uuid
from unittest.mock import patch

import pytest

from app.services.device_log_bus import DeviceLogBus, redact, LogEntry


class TestRedactor:
    def test_redacts_aws_secret_key(self) -> None:
        msg = "AWS_SECRET_ACCESS_KEY=ABCDEFGHIJ1234567890"
        result = redact(msg)
        assert "ABCDEFGHIJ1234567890" not in result
        assert "[REDACTED]" in result

    def test_redacts_bearer_token(self) -> None:
        msg = "Authorization: Bearer eyJhbGci.eyJzdWIi.SflKxw"
        result = redact(msg)
        assert "eyJhbGci" not in result
        assert "[REDACTED]" in result

    def test_redacts_password(self) -> None:
        msg = "password=supersecret123"
        result = redact(msg)
        assert "supersecret123" not in result

    def test_passes_benign_text(self) -> None:
        msg = "Device transitioned to state: ready"
        assert redact(msg) == msg


class TestLogBusRingBuffer:
    def test_log_bus_ringbuffer_evicts_oldest(self) -> None:
        from app.services.device_log_bus import _RING_BUFFER_SIZE, _DeviceBus
        bus = _DeviceBus()
        device_id = uuid.uuid4()

        # Fill beyond ring capacity
        for i in range(_RING_BUFFER_SIZE + 10):
            entry = LogEntry(device_id, "info", "lifecycle", f"msg {i}")
            bus.emit(entry)

        entries = bus.replay()
        assert len(entries) == _RING_BUFFER_SIZE
        # Oldest evicted; newest retained
        assert entries[-1].message == f"msg {_RING_BUFFER_SIZE + 9}"

    def test_log_bus_filters_by_source(self) -> None:
        from app.services.device_log_bus import _DeviceBus
        bus = _DeviceBus()
        device_id = uuid.uuid4()

        bus.emit(LogEntry(device_id, "info", "lifecycle", "lifecycle event"))
        bus.emit(LogEntry(device_id, "info", "mcp", "mcp event"))

        lifecycle_only = bus.replay(source="lifecycle")
        assert len(lifecycle_only) == 1
        assert lifecycle_only[0].source == "lifecycle"


class TestDeviceLogBusSecretRedaction:
    def test_log_bus_redacts_secrets(self) -> None:
        bus = DeviceLogBus()
        device_id = uuid.uuid4()

        with patch.object(bus, "_persist_async"):
            bus.emit(device_id, "info", "transport", "token=mysecrettoken123")
            entries = bus.replay(device_id)
            assert len(entries) == 1
            assert "mysecrettoken123" not in entries[0].message
            assert "[REDACTED]" in entries[0].message


class TestDeviceLogBusFanout:
    def test_log_bus_fanout_to_subscribers(self) -> None:
        from app.services.device_log_bus import _DeviceBus
        bus = _DeviceBus()
        device_id = uuid.uuid4()

        q = bus.subscribe()
        entry = LogEntry(device_id, "info", "lifecycle", "test fanout")
        bus.emit(entry)

        received = q.get_nowait()
        assert received.message == "test fanout"
        bus.unsubscribe(q)


class TestDeviceLogBusReplayThenLive:
    def test_replay_returns_buffered_events(self) -> None:
        bus = DeviceLogBus()
        device_id = uuid.uuid4()

        with patch.object(bus, "_persist_async"):
            bus.emit(device_id, "info", "lifecycle", "old event")

        replayed = bus.replay(device_id)
        assert any(e.message == "old event" for e in replayed)
