"""
app/realtime/redis_pubsub.py

Redis Pub/Sub wrapper for distributed task event broadcasting.
Enables Celery workers and multiple FastAPI instances to publish and subscribe
to task event channels across process and server boundaries.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncGenerator

import redis
import redis.asyncio as aioredis
from redis.exceptions import RedisError

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_task_channel(task_id: str) -> str:
    """Generate the Redis Pub/Sub channel name for a task."""
    return f"{settings.REDIS_PUBSUB_PREFIX}:{task_id}"


class RedisPubSub:
    """Handles publishing and subscribing to Redis channels for real-time task notifications."""

    def __init__(self, redis_url: str | None = None) -> None:
        self.redis_url = redis_url or settings.REDIS_URL
        self._async_redis: aioredis.Redis | None = None
        self._sync_redis: redis.Redis | None = None

    def _get_async_client(self) -> aioredis.Redis:
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None

        if self._async_redis is not None:
            client_loop = getattr(self._async_redis, "_loop", None)
            if current_loop and client_loop and (client_loop.is_closed() or client_loop != current_loop):
                self._async_redis = None

        if self._async_redis is None:
            self._async_redis = aioredis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=5.0,
            )
        return self._async_redis

    def _get_sync_client(self) -> redis.Redis:
        if self._sync_redis is None:
            self._sync_redis = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=5.0,
            )
        return self._sync_redis

    async def publish(self, task_id: str, event: dict[str, Any]) -> bool:
        """Publish an event to the task's Redis channel asynchronously."""
        channel = get_task_channel(task_id)
        try:
            client = self._get_async_client()
            payload = json.dumps(event)
            await client.publish(channel, payload)
            logger.debug(
                "REALTIME_EVENT_PUBLISHED: published event '%s' to channel %s",
                event.get("type"),
                channel,
            )
            return True
        except (RedisError, ConnectionError, OSError) as exc:
            logger.warning(
                "REALTIME_PUBLISH_FAILED: could not publish to Redis channel %s: %s",
                channel,
                exc,
            )
            return False

    def publish_sync(self, task_id: str, event: dict[str, Any]) -> bool:
        """Publish an event to the task's Redis channel synchronously (for worker processes)."""
        channel = get_task_channel(task_id)
        try:
            client = self._get_sync_client()
            payload = json.dumps(event)
            client.publish(channel, payload)
            logger.debug(
                "REALTIME_EVENT_PUBLISHED: published event '%s' to channel %s (sync)",
                event.get("type"),
                channel,
            )
            return True
        except (RedisError, ConnectionError, OSError) as exc:
            logger.warning(
                "REALTIME_PUBLISH_FAILED: could not publish to Redis channel %s: %s",
                channel,
                exc,
            )
            return False

    async def subscribe(self, task_id: str) -> AsyncGenerator[dict[str, Any], None]:
        """Subscribe to a task's Redis channel and yield received events as dicts."""
        channel = get_task_channel(task_id)
        client = self._get_async_client()
        pubsub = client.pubsub()
        await pubsub.subscribe(channel)
        logger.info("REALTIME_SUBSCRIBER_STARTED: subscribed to Redis channel %s", channel)

        try:
            async for message in pubsub.listen():
                if message and message.get("type") == "message":
                    raw_data = message.get("data")
                    if isinstance(raw_data, str):
                        try:
                            parsed = json.loads(raw_data)
                            yield parsed
                        except json.JSONDecodeError as err:
                            logger.error("Failed to decode event JSON from channel %s: %s", channel, err)
        finally:
            try:
                await pubsub.unsubscribe(channel)
                await pubsub.close()
            except Exception as e:
                logger.debug("Error unsubscribing from channel %s: %s", channel, e)
            logger.info("REALTIME_SUBSCRIBER_STOPPED: unsubscribed from Redis channel %s", channel)

    async def close(self) -> None:
        """Close Redis connections cleanly."""
        if self._async_redis:
            try:
                await self._async_redis.aclose()
            except Exception:
                pass
            self._async_redis = None

        if self._sync_redis:
            try:
                self._sync_redis.close()
            except Exception:
                pass
            self._sync_redis = None


# Module-level singleton instance
redis_pubsub = RedisPubSub()
