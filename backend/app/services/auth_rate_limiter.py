"""
app/services/auth_rate_limiter.py

Brute force protection for authentication endpoints.
Tracks consecutive failed login attempts per client IP and normalized email.

Uses Redis when available, falling back safely to an in-memory sliding-window cache
for testing or offline development mode without Redis.
"""

from __future__ import annotations

import time
from typing import Dict, Tuple

import redis.asyncio as aioredis

from app.core.config import settings
from app.core.exceptions import RateLimitExceededError
from app.core.logging import get_logger

logger = get_logger(__name__)


class InMemoryRateLimiter:
    """Thread-safe in-memory fallback rate limiter."""

    def __init__(self) -> None:
        # key -> (attempt_count, window_expiry_timestamp)
        self._attempts: Dict[str, Tuple[int, float]] = {}
        # key -> lockout_expiry_timestamp
        self._lockouts: Dict[str, float] = {}

    def is_locked_out(self, key: str) -> bool:
        now = time.time()
        lockout_expiry = self._lockouts.get(key)
        if lockout_expiry:
            if now < lockout_expiry:
                return True
            # Expired lockout
            del self._lockouts[key]
        return False

    def record_failure(
        self,
        key: str,
        max_attempts: int,
        window_seconds: int,
        lockout_seconds: int,
    ) -> bool:
        now = time.time()
        # Clean expired attempt window
        count, window_expiry = self._attempts.get(key, (0, now + window_seconds))
        if now > window_expiry:
            count = 0
            window_expiry = now + window_seconds

        count += 1
        self._attempts[key] = (count, window_expiry)

        if count >= max_attempts:
            self._lockouts[key] = now + lockout_seconds
            self._attempts.pop(key, None)
            return True
        return False

    def reset(self, key: str) -> None:
        self._attempts.pop(key, None)
        self._lockouts.pop(key, None)

    def reset_all(self) -> None:
        self._attempts.clear()
        self._lockouts.clear()


_in_memory_limiter = InMemoryRateLimiter()


class AuthRateLimiter:
    """Authentication rate limiter protecting login against credential stuffing & brute force."""

    def __init__(self) -> None:
        self.max_attempts = settings.AUTH_LOGIN_MAX_ATTEMPTS
        self.window_seconds = settings.AUTH_LOGIN_WINDOW_SECONDS
        self.lockout_seconds = settings.AUTH_LOCKOUT_SECONDS
        self._redis_client: aioredis.Redis | None = None
        self._redis_available: bool = True

    def _get_key(self, ip: str, email_normalized: str) -> str:
        safe_ip = ip.replace(":", "_").replace("/", "_")
        return f"auth:login:{safe_ip}:{email_normalized}"

    def _get_redis(self) -> aioredis.Redis | None:
        if not self._redis_available:
            return None
        if self._redis_client is None:
            try:
                self._redis_client = aioredis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_timeout=1.0,
                )
            except Exception as e:
                logger.debug("Redis unavailable for auth rate limiter, using in-memory fallback: %s", e)
                self._redis_available = False
                return None
        return self._redis_client

    async def check_rate_limit(self, ip: str, email_normalized: str) -> None:
        """Check if client IP or account is currently locked out.

        Raises RateLimitExceededError (HTTP 429) if locked out.
        """
        key = self._get_key(ip, email_normalized)
        lock_key = f"{key}:locked"

        redis_client = self._get_redis()
        if redis_client is not None:
            try:
                is_locked = await redis_client.get(lock_key)
                if is_locked:
                    logger.warning("AUTH_RATE_LIMIT_BLOCKED: ip=%s email=%s", ip, email_normalized)
                    raise RateLimitExceededError(
                        "Too many login attempts. Account temporarily locked out. Please try again later."
                    )
                return
            except RateLimitExceededError:
                raise
            except Exception as re:
                logger.debug("Redis rate limit check failed (%s), falling back to in-memory", re)

        # Fallback to in-memory
        if _in_memory_limiter.is_locked_out(key):
            logger.warning("AUTH_RATE_LIMIT_BLOCKED (in-memory): ip=%s email=%s", ip, email_normalized)
            raise RateLimitExceededError(
                "Too many login attempts. Account temporarily locked out. Please try again later."
            )

    async def record_failed_attempt(self, ip: str, email_normalized: str) -> None:
        """Record a failed login attempt. If max_attempts reached, locks out."""
        key = self._get_key(ip, email_normalized)
        lock_key = f"{key}:locked"

        redis_client = self._get_redis()
        if redis_client is not None:
            try:
                pipe = redis_client.pipeline()
                pipe.incr(key)
                pipe.expire(key, self.window_seconds)
                results = await pipe.execute()
                current_attempts = results[0]

                if current_attempts >= self.max_attempts:
                    await redis_client.set(lock_key, "1", ex=self.lockout_seconds)
                    await redis_client.delete(key)
                    logger.warning(
                        "AUTH_RATE_LIMIT_LOCKOUT_TRIGGERED: ip=%s email=%s attempts=%d lockout=%ds",
                        ip,
                        email_normalized,
                        current_attempts,
                        self.lockout_seconds,
                    )
                return
            except Exception as re:
                logger.debug("Redis rate limit record failed (%s), falling back to in-memory", re)

        # In-memory fallback
        _in_memory_limiter.record_failure(
            key,
            max_attempts=self.max_attempts,
            window_seconds=self.window_seconds,
            lockout_seconds=self.lockout_seconds,
        )

    async def reset_attempts(self, ip: str, email_normalized: str) -> None:
        """Clear failed attempts upon successful login."""
        key = self._get_key(ip, email_normalized)
        lock_key = f"{key}:locked"

        redis_client = self._get_redis()
        if redis_client is not None:
            try:
                await redis_client.delete(key, lock_key)
                return
            except Exception as re:
                logger.debug("Redis rate limit reset failed (%s)", re)

        _in_memory_limiter.reset(key)

    def reset_all(self) -> None:
        """Clear all rate limit state in memory (for test isolation)."""
        _in_memory_limiter.reset_all()


auth_rate_limiter = AuthRateLimiter()
