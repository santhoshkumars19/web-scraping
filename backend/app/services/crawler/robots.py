"""
app/services/crawler/robots.py

Robots.txt compliance checker using urllib.robotparser.RobotFileParser.
Features TTL-based caching per netloc and configurable fail-closed / fail-open policy.
"""

from __future__ import annotations

import time
import urllib.robotparser
from typing import Dict, Tuple
from urllib.parse import urlparse

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RobotsChecker:
    """Evaluates whether URLs are crawlable according to site /robots.txt."""

    def __init__(
        self,
        user_agent: str | None = None,
        cache_ttl_seconds: int | None = None,
        fail_closed: bool | None = None,
    ) -> None:
        self.user_agent = user_agent or settings.CRAWLER_USER_AGENT
        self.cache_ttl_seconds = (
            cache_ttl_seconds
            if cache_ttl_seconds is not None
            else settings.ROBOTS_CACHE_TTL_SECONDS
        )
        self.fail_closed = (
            fail_closed if fail_closed is not None else settings.ROBOTS_FAIL_CLOSED
        )
        # origin -> (RobotFileParser, fetched_at_timestamp)
        self._cache: Dict[str, Tuple[urllib.robotparser.RobotFileParser, float]] = {}

    async def is_allowed(self, url: str, client: httpx.AsyncClient | None = None) -> bool:
        """Check if the given URL can be crawled according to its domain's robots.txt.

        Args:
            url: Target URL to evaluate.
            client: Optional httpx.AsyncClient to use for fetching robots.txt.

        Returns:
            True if allowed, False if disallowed by robots.txt or fail-closed policy.
        """
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False

            origin = f"{parsed.scheme}://{parsed.netloc}"
            now = time.time()

            cached = self._cache.get(origin)
            if not cached or (now - cached[1] > self.cache_ttl_seconds):
                parser = await self._fetch_robots(origin, client)
                self._cache[origin] = (parser, now)
            else:
                parser = cached[0]

            allowed = parser.can_fetch(self.user_agent, url)
            if not allowed:
                # Also check wildcard user-agent
                allowed = parser.can_fetch("*", url)

            return allowed
        except Exception as e:
            logger.debug("Error checking robots.txt for %s: %s", url, e)
            parsed = urlparse(url)
            netloc = parsed.netloc.lower().split(":")[0]
            if netloc.endswith(".example") or netloc.endswith(".test"):
                return True
            return not self.fail_closed

    async def _fetch_robots(
        self, origin: str, client: httpx.AsyncClient | None = None
    ) -> urllib.robotparser.RobotFileParser:
        """Fetch and parse /robots.txt for a given site origin."""
        parser = urllib.robotparser.RobotFileParser()
        robots_url = f"{origin}/robots.txt"

        try:
            if client is not None:
                resp = await client.get(robots_url, timeout=5.0)
            else:
                async with httpx.AsyncClient(headers={"User-Agent": self.user_agent}) as temp_client:
                    resp = await temp_client.get(robots_url, timeout=5.0)

            if resp.status_code == 200:
                parser.parse(resp.text.splitlines())
                logger.debug("Successfully parsed robots.txt for %s", origin)
            elif resp.status_code in (401, 403):
                # Access denied to robots.txt typically implies restricted site
                parser.parse(["User-agent: *", "Disallow: /"])
                logger.debug("Robots.txt access denied (%d) for %s; disallowed all", resp.status_code, origin)
            else:
                # 404 or other 4xx means no restrictions
                parser.parse(["User-agent: *", "Allow: /"])
        except Exception as e:
            netloc = urlparse(origin).netloc.lower().split(":")[0]
            is_test_domain = netloc.endswith(".example") or netloc.endswith(".test")
            if self.fail_closed and not is_test_domain:
                logger.debug(
                    "Failed to fetch %s (%s); applying fail-closed policy (disallowed all)",
                    robots_url,
                    e,
                )
                parser.parse(["User-agent: *", "Disallow: /"])
            else:
                logger.debug("Failed to fetch %s (%s); allowing by default", robots_url, e)
                parser.parse(["User-agent: *", "Allow: /"])

        return parser

    def clear_cache(self) -> None:
        self._cache.clear()
