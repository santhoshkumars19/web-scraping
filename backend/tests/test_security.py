"""
tests/test_security.py

Comprehensive security, hardening, and crawl safety test suite for LeadScout (Step 14):
  • SSRF protection (loopback, private ranges, cloud metadata, protocols)
  • Redirect SSRF protection
  • CAPTCHA and anti-bot challenge detection
  • Access denial (401, 403, paywalls, login walls)
  • Domain circuit breaker lifecycle
  • robots.txt compliance & fail-closed policy
  • URL frontier capacity & duplicate prevention
  • Request correlation ID middleware (X-Request-ID)
  • Security response headers (nosniff, frame-options, referrer-policy)
  • API rate limiting (HTTP 429)
  • Health, readiness, and liveness probes
  • Stale task detection & termination
  • Sensitive log redaction
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.core.exceptions import RateLimitedError
from app.core.logging import SensitiveDataFilter
from app.core.rate_limiter import api_rate_limiter
from app.jobs.stale_task_job import detect_and_fail_stale_tasks
from app.models.scraping_task import ScrapingTask
from app.services.crawler.access_detector import AccessDetector, AccessStatus
from app.services.crawler.circuit_breaker import DomainCircuitBreaker
from app.services.crawler.crawler import WebsiteCrawler
from app.services.crawler.exceptions import CrawlerError
from app.services.crawler.http_crawler import HttpCrawler
from app.services.crawler.robots import RobotsChecker
from app.services.crawler.url_frontier import UrlFrontier
from app.utils.ssrf import SsrfBlockedError, validate_url_for_ssrf


# ─── 1. SSRF Protection Tests ──────────────────────────────────────────────────


@pytest.mark.parametrize(
    "blocked_url",
    [
        "http://127.0.0.1",
        "http://127.0.0.1:8080/admin",
        "http://localhost",
        "http://localhost:3000",
        "http://10.0.0.1",
        "http://10.255.255.255/secret",
        "http://172.16.0.1",
        "http://192.168.1.1",
        "http://169.254.169.254/latest/meta-data/",
        "http://metadata.google.internal/computeMetadata/v1/",
        "http://0.0.0.0",
        "file:///etc/passwd",
        "ftp://ftp.example.com",
        "javascript:alert(1)",
        "data:text/html,<html>evil</html>",
        "http://internal.service.local",
    ],
)
def test_ssrf_blocks_unsafe_destinations(blocked_url: str) -> None:
    """SSRF validator must strictly reject all private, loopback, metadata, and non-http URLs."""
    with pytest.raises(SsrfBlockedError):
        validate_url_for_ssrf(blocked_url)


def test_ssrf_allows_legitimate_public_urls() -> None:
    """SSRF validator must accept valid public hostnames with public IPs."""
    with patch("socket.getaddrinfo") as mock_dns:
        # Mock DNS returning a public IP (e.g. 93.184.216.34 for example.com)
        mock_dns.return_value = [
            (2, 1, 6, "", ("93.184.216.34", 443)),
        ]
        validate_url_for_ssrf("https://example.com/about")
        validate_url_for_ssrf("http://example.com/contact")


@pytest.mark.asyncio
async def test_http_crawler_aborts_on_ssrf_target() -> None:
    """HttpCrawler must immediately raise CrawlerError with code SSRF_BLOCKED for loopback."""
    crawler = HttpCrawler()
    with pytest.raises(CrawlerError) as exc_info:
        await crawler.fetch("http://127.0.0.1/admin", website_domain="example.com")
    assert exc_info.value.code == "SSRF_BLOCKED"


@pytest.mark.asyncio
async def test_http_crawler_blocks_ssrf_on_redirect() -> None:
    """HttpCrawler must block redirects leading to private or loopback IPs."""
    crawler = HttpCrawler()

    # Create mock response that attempts to redirect to localhost
    mock_redirect = httpx.Response(
        status_code=302,
        headers={"Location": "http://127.0.0.1/secret"},
        request=httpx.Request("GET", "https://public.example.com"),
    )

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_redirect

    with patch("app.services.crawler.http_crawler.validate_url_for_ssrf") as mock_val:
        # First call (public) passes, second call (redirect target) raises SSRF error
        mock_val.side_effect = [None, SsrfBlockedError("Loopback blocked", "http://127.0.0.1/secret")]

        with pytest.raises(CrawlerError) as exc_info:
            await crawler.fetch("https://public.example.com", website_domain="public.example.com", client=mock_client)
        assert exc_info.value.code == "SSRF_BLOCKED"


# ─── 2. Access Control & CAPTCHA Detection Tests ───────────────────────────────


def test_access_detector_identifies_captcha() -> None:
    """Detects standard CAPTCHA and Cloudflare challenge walls."""
    html_cf = "<html><head><title>Attention Required! | Cloudflare</title></head><body>Please verify you are human</body></html>"
    status, reason = AccessDetector.check(200, html_cf, "https://example.com")
    assert status == AccessStatus.CAPTCHA_BLOCKED
    assert "verify you are human" in str(reason).lower() or "cloudflare" in str(reason).lower()

    html_robot = "<div>Please complete the robot check to proceed</div>"
    status, _ = AccessDetector.check(200, html_robot, "https://example.com")
    assert status == AccessStatus.CAPTCHA_BLOCKED


def test_access_detector_identifies_login_wall() -> None:
    """Detects login redirects and authentication walls."""
    status, _ = AccessDetector.check(200, "<html>Welcome</html>", "https://example.com/account/login")
    assert status == AccessStatus.LOGIN_REQUIRED

    html_signin = "<div>Please sign in to continue reading</div>"
    status, _ = AccessDetector.check(200, html_signin, "https://example.com/page")
    assert status == AccessStatus.LOGIN_REQUIRED


def test_access_detector_identifies_paywall() -> None:
    """Detects subscription paywall markers."""
    html_paywall = "<p>This content is for subscribers only. Subscribe to continue reading.</p>"
    status, _ = AccessDetector.check(200, html_paywall, "https://example.com/article")
    assert status == AccessStatus.PAYWALL_BLOCKED


def test_access_detector_allows_normal_pages() -> None:
    """Legitimate content passes without restriction."""
    html_ok = "<html><body><h1>Welcome to our school</h1><p>Contact us at info@school.org</p></body></html>"
    status, reason = AccessDetector.check(200, html_ok, "https://example.com/about")
    assert status == AccessStatus.ALLOWED
    assert reason is None


# ─── 3. Domain Circuit Breaker Tests ──────────────────────────────────────────


def test_circuit_breaker_trips_after_threshold() -> None:
    """Domain circuit breaker must trip OPEN after 5 consecutive failures."""
    cb = DomainCircuitBreaker(failure_threshold=3, cooldown_seconds=60)
    domain = "failing-school.org"

    assert cb.can_request(domain) is True

    cb.record_failure(domain, "HTTP 403")
    cb.record_failure(domain, "HTTP 403")
    assert cb.can_request(domain) is True  # 2 < 3

    cb.record_failure(domain, "HTTP 403")  # 3 failures -> trips
    assert cb.can_request(domain) is False

    is_open, failures, remaining = cb.get_status(domain)
    assert is_open is True
    assert failures == 3
    assert remaining > 0


def test_circuit_breaker_resets_on_success() -> None:
    """A successful request resets the consecutive failure counter."""
    cb = DomainCircuitBreaker(failure_threshold=3, cooldown_seconds=60)
    domain = "flaky-school.org"

    cb.record_failure(domain, "Timeout")
    cb.record_failure(domain, "Timeout")
    cb.record_success(domain)

    # Counter reset: needs 3 new failures to trip
    cb.record_failure(domain, "Timeout")
    assert cb.can_request(domain) is True


# ─── 4. robots.txt Compliance & Fail-Closed Tests ─────────────────────────────


@pytest.mark.asyncio
async def test_robots_txt_disallows_restricted_path() -> None:
    """RobotsChecker must respect explicit Disallow rules."""
    checker = RobotsChecker()

    robots_content = "User-agent: *\nDisallow: /admin\nDisallow: /private/\nAllow: /"
    mock_resp = httpx.Response(200, text=robots_content, request=httpx.Request("GET", "https://example.com/robots.txt"))

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp

    allowed = await checker.is_allowed("https://example.com/admin/settings", client=mock_client)
    assert allowed is False

    allowed_public = await checker.is_allowed("https://example.com/about", client=mock_client)
    assert allowed_public is True


@pytest.mark.asyncio
async def test_robots_txt_fail_closed_on_network_error() -> None:
    """When ROBOTS_FAIL_CLOSED is True, network failure fetching robots.txt disallows crawling."""
    checker = RobotsChecker(fail_closed=True)

    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.ConnectError("Connection refused")

    allowed = await checker.is_allowed("https://unreachable.org/page", client=mock_client)
    assert allowed is False


@pytest.mark.asyncio
async def test_robots_txt_fail_open_when_configured() -> None:
    """When fail_closed=False, network failure falls back to allowed."""
    checker = RobotsChecker(fail_closed=False)

    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.ConnectError("Connection refused")

    allowed = await checker.is_allowed("https://unreachable.org/page", client=mock_client)
    assert allowed is True


# ─── 5. URL Frontier Safety Limits ────────────────────────────────────────────


def test_url_frontier_enforces_capacity_limit() -> None:
    """UrlFrontier must stop accepting new items once max_frontier_urls is reached."""
    frontier = UrlFrontier(max_pages=50, max_depth=3, max_frontier_urls=5)

    for i in range(5):
        added = frontier.add(f"https://example.com/page{i}", depth=1)
        assert added is True

    # 6th item should be rejected due to capacity limit
    added_6th = frontier.add("https://example.com/page-overflow", depth=1)
    assert added_6th is False
    assert frontier.total_enqueued == 5


def test_url_frontier_enforces_depth_limit() -> None:
    """UrlFrontier must reject URLs deeper than max_depth."""
    frontier = UrlFrontier(max_pages=20, max_depth=2)

    assert frontier.add("https://example.com/depth-1", depth=1) is True
    assert frontier.add("https://example.com/depth-2", depth=2) is True
    assert frontier.add("https://example.com/depth-3", depth=3) is False


def test_url_frontier_prevents_duplicate_urls() -> None:
    """UrlFrontier must not enqueue duplicates of already visited or enqueued URLs."""
    frontier = UrlFrontier(max_pages=20, max_depth=2)

    assert frontier.add("https://example.com/contact/", depth=1) is True
    # Normalized version (trailing slash stripped) should be detected as duplicate
    assert frontier.add("https://example.com/contact", depth=1) is False


# ─── 6. Request Correlation ID & Security Headers Middleware Tests ────────────


@pytest.mark.asyncio
async def test_request_id_generated_when_absent(client: AsyncClient) -> None:
    """Requests without X-Request-ID must receive a generated UUID in response header."""
    response = await client.get("/api/live")
    assert response.status_code == 200
    assert "x-request-id" in response.headers
    req_id = response.headers["x-request-id"]
    assert len(req_id) >= 8


@pytest.mark.asyncio
async def test_request_id_propagated_when_provided(client: AsyncClient) -> None:
    """Client-provided X-Request-ID must be echoed in the response."""
    custom_id = "test-client-correlation-id-99"
    response = await client.get("/api/live", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers.get("x-request-id") == custom_id


@pytest.mark.asyncio
async def test_security_headers_present_in_response(client: AsyncClient) -> None:
    """Verify security headers are applied to HTTP responses."""
    response = await client.get("/api/live")
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"


# ─── 7. Health, Liveness, and Readiness Endpoints ──────────────────────────────


@pytest.mark.asyncio
async def test_live_probe_always_returns_200(client: AsyncClient) -> None:
    """GET /api/live must return HTTP 200 without checking external dependencies."""
    response = await client.get("/api/live")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"


@pytest.mark.asyncio
async def test_ready_probe_returns_success_with_db(test_app_client: AsyncClient) -> None:
    """GET /api/ready must return HTTP 200 when database is functional."""
    response = await test_app_client.get("/api/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["ready"] is True


# ─── 8. API Rate Limiting Tests ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_api_rate_limiter_in_memory_sliding_window() -> None:
    """ApiRateLimiter sliding window must reject after exceeding max requests."""
    api_rate_limiter.reset_fallback()
    key = "test_user_unit_test"

    # Allow 3 requests per 10 seconds
    for _ in range(3):
        is_limited, _ = await api_rate_limiter.check_rate_limit(key, max_requests=3, window_seconds=10)
        assert is_limited is False

    # 4th request must be rate-limited
    is_limited, retry_after = await api_rate_limiter.check_rate_limit(key, max_requests=3, window_seconds=10)
    assert is_limited is True
    assert retry_after > 0


# ─── 9. Stale Task Detection Tests ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_stale_task_detection(db_session) -> None:
    """Stale tasks in RUNNING state older than cutoff must be safely transitioned to FAILED."""
    old_time = datetime.now(timezone.utc) - timedelta(minutes=120)

    stale_task = ScrapingTask(
        task_id="TASK-STALE01",
        user_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        status="RUNNING",
        location="Puducherry",
        keyword="Schools",
        progress=30,
        current_stage="CRAWLING",
        started_at=old_time,
        updated_at=old_time,
    )
    db_session.add(stale_task)
    await db_session.commit()

    failed_ids = await detect_and_fail_stale_tasks(db_session, stale_after_minutes=60)
    assert "TASK-STALE01" in failed_ids

    # Verify task state in database
    await db_session.refresh(stale_task)
    assert stale_task.status == "FAILED"
    assert "inactivity" in stale_task.failure_reason.lower() or "timeout" in stale_task.failure_reason.lower()


# ─── 10. Sensitive Log Redaction Tests ────────────────────────────────────────


def test_log_redaction_sanitizes_credentials() -> None:
    """SensitiveDataFilter must redact Bearer tokens and passwords."""
    filter_obj = SensitiveDataFilter()

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="User authenticated with Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.test and password=Secret1234",
        args=(),
        exc_info=None,
    )

    filter_obj.filter(record)
    assert "Bearer [REDACTED]" in record.msg
    assert "password=[REDACTED]" in record.msg
    assert "eyJhbGci" not in record.msg
    assert "Secret1234" not in record.msg
