"""
app/services/crawler/domain_rate_limiter.py

Distributed domain-level rate limiting and concurrency enforcement using Redis
with automatic in-memory fallback. Enforces politeness delays across all worker processes.
"""

from __future__ import annotations

import asyncio
import time
from typing import Dict

import redis.asyncio as aioredis

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class DomainRateLimiter:
    """Enforces minimum interval between consecutive requests to the same domain."""

    def __init__(self, delay_seconds: float | None = None) -> None:
        self.delay_seconds = (
            delay_seconds if delay_seconds is not None else settings.CRAWL_DELAY_SECONDS
        )
        self._local_last_request: Dict[str, float] = {}
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

    async def acquire(self, domain: str) -> None:
        """Wait until politeness delay has elapsed for this domain, then mark requested."""
        if self.delay_seconds <= 0:
            return

        norm_domain = domain.lower().replace("www.", "")
        r = self._get_redis()

        if r is not None:
            try:
                key = f"leadscout:rate:{norm_domain}"
                last_ts_str = await r.get(key)
                now = time.time()

                if last_ts_str:
                    elapsed = now - float(last_ts_str)
                    remaining = self.delay_seconds - elapsed
                    if remaining > 0:
                        logger.debug("Domain %s rate limited, waiting %.2fs", norm_domain, remaining)
                        await asyncio.sleep(remaining)

                # Record current timestamp with a short TTL (delay_seconds * 2 + 1)
                ttl = max(2, int(self.delay_seconds * 2) + 1)
                await r.set(key, str(time.time()), ex=ttl)
                return

            except Exception as exc:
                logger.debug("Redis domain rate limiter fallback (%s)", exc)
                self._redis_available = False

        # In-memory fallback
        now = time.time()
        last_time = self._local_last_request.get(norm_domain, 0.0)
        elapsed = now - last_time
        remaining = self.delay_seconds - elapsed
        if remaining > 0:
            await asyncio.sleep(remaining)
        self._local_last_request[norm_domain] = time.time()


domain_rate_limiter = DomainRateLimiter()
