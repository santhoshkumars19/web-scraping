"""
app/services/crawler/http_crawler.py

Level 1 HTTP fetcher using HTTPX.
Enforces SSRF protection, content-type validation, max response size, domain redirects,
timeouts, and bounded exponential backoff with jitter.
"""

from __future__ import annotations

import asyncio
import random
import time
from urllib.parse import urlparse

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.services.crawler.exceptions import (
    AccessDeniedError,
    CrawlerError,
    DomainNotAllowedError,
    FetchTimeoutError,
    NonHtmlContentError,
    RateLimitedError,
    RedirectLimitError,
    ResponseTooLargeError,
)
from app.utils.ssrf import SsrfBlockedError, validate_url_for_ssrf
from app.utils.url import extract_domain

logger = get_logger(__name__)

ALLOWED_CONTENT_TYPES = ("text/html", "application/xhtml+xml")
RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}


class HttpCrawler:
    """Level 1 direct HTTP crawler using httpx."""

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        timeout: float | None = None,
        max_response_size_bytes: int | None = None,
        max_redirects: int | None = None,
        max_retries: int | None = None,
    ) -> None:
        self._client = client
        self.timeout = timeout or settings.HTTP_TIMEOUT_SECONDS
        self.max_response_size_bytes = max_response_size_bytes or (
            settings.MAX_RESPONSE_SIZE_MB * 1024 * 1024
        )
        self.max_redirects = max_redirects or settings.MAX_REDIRECTS
        self.max_retries = max_retries or settings.MAX_RETRIES

    async def fetch(
        self,
        url: str,
        website_domain: str,
        client: httpx.AsyncClient | None = None,
    ) -> tuple[str, str, int, str, float]:
        """Fetch a page via HTTP GET.

        Args:
            url: Target URL to fetch.
            website_domain: Target website domain for redirect boundary validation.
            client: Optional injected httpx client (e.g. for mock testing or shared sessions).

        Returns:
            Tuple: (html_text, final_url, status_code, content_type, response_time_ms)
        """
        active_client = client or self._client
        if active_client is not None:
            return await self._fetch_with_client(active_client, url, website_domain)

        async with httpx.AsyncClient(
            headers={
                "User-Agent": settings.CRAWLER_USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
            timeout=self.timeout,
            follow_redirects=False,
        ) as session_client:
            return await self._fetch_with_client(session_client, url, website_domain)

    async def _fetch_with_client(
        self,
        client: httpx.AsyncClient,
        url: str,
        website_domain: str,
    ) -> tuple[str, str, int, str, float]:
        current_url = url
        redirect_count = 0
        start_time = time.monotonic()

        while True:
            # 1. SSRF check on every URL hop
            try:
                validate_url_for_ssrf(current_url)
            except SsrfBlockedError as exc:
                logger.warning("SSRF blocked URL: %s (%s)", current_url, exc.reason)
                raise CrawlerError(
                    message=f"SSRF blocked: {exc.reason}",
                    status_code=400,
                    code="SSRF_BLOCKED",
                    url=current_url,
                ) from exc

            # 2. Domain check on each redirect hop
            target_domain = extract_domain(current_url)
            if target_domain and not self._is_domain_match(target_domain, website_domain):
                raise DomainNotAllowedError(
                    message=f"Redirected off-domain to {target_domain}",
                    url=current_url,
                )

            response = await self._send_with_retry(client, current_url)

            # Handle redirects manually to enforce boundaries, SSRF check, and hop limits
            if response.is_redirect:
                redirect_count += 1
                if redirect_count > self.max_redirects:
                    raise RedirectLimitError(
                        message=f"Exceeded max redirects ({self.max_redirects})",
                        url=current_url,
                    )

                redirect_target = response.headers.get("Location")
                if not redirect_target:
                    raise RedirectLimitError(
                        message="Redirect response missing Location header",
                        url=current_url,
                    )

                # Resolve relative redirect URLs
                current_url = str(response.url.join(redirect_target))
                continue

            # Check status code
            status = response.status_code
            if status in (401, 403):
                raise AccessDeniedError(
                    message=f"HTTP {status} Forbidden/Unauthorized",
                    status_code=status,
                    url=current_url,
                )
            elif status == 429:
                raise RateLimitedError(message="HTTP 429 Too Many Requests", url=current_url)
            elif status == 404:
                raise CrawlerError(
                    message="HTTP 404 Not Found",
                    status_code=404,
                    code="NOT_FOUND",
                    url=current_url,
                )
            elif status >= 400:
                raise CrawlerError(
                    message=f"HTTP {status} Error",
                    status_code=status,
                    code="HTTP_ERROR",
                    url=current_url,
                )

            # Check Content-Type
            content_type_header = response.headers.get("Content-Type", "").lower()
            content_type = content_type_header.split(";")[0].strip()
            if content_type and not any(
                content_type.startswith(allowed) for allowed in ALLOWED_CONTENT_TYPES
            ):
                raise NonHtmlContentError(
                    message=f"Rejected non-HTML Content-Type: {content_type}",
                    url=current_url,
                )

            # Check response size
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > self.max_response_size_bytes:
                raise ResponseTooLargeError(
                    message=f"Content-Length {content_length} bytes exceeds limit of {self.max_response_size_bytes}",
                    url=current_url,
                )

            content_bytes = response.content
            if len(content_bytes) > self.max_response_size_bytes:
                raise ResponseTooLargeError(
                    message=f"Response body {len(content_bytes)} bytes exceeds limit",
                    url=current_url,
                )

            elapsed_ms = (time.monotonic() - start_time) * 1000.0
            html_text = response.text

            return html_text, str(response.url), status, content_type or "text/html", elapsed_ms

    async def _send_with_retry(self, client: httpx.AsyncClient, url: str) -> httpx.Response:
        attempts = 0
        last_err: Exception | None = None

        while attempts <= self.max_retries:
            try:
                response = await client.get(url, timeout=self.timeout)

                # Check if response status is transiently retryable
                if response.status_code in RETRYABLE_STATUS_CODES and attempts < self.max_retries:
                    attempts += 1
                    delay = self._compute_backoff(attempts, response.headers.get("Retry-After"))
                    logger.debug(
                        "Received HTTP %d from %s; backing off for %.2fs (attempt %d/%d)",
                        response.status_code,
                        url,
                        delay,
                        attempts,
                        self.max_retries,
                    )
                    await asyncio.sleep(delay)
                    continue

                return response

            except (httpx.TimeoutException, httpx.ConnectTimeout, httpx.ReadTimeout) as e:
                attempts += 1
                last_err = e
                if attempts <= self.max_retries:
                    delay = self._compute_backoff(attempts)
                    await asyncio.sleep(delay)
            except (httpx.ConnectError, httpx.NetworkError) as e:
                attempts += 1
                last_err = e
                if attempts <= self.max_retries:
                    delay = self._compute_backoff(attempts)
                    await asyncio.sleep(delay)
            except Exception:
                raise

        raise FetchTimeoutError(
            message=f"Failed to fetch {url} after {self.max_retries + 1} attempts: {last_err}",
            url=url,
        )

    @staticmethod
    def _compute_backoff(attempt: int, retry_after_header: str | None = None) -> float:
        """Compute bounded exponential backoff with random jitter (0–500ms).

        Respects Retry-After header if safely integer-formatted, up to 10 seconds max.
        """
        if retry_after_header:
            try:
                val = float(retry_after_header)
                return min(10.0, max(0.5, val))
            except ValueError:
                pass

        # Exponential: 1s, 2s, 4s... capped at 10s + 0-500ms jitter
        base = min(10.0, float(2 ** (attempt - 1)))
        jitter = random.uniform(0.0, 0.5)
        return min(10.0, base + jitter)

    @staticmethod
    def _is_domain_match(target_domain: str, base_domain: str) -> bool:
        t = target_domain.lower().replace("www.", "")
        b = base_domain.lower().replace("www.", "")
        return t == b
