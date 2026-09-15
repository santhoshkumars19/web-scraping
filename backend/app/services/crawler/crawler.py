"""
app/services/crawler/crawler.py

Orchestrator for crawling a single Website.
Manages the URL frontier, Level 1 HTTP fetch, Level 2 Playwright fallback,
link extraction, robots.txt checks, domain rate limiting, circuit breaker, and politeness delays.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from datetime import datetime, timezone
from typing import Callable, Coroutine

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.crawler import FetchedPage, WebsiteCrawlResult
from app.services.crawler.access_detector import AccessDetector, AccessStatus
from app.services.crawler.circuit_breaker import domain_circuit_breaker
from app.services.crawler.domain_rate_limiter import domain_rate_limiter
from app.services.crawler.exceptions import AccessDeniedError, CrawlerError, RobotsDisallowedError
from app.services.crawler.http_crawler import HttpCrawler
from app.services.crawler.link_extractor import LinkExtractor
from app.services.crawler.page_classifier import PageClassifier
from app.services.crawler.playwright_crawler import PlaywrightCrawler
from app.services.crawler.robots import RobotsChecker
from app.services.crawler.url_frontier import UrlFrontier
from app.utils.url import extract_domain, normalize_url

logger = get_logger(__name__)


class WebsiteCrawler:
    """Orchestrates the crawling lifecycle for an individual Website."""

    def __init__(
        self,
        http_crawler: HttpCrawler | None = None,
        playwright_crawler: PlaywrightCrawler | None = None,
        robots_checker: RobotsChecker | None = None,
        crawl_delay: float | None = None,
    ) -> None:
        self.http_crawler = http_crawler or HttpCrawler()
        self.playwright_crawler = playwright_crawler or PlaywrightCrawler()
        self.robots_checker = robots_checker or RobotsChecker()
        self.crawl_delay = settings.CRAWL_DELAY_SECONDS if crawl_delay is None else crawl_delay

    async def crawl(
        self,
        website_id: uuid.UUID,
        root_url: str,
        max_pages: int = 15,
        max_depth: int = 2,
        follow_internal_links: bool = True,
        prioritize_contact: bool = True,
        prioritize_about: bool = True,
        prioritize_admissions: bool = False,
        prioritize_staff_management: bool = False,
        allow_subdomains: bool = False,
        on_event: Callable[[str, str, str | None], Coroutine] | None = None,
    ) -> WebsiteCrawlResult:
        """Crawl a single website starting from root_url within domain boundaries."""
        start_time = time.monotonic()
        website_domain = extract_domain(root_url)
        if not website_domain:
            return WebsiteCrawlResult(
                website_id=website_id,
                url=root_url,
                status="FAILED",
                error_reason="Could not extract domain from URL",
                duration_seconds=0.0,
            )

        # ── 0. Circuit Breaker Check ──────────────────────────────────────────
        if not domain_circuit_breaker.can_request(website_domain):
            is_open, failures, remaining = domain_circuit_breaker.get_status(website_domain)
            msg = f"Circuit breaker is OPEN for {website_domain} ({failures} failures, {remaining:.0f}s cooldown remaining)."
            logger.warning(msg)
            if on_event:
                await on_event("CIRCUIT_OPEN", msg, root_url)
            return WebsiteCrawlResult(
                website_id=website_id,
                url=root_url,
                domain=website_domain,
                status="FAILED",
                error_reason=msg,
                duration_seconds=0.0,
            )

        frontier = UrlFrontier(
            max_pages=max_pages,
            max_depth=max_depth,
            prioritize_contact=prioritize_contact,
            prioritize_about=prioritize_about,
            prioritize_admissions=prioritize_admissions,
            prioritize_staff_management=prioritize_staff_management,
            max_frontier_urls=settings.MAX_FRONTIER_URLS,
        )

        frontier.add(root_url, depth=0, tentative_type="HOME")

        pages_crawled: list[FetchedPage] = []
        playwright_used_count = 0
        is_blocked = False
        last_error_reason: str | None = None

        while frontier.has_more():
            item = frontier.pop()
            if not item:
                break

            # 1. Robots.txt check
            try:
                allowed = await self.robots_checker.is_allowed(
                    item.url, client=self.http_crawler._client
                )
                if not allowed:
                    frontier.mark_visited(item.normalized_url)
                    if on_event:
                        await on_event(
                            "ROBOTS_DISALLOWED",
                            f"robots.txt disallowed crawling of {item.url}",
                            item.url,
                        )
                    continue
            except Exception as e:
                logger.debug("Error checking robots.txt for %s: %s", item.url, e)

            # 2. Mark visited in frontier
            frontier.mark_visited(item.normalized_url)

            if on_event:
                await on_event("PAGE_CRAWL_STARTED", f"Fetching {item.url}", item.url)

            # 3. Domain Rate Limiter Check (Politeness)
            await domain_rate_limiter.acquire(website_domain)

            # 4. Level 1 HTTP Fetch
            level_used = "HTTPX"
            try:
                html, final_url, status_code, content_type, elapsed_ms = await self.http_crawler.fetch(
                    url=item.url,
                    website_domain=website_domain,
                )
            except AccessDeniedError as e:
                logger.warning("Access denied (%d) for %s", e.status_code, item.url)
                last_error_reason = f"Access denied: {e.message}"
                domain_circuit_breaker.record_failure(website_domain, e.message)
                if item.depth == 0:
                    is_blocked = True
                if on_event:
                    await on_event("ACCESS_DENIED", e.message, item.url)
                continue
            except CrawlerError as e:
                logger.warning("Crawler error for %s: %s", item.url, e.message)
                last_error_reason = e.message
                domain_circuit_breaker.record_failure(website_domain, e.message)
                if on_event:
                    await on_event(e.code, e.message, item.url)
                continue
            except Exception as e:
                logger.error("Unexpected error fetching %s: %s", item.url, e)
                last_error_reason = str(e)
                domain_circuit_breaker.record_failure(website_domain, str(e))
                if on_event:
                    await on_event("FETCH_FAILED", f"Unexpected error: {e}", item.url)
                continue

            # 5. Access Control & CAPTCHA Detection
            access_status, restriction_reason = AccessDetector.check(
                status_code=status_code,
                html=html,
                final_url=final_url,
            )
            if access_status != AccessStatus.ALLOWED:
                logger.warning(
                    "Access restriction (%s) detected for %s: %s",
                    access_status.value,
                    item.url,
                    restriction_reason,
                )
                domain_circuit_breaker.record_failure(website_domain, access_status.value)
                if on_event:
                    await on_event(
                        access_status.value,
                        f"Access restriction: {restriction_reason}",
                        item.url,
                    )
                if item.depth == 0:
                    is_blocked = True
                    last_error_reason = restriction_reason
                    break
                continue

            # If fetch and checks passed, record success in circuit breaker
            domain_circuit_breaker.record_success(website_domain)

            # 6. Extract links & page title from Level 1 HTML
            page_title, discovered_links = LinkExtractor.extract_links(
                html=html,
                base_url=final_url,
                website_domain=website_domain,
                depth=item.depth,
                allow_subdomains=allow_subdomains,
            )

            # 7. Level 2 Playwright Fallback check
            if PlaywrightCrawler.is_js_shell(html, len(discovered_links)) and self.playwright_crawler.enabled:
                if on_event:
                    await on_event(
                        "PLAYWRIGHT_FALLBACK",
                        f"JS shell detected at {item.url}; invoking Playwright fallback",
                        item.url,
                    )

                rendered_res = await self.playwright_crawler.fetch_rendered(item.url)
                if rendered_res is not None:
                    html, final_url, status_code, elapsed_ms = rendered_res
                    level_used = "PLAYWRIGHT"
                    playwright_used_count += 1
                    # Re-extract with rendered DOM
                    page_title, discovered_links = LinkExtractor.extract_links(
                        html=html,
                        base_url=final_url,
                        website_domain=website_domain,
                        depth=item.depth,
                        allow_subdomains=allow_subdomains,
                    )

            # 8. Classify page
            page_type = PageClassifier.classify(
                url=final_url,
                anchor_text="",
                page_title=page_title,
            )

            fetched_page = FetchedPage(
                url=item.url,
                final_url=final_url,
                normalized_url=item.normalized_url,
                status_code=status_code,
                content_type=content_type,
                html=html,
                page_title=page_title,
                page_type=page_type,
                level_used=level_used,
                response_time_ms=elapsed_ms,
                discovered_at=datetime.now(timezone.utc),
                crawled_at=datetime.now(timezone.utc),
                internal_links=discovered_links,
            )
            pages_crawled.append(fetched_page)

            if on_event:
                await on_event(
                    "PAGE_CRAWLED",
                    f"Crawled {item.url} (HTTP {status_code}, type={page_type}, links={len(discovered_links)})",
                    item.url,
                )

            # 9. Queue discovered links if within depth and link following enabled
            if follow_internal_links and item.depth < max_depth:
                for link in discovered_links:
                    frontier.add(
                        url=link.url,
                        depth=link.depth,
                        tentative_type=link.tentative_page_type,
                        parent_url=item.url,
                    )

            # 10. Politeness delay between pages
            if frontier.has_more() and self.crawl_delay > 0:
                await asyncio.sleep(self.crawl_delay)

        duration = time.monotonic() - start_time

        # Compute status
        if pages_crawled:
            final_status = "CRAWLED"
        elif is_blocked:
            final_status = "BLOCKED"
        else:
            final_status = "FAILED"

        return WebsiteCrawlResult(
            website_id=website_id,
            url=root_url,
            domain=website_domain,
            status=final_status,
            pages_crawled=len(pages_crawled),
            pages_discovered=frontier.total_enqueued,
            playwright_used_count=playwright_used_count,
            pages=pages_crawled,
            error_reason=last_error_reason if not pages_crawled else None,
            duration_seconds=duration,
        )
