# device_log_bus.py — Per-device structured log bus: ring buffer + async pub/sub + secret redaction
from __future__ import annotations
import asyncio
import json
import logging
import re
import threading
import uuid
from collections import deque
from datetime import UTC, datetime
from typing import AsyncIterator

log = logging.getLogger(__name__)

# Ring buffer size per device (events; oldest evicted when full)
_RING_BUFFER_SIZE = 1000

# How many events to persist to DB on best-effort basis
_DB_PERSIST_BATCH = 50

# ------------------------------------------------------------------
# Secret redaction
# ------------------------------------------------------------------

# Patterns that indicate a secret value — redact the matched group
_SECRET_PATTERNS = [
    re.compile(r'(AWS_SECRET_ACCESS_KEY\s*=\s*)[^\s&"\']+', re.IGNORECASE),
    re.compile(r'(AWS_ACCESS_KEY_ID\s*=\s*)[A-Z0-9]{16,}', re.IGNORECASE),
    re.compile(r'(Authorization:\s*Bearer\s+)\S+', re.IGNORECASE),
    re.compile(r'(token\s*=\s*)[^\s&"\']+', re.IGNORECASE),
    re.compile(r'(password\s*=\s*)[^\s&"\']+', re.IGNORECASE),
    re.compile(r'(secret\s*=\s*)[^\s&"\']+', re.IGNORECASE),
    re.compile(r'(key\s*=\s*)[^\s&"\']{8,}', re.IGNORECASE),
    # AWS session tokens (long base64)
    re.compile(r'(SessionToken\s*=\s*)[A-Za-z0-9+/=]{20,}', re.IGNORECASE),
]
_REDACT_REPLACEMENT = r'\1[REDACTED]'


def redact(text: str) -> str:
    """Strip secret-looking values from a log message or fields_json string."""
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub(_REDACT_REPLACEMENT, text)
    return text


# ------------------------------------------------------------------
# In-memory per-device log entry
# ------------------------------------------------------------------

class LogEntry:
    __slots__ = ("id", "device_id", "ts", "level", "source", "message", "fields_json")

    def __init__(
        self,
        device_id: uuid.UUID,
        level: str,
        source: str,
        message: str,
        fields: dict | None = None,
    ) -> None:
        self.id = uuid.uuid4()
        self.device_id = device_id
        self.ts = datetime.now(UTC)
        self.level = level
        self.source = source
        self.message = redact(message)
        self.fields_json = json.dumps(
            {k: redact(str(v)) for k, v in fields.items()} if fields else {}
        )

    def as_dict(self) -> dict:
        return {
            "id": str(self.id),
            "device_id": str(self.device_id),
            "ts": self.ts.isoformat(),
            "level": self.level,
            "source": self.source,
            "message": self.message,
            "fields_json": self.fields_json,
        }


# ------------------------------------------------------------------
# Per-device log bus
# ------------------------------------------------------------------

class _DeviceBus:
    """Ring buffer + subscriber set for one device."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._ring: deque[LogEntry] = deque(maxlen=_RING_BUFFER_SIZE)
        self._subscribers: set[asyncio.Queue] = set()

    def emit(self, entry: LogEntry) -> None:
        with self._lock:
            self._ring.append(entry)
            subs = list(self._subscribers)
        for q in subs:
            try:
                q.put_nowait(entry)
            except asyncio.QueueFull:
                pass  # slow subscriber — drop rather than block

    def replay(
        self,
        level: str | None = None,
        source: str | None = None,
        since: datetime | None = None,
    ) -> list[LogEntry]:
        with self._lock:
            entries = list(self._ring)
        return [
            e for e in entries
            if (level is None or e.level == level)
            and (source is None or e.source == source)
            and (since is None or e.ts >= since)
        ]

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=_RING_BUFFER_SIZE)
        with self._lock:
            self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        with self._lock:
            self._subscribers.discard(q)


# ------------------------------------------------------------------
# Global bus registry
# ------------------------------------------------------------------

class DeviceLogBus:
    """Process-global registry of per-device buses.

    Call :meth:`emit` from anywhere (sync or async) — fire-and-forget.
    Use :meth:`subscribe_stream` for an async generator that replays then
    streams live events (used by the WS/SSE route).
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._buses: dict[uuid.UUID, _DeviceBus] = {}

    def _bus(self, device_id: uuid.UUID) -> _DeviceBus:
        with self._lock:
            if device_id not in self._buses:
                self._buses[device_id] = _DeviceBus()
            return self._buses[device_id]

    def emit(
        self,
        device_id: uuid.UUID | str,
        level: str,
        source: str,
        message: str,
        fields: dict | None = None,
    ) -> None:
        """Emit a log event. Non-blocking; safe to call from sync code."""
        did = uuid.UUID(str(device_id)) if not isinstance(device_id, uuid.UUID) else device_id
        entry = LogEntry(did, level, source, message, fields)
        self._bus(did).emit(entry)
        self._persist_async(entry)

    def replay(
        self,
        device_id: uuid.UUID | str,
        level: str | None = None,
        source: str | None = None,
        since: datetime | None = None,
    ) -> list[LogEntry]:
        did = uuid.UUID(str(device_id)) if not isinstance(device_id, uuid.UUID) else device_id
        return self._bus(did).replay(level=level, source=source, since=since)

    async def subscribe_stream(
        self,
        device_id: uuid.UUID | str,
        level: str | None = None,
        source: str | None = None,
        since: datetime | None = None,
    ) -> AsyncIterator[LogEntry]:
        """Async generator: replay ring buffer then yield live events."""
        did = uuid.UUID(str(device_id)) if not isinstance(device_id, uuid.UUID) else device_id
        bus = self._bus(did)
        q = bus.subscribe()
        try:
            for entry in bus.replay(level=level, source=source, since=since):
                yield entry
            while True:
                entry = await q.get()
                if level and entry.level != level:
                    continue
                if source and entry.source != source:
                    continue
                if since and entry.ts < since:
                    continue
                yield entry
        finally:
            bus.unsubscribe(q)

    def _persist_async(self, entry: LogEntry) -> None:
        """Best-effort: persist log event to DB without blocking the caller."""
        def _do_persist() -> None:
            try:
                from app.core.db import engine
                from app.models import DeviceLogEvent
                from sqlmodel import Session
                with Session(engine) as db:
                    db.add(DeviceLogEvent(
                        id=entry.id,
                        device_id=entry.device_id,
                        ts=entry.ts,
                        level=entry.level,
                        source=entry.source,
                        message=entry.message,
                        fields_json=entry.fields_json if entry.fields_json != "{}" else None,
                    ))
                    db.commit()
            except Exception:
                pass  # best-effort; never block device operations on log persistence

        import threading
        threading.Thread(target=_do_persist, daemon=True).start()


# Process-global singleton
_log_bus: DeviceLogBus | None = None
_log_bus_lock = threading.Lock()


def get_log_bus() -> DeviceLogBus:
    global _log_bus
    if _log_bus is None:
        with _log_bus_lock:
            if _log_bus is None:
                _log_bus = DeviceLogBus()
    return _log_bus
