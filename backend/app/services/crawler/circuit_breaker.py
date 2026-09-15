"""
app/services/crawler/circuit_breaker.py

Domain-level circuit breaker to avoid hitting failing or blocking target websites repeatedly.
Tracks consecutive failures per domain and triggers a cooldown period.
"""

from __future__ import annotations

import time
from typing import Dict, Tuple

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class DomainCircuitBreaker:
    """Tracks domain health and trips if consecutive failures exceed threshold."""

    def __init__(
        self,
        failure_threshold: int | None = None,
        cooldown_seconds: int | None = None,
    ) -> None:
        self.failure_threshold = failure_threshold or settings.DOMAIN_FAILURE_THRESHOLD
        self.cooldown_seconds = cooldown_seconds or settings.DOMAIN_COOLDOWN_SECONDS

        # domain -> (consecutive_failures: int, open_until_timestamp: float)
        self._domains: Dict[str, Tuple[int, float]] = {}

    def can_request(self, domain: str) -> bool:
        """Return True if requests are allowed to this domain, False if circuit is OPEN."""
        norm_domain = domain.lower().replace("www.", "")
        info = self._domains.get(norm_domain)
        if not info:
            return True

        failures, open_until = info
        now = time.time()

        if open_until > 0:
            if now < open_until:
                # Circuit is still OPEN
                return False
            else:
                # Cooldown expired, allow retry (half-open)
                self._domains[norm_domain] = (0, 0.0)
                return True

        return failures < self.failure_threshold

    def record_failure(self, domain: str, reason: str = "") -> None:
        """Record an error (403, 429, CAPTCHA, 5xx, timeout)."""
        norm_domain = domain.lower().replace("www.", "")
        now = time.time()
        failures, open_until = self._domains.get(norm_domain, (0, 0.0))

        failures += 1
        if failures >= self.failure_threshold:
            open_until = now + self.cooldown_seconds
            logger.warning(
                "Circuit breaker TRIPPED for domain '%s' after %d consecutive failures (reason: %s). "
                "Cooling down for %ds.",
                norm_domain,
                failures,
                reason,
                self.cooldown_seconds,
            )

        self._domains[norm_domain] = (failures, open_until)

    def record_success(self, domain: str) -> None:
        """Reset consecutive failures on success."""
        norm_domain = domain.lower().replace("www.", "")
        if norm_domain in self._domains:
            self._domains[norm_domain] = (0, 0.0)

    def get_status(self, domain: str) -> Tuple[bool, int, float]:
        """Returns (is_open, consecutive_failures, remaining_cooldown_seconds)."""
        norm_domain = domain.lower().replace("www.", "")
        failures, open_until = self._domains.get(norm_domain, (0, 0.0))
        now = time.time()
        is_open = open_until > now
        remaining = max(0.0, open_until - now) if is_open else 0.0
        return is_open, failures, remaining

    def reset(self) -> None:
        self._domains.clear()


# Global singleton instance for the worker process
domain_circuit_breaker = DomainCircuitBreaker()
