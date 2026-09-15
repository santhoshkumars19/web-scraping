"""
app/realtime/subscriber.py

Task subscriber manager.
Listens to Redis Pub/Sub channels for tasks with active WebSocket subscribers
and forwards incoming events to the ConnectionManager for browser delivery.
"""

from __future__ import annotations

import asyncio
from typing import Any

from app.core.logging import get_logger
from app.realtime.connection_manager import ConnectionManager, connection_manager
from app.realtime.redis_pubsub import redis_pubsub

logger = get_logger(__name__)


class TaskSubscriberManager:
    """Manages background Redis Pub/Sub listener tasks for active tasks."""

    def __init__(self) -> None:
        # task_id -> asyncio.Task running _listen_loop
        self._listener_tasks: dict[str, asyncio.Task[Any]] = {}
        self._lock = asyncio.Lock()

    async def ensure_subscribed(
        self,
        task_id: str,
        manager: ConnectionManager = connection_manager,
    ) -> None:
        """Ensure a background listener is actively streaming from Redis for this task."""
        async with self._lock:
            existing_task = self._listener_tasks.get(task_id)
            if existing_task is None or existing_task.done():
                task = asyncio.create_task(
                    self._listen_loop(task_id, manager),
                    name=f"redis-subscriber-{task_id}",
                )
                self._listener_tasks[task_id] = task
                logger.info("Started Redis Pub/Sub subscriber task for %s", task_id)

    async def unsubscribe_if_empty(
        self,
        task_id: str,
        manager: ConnectionManager = connection_manager,
    ) -> None:
        """Cancel and clean up the Redis listener if no connected clients remain for this task."""
        async with self._lock:
            if manager.get_connection_count(task_id) == 0:
                listener = self._listener_tasks.pop(task_id, None)
                if listener and not listener.done():
                    listener.cancel()
                    logger.info("Cancelled Redis Pub/Sub subscriber task for %s (no clients remaining)", task_id)

    async def _listen_loop(self, task_id: str, manager: ConnectionManager) -> None:
        """Background coroutine listening on the task's Redis channel."""
        retry_delay = 1.0
        while True:
            try:
                async for event in redis_pubsub.subscribe(task_id):
                    # Forward the decoded event to all connected browser WebSockets
                    await manager.broadcast(task_id, event)
                retry_delay = 1.0
            except asyncio.CancelledError:
                logger.debug("Subscriber task for %s cancelled cleanly.", task_id)
                break
            except Exception as exc:
                logger.warning(
                    "Redis subscriber loop error for task %s: %s (retrying in %.1fs)",
                    task_id,
                    exc,
                    retry_delay,
                )
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2.0, 10.0)

    async def stop_all(self) -> None:
        """Cleanly cancel all active subscriber tasks."""
        async with self._lock:
            tasks_to_cancel = list(self._listener_tasks.values())
            self._listener_tasks.clear()

        for t in tasks_to_cancel:
            if not t.done():
                t.cancel()

        if tasks_to_cancel:
            await asyncio.gather(*tasks_to_cancel, return_exceptions=True)
            logger.info("All Redis subscriber background tasks stopped.")


# Module-level singleton instance
subscriber_manager = TaskSubscriberManager()
