"""
app/realtime/publisher.py

Task event publisher abstraction.
Decouples services and workers from the underlying messaging transport (Redis Pub/Sub vs Mock).
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from app.core.logging import get_logger
from app.realtime.events import (
    build_activity_event,
    build_cancelled_event,
    build_completed_event,
    build_failed_event,
    build_progress_event,
    build_queued_event,
    build_stage_changed_event,
    build_started_event,
)
from app.realtime.redis_pubsub import redis_pubsub

logger = get_logger(__name__)


@runtime_checkable
class TaskEventPublisher(Protocol):
    """Protocol defining the task event publisher interface."""

    async def publish_event(self, task_id: str, event: dict[str, Any]) -> bool:
        """Publish a generic event dictionary asynchronously."""
        ...

    def publish_event_sync(self, task_id: str, event: dict[str, Any]) -> bool:
        """Publish a generic event dictionary synchronously."""
        ...

    async def publish_queued(self, task_id: str, data: dict[str, Any] | None = None) -> bool: ...
    async def publish_started(self, task_id: str, stage: str = "DISCOVERING", progress: int = 10, metrics: dict[str, Any] | None = None) -> bool: ...
    async def publish_progress(self, task_id: str, progress: int, stage: str, status: str = "RUNNING", metrics: dict[str, Any] | None = None) -> bool: ...
    async def publish_stage_changed(self, task_id: str, stage: str, progress: int, status: str = "RUNNING", metrics: dict[str, Any] | None = None) -> bool: ...
    async def publish_activity(self, task_id: str, message: str, stage: str) -> bool: ...
    async def publish_completed(self, task_id: str, metrics: dict[str, Any] | None = None) -> bool: ...
    async def publish_failed(self, task_id: str, stage: str, reason: str) -> bool: ...
    async def publish_cancelled(self, task_id: str, stage: str, progress: int) -> bool: ...


class BaseTaskEventPublisher:
    """Base class implementing convenience event building methods."""

    async def publish_event(self, task_id: str, event: dict[str, Any]) -> bool:
        raise NotImplementedError

    def publish_event_sync(self, task_id: str, event: dict[str, Any]) -> bool:
        raise NotImplementedError

    async def publish_queued(self, task_id: str, data: dict[str, Any] | None = None) -> bool:
        return await self.publish_event(task_id, build_queued_event(task_id, data))

    async def publish_started(
        self,
        task_id: str,
        stage: str = "DISCOVERING",
        progress: int = 10,
        metrics: dict[str, Any] | None = None,
    ) -> bool:
        return await self.publish_event(
            task_id,
            build_started_event(task_id, stage=stage, progress=progress, metrics=metrics),
        )

    async def publish_progress(
        self,
        task_id: str,
        progress: int,
        stage: str,
        status: str = "RUNNING",
        metrics: dict[str, Any] | None = None,
    ) -> bool:
        return await self.publish_event(
            task_id,
            build_progress_event(
                task_id,
                progress=progress,
                stage=stage,
                status=status,
                metrics=metrics,
            ),
        )

    async def publish_stage_changed(
        self,
        task_id: str,
        stage: str,
        progress: int,
        status: str = "RUNNING",
        metrics: dict[str, Any] | None = None,
    ) -> bool:
        return await self.publish_event(
            task_id,
            build_stage_changed_event(
                task_id,
                stage=stage,
                progress=progress,
                status=status,
                metrics=metrics,
            ),
        )

    async def publish_activity(self, task_id: str, message: str, stage: str) -> bool:
        return await self.publish_event(
            task_id,
            build_activity_event(task_id, message=message, stage=stage),
        )

    async def publish_completed(self, task_id: str, metrics: dict[str, Any] | None = None) -> bool:
        return await self.publish_event(
            task_id,
            build_completed_event(task_id, metrics=metrics),
        )

    async def publish_failed(self, task_id: str, stage: str, reason: str) -> bool:
        return await self.publish_event(
            task_id,
            build_failed_event(task_id, stage=stage, reason=reason),
        )

    async def publish_cancelled(self, task_id: str, stage: str, progress: int) -> bool:
        return await self.publish_event(
            task_id,
            build_cancelled_event(task_id, stage=stage, progress=progress),
        )


class RedisTaskEventPublisher(BaseTaskEventPublisher):
    """Production publisher using Redis Pub/Sub."""

    async def publish_event(self, task_id: str, event: dict[str, Any]) -> bool:
        return await redis_pubsub.publish(task_id, event)

    def publish_event_sync(self, task_id: str, event: dict[str, Any]) -> bool:
        return redis_pubsub.publish_sync(task_id, event)


class MockTaskEventPublisher(BaseTaskEventPublisher):
    """In-memory publisher for testing without requiring an active Redis broker."""

    def __init__(self, connection_manager: Any = None) -> None:
        self.published_events: list[dict[str, Any]] = []
        self.connection_manager = connection_manager

    async def publish_event(self, task_id: str, event: dict[str, Any]) -> bool:
        self.published_events.append(event)
        if self.connection_manager:
            await self.connection_manager.broadcast(task_id, event)
        return True

    def publish_event_sync(self, task_id: str, event: dict[str, Any]) -> bool:
        self.published_events.append(event)
        return True

    def clear(self) -> None:
        self.published_events.clear()


# Default singleton publisher instance
_current_publisher: TaskEventPublisher = RedisTaskEventPublisher()


def get_event_publisher() -> TaskEventPublisher:
    """Return the currently configured event publisher."""
    return _current_publisher


def set_event_publisher(publisher: TaskEventPublisher) -> None:
    """Override the event publisher (e.g. with MockTaskEventPublisher during tests)."""
    global _current_publisher
    _current_publisher = publisher
