# packages/tasks/interfaces.py
"""Background task protocols and an in-memory implementation for development."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal, Protocol, runtime_checkable

TaskStatus = Literal["pending", "running", "success", "failure", "cancelled"]


@dataclass(frozen=True, slots=True)
class TaskDefinition:
    """Immutable description of work to run asynchronously."""

    task_name: str
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] | None = None
    idempotency_key: str | None = None
    priority: int = 0


@dataclass(frozen=True, slots=True)
class TaskResult:
    """Snapshot of task state returned by a broker."""

    task_id: str
    status: TaskStatus
    result: Any | None = None
    error: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None


@runtime_checkable
class TaskInterface(Protocol):
    """Submit and observe background tasks."""

    async def submit(self, task: TaskDefinition) -> TaskResult: ...

    async def get_status(self, task_id: str) -> TaskResult: ...

    async def cancel(self, task_id: str) -> bool: ...


@runtime_checkable
class TaskHandler(Protocol):
    """Executes a logical unit of background work."""

    async def handle(self, task: TaskDefinition) -> Any: ...


class InMemoryTaskInterface:
    """Development helper that records submitted tasks without a broker."""

    def __init__(self) -> None:
        self._tasks: dict[str, TaskResult] = {}

    async def submit(self, task: TaskDefinition) -> TaskResult:
        task_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        result = TaskResult(task_id=task_id, status="pending", created_at=now)
        self._tasks[task_id] = result
        return result

    async def get_status(self, task_id: str) -> TaskResult:
        return self._tasks[task_id]

    async def cancel(self, task_id: str) -> bool:
        if task_id not in self._tasks:
            return False
        existing = self._tasks[task_id]
        if existing.status != "pending":
            return False
        self._tasks[task_id] = TaskResult(
            task_id=task_id,
            status="cancelled",
            created_at=existing.created_at,
            completed_at=datetime.now(UTC),
        )
        return True
