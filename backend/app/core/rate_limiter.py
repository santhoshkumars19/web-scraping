"""
app/core/rate_limiter.py

Sliding-window rate limiter for API endpoints (Scrape Task creation, Leads querying).
Uses Redis with automatic fallback to an in-memory sliding window when Redis is unreachable.
"""

from __future__ import annotations

import time
from typing import Dict, List, Tuple

import redis.asyncio as aioredis
from fastapi import Depends, Request

from app.api.dependencies.auth import get_current_user
from app.core.config import settings
from app.core.exceptions import RateLimitedError
from app.core.logging import get_logger
from app.models.user import User

logger = get_logger(__name__)


class InMemorySlidingWindow:
    """In-memory fallback sliding-window rate limiter."""

    def __init__(self) -> None:
        # key -> list of request timestamps
        self._hits: Dict[str, List[float]] = {}

    def is_rate_limited(self, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
        now = time.time()
        window_start = now - window_seconds
        timestamps = [ts for ts in self._hits.get(key, []) if ts > window_start]

        if len(timestamps) >= max_requests:
            oldest_relevant = timestamps[0]
            retry_after = max(1, int(oldest_relevant + window_seconds - now))
            self._hits[key] = timestamps
            return True, retry_after

        timestamps.append(now)
        self._hits[key] = timestamps
        return False, 0

    def reset(self) -> None:
        self._hits.clear()


class ApiRateLimiter:
    """Redis-backed sliding window rate limiter with in-memory fallback."""

    def __init__(self) -> None:
        self._fallback = InMemorySlidingWindow()
        self._redis_client: aioredis.Redis | None = None
        self._redis_available: bool = True
        self._last_redis_check: float = 0.0

    def _get_redis(self) -> aioredis.Redis | None:
        now = time.time()
        if not self._redis_available and (now - self._last_redis_check < 60.0):
            return None
        self._last_redis_check = now
        if self._redis_client is None:
            try:
                self._redis_client = aioredis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=0.5,
                    socket_timeout=0.5,
                )
            except Exception:
                self._redis_available = False
                return None
        return self._redis_client

    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> Tuple[bool, int]:
        """Returns (is_limited, retry_after_seconds)."""
        r = self._get_redis()
        if r is None:
            return self._fallback.is_rate_limited(key, max_requests, window_seconds)

        try:
            now = time.time()
            window_start = now - window_seconds
            zset_key = f"leadscout:ratelimit:{key}"

            pipe = r.pipeline()
            pipe.zremrangebyscore(zset_key, 0, window_start)
            pipe.zcard(zset_key)
            pipe.zadd(zset_key, {str(now): now})
            pipe.expire(zset_key, window_seconds + 5)
            results = await pipe.execute()

            current_count = results[1]
            if current_count >= max_requests:
                oldest_entries = await r.zrange(zset_key, 0, 0, withscores=True)
                retry_after = 1
                if oldest_entries:
                    oldest_ts = oldest_entries[0][1]
                    retry_after = max(1, int(oldest_ts + window_seconds - now))
                return True, retry_after

            return False, 0
        except Exception as exc:
            logger.debug("Redis rate limit check failed (%s); using in-memory fallback.", exc)
            self._redis_available = False
            return self._fallback.is_rate_limited(key, max_requests, window_seconds)

    def reset_fallback(self) -> None:
        self._fallback.reset()


api_rate_limiter = ApiRateLimiter()


async def check_scrape_task_rate_limit(
    current_user: User = Depends(get_current_user),
) -> None:
    """FastAPI dependency: Enforce task creation rate limit per authenticated user."""
    key = f"scrape_task:{current_user.id}"
    limited, retry_after = await api_rate_limiter.check_rate_limit(
        key=key,
        max_requests=settings.SCRAPE_TASK_RATE_LIMIT,
        window_seconds=settings.SCRAPE_TASK_RATE_WINDOW_SECONDS,
    )
    if limited:
        raise RateLimitedError(
            message=f"Rate limit exceeded: maximum {settings.SCRAPE_TASK_RATE_LIMIT} scraping tasks per hour. "
                    f"Please try again in {retry_after}s.",
            details={"retry_after": retry_after},
        )


async def check_api_rate_limit(
    current_user: User = Depends(get_current_user),
) -> None:
    """FastAPI dependency: Enforce general API query rate limit per authenticated user."""
    key = f"api_general:{current_user.id}"
    limited, retry_after = await api_rate_limiter.check_rate_limit(
        key=key,
        max_requests=settings.API_RATE_LIMIT,
        window_seconds=settings.API_RATE_LIMIT_WINDOW_SECONDS,
    )
    if limited:
        raise RateLimitedError(
            message=f"Rate limit exceeded: maximum {settings.API_RATE_LIMIT} requests per minute. "
                    f"Please try again in {retry_after}s.",
            details={"retry_after": retry_after},
        )
