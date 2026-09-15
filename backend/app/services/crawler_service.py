"""
app/services/crawler_service.py

Service orchestrating the website crawling phase for a ScrapingTask.
Crawls all candidate websites attached to a task, isolates individual website failures,
upserts crawled SourcePages in PostgreSQL, and advances the task to EXTRACTING.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.models.organization import Organization, task_organizations
from app.models.scraping_log import ScrapingLog
from app.models.scraping_task import ScrapingTask
from app.models.source_page import SourcePage
from app.models.website import Website
from app.repositories.task_repository import TaskRepository
from app.schemas.crawler import TaskCrawlSummary, WebsiteCrawlResult
from app.services.crawler.crawler import WebsiteCrawler

logger = get_logger(__name__)


class CrawlerService:
    """Orchestrates website crawling for a ScrapingTask with strict failure isolation."""

    def __init__(
        self,
        session: AsyncSession,
        crawler: WebsiteCrawler | None = None,
    ) -> None:
        self.session = session
        self.repository = TaskRepository(session)
        self.crawler = crawler or WebsiteCrawler()

    async def crawl_for_task(self, task_id: str) -> TaskCrawlSummary:
        """Crawl all websites attached to a ScrapingTask.

        Args:
            task_id: Human-readable task identifier (e.g. "TASK-000124").

        Returns:
            TaskCrawlSummary summary of crawled pages, websites, and status.
        """
        start_time = time.monotonic()
        task = await self.repository.get_by_task_id(task_id)
        if task is None:
            raise AppException(
                message="Scraping task not found.",
                status_code=404,
                code="TASK_NOT_FOUND",
            )

        logger.info("Task %s crawl execution started", task.task_id)

        # ── 1. Update task stage to CRAWLING ──────────────────────────────────
        task.status = "RUNNING"
        task.current_stage = "CRAWLING"
        if not task.started_at:
            task.started_at = datetime.now(timezone.utc)
        task.progress = max(task.progress, 20)

        self.session.add(
            ScrapingLog(
                task_id=task.id,
                level="INFO",
                event_type="CRAWL_STARTED",
                message=f"Starting website crawler for task {task.task_id}.",
            )
        )
        await self.session.flush()

        # ── 2. Discover all websites attached to this task ────────────────────
        stmt_websites = (
            select(Website)
            .join(Organization, Website.organization_id == Organization.id)
            .join(task_organizations, task_organizations.c.organization_id == Organization.id)
            .where(task_organizations.c.task_id == task.id)
            .order_by(Website.is_official.desc(), Website.created_at.asc())
        )
        res_websites = await self.session.execute(stmt_websites)
        websites = list(res_websites.scalars().all())

        total_websites = len(websites)
        websites_crawled_count = 0
        failed_websites_count = 0
        blocked_websites_count = 0
        total_pages_stored = 0
        playwright_total = 0

        # Event logging helper for the crawler
        async def log_crawler_event(event_type: str, message: str, page_url: str | None = None, website_id: any = None) -> None:
            log_level = "INFO"
            if "FAIL" in event_type or "ERROR" in event_type:
                log_level = "ERROR"
            elif "BLOCKED" in event_type or "DENIED" in event_type or "DISALLOWED" in event_type or "TIMEOUT" in event_type:
                log_level = "WARNING"

            self.session.add(
                ScrapingLog(
                    task_id=task.id,
                    website_id=website_id,
                    level=log_level,
                    event_type=event_type,
                    message=message,
                    url=page_url,
                )
            )
            await self.session.flush()

        # ── 3. Crawl Websites with Failure Isolation ──────────────────────────
        for idx, website in enumerate(websites, 1):
            logger.info(
                "Task %s: Crawling website [%d/%d] %s (%s)",
                task.task_id,
                idx,
                total_websites,
                website.url,
                website.domain,
            )

            await log_crawler_event(
                event_type="WEBSITE_CRAWL_STARTED",
                message=f"Beginning crawl of website: {website.url}",
                page_url=website.url,
                website_id=website.id,
            )
            website.status = "CRAWLING"
            await self.session.flush()

            async def site_event_cb(ev_type: str, msg: str, url_str: str | None) -> None:
                await log_crawler_event(ev_type, msg, url_str, website_id=website.id)

            try:
                crawl_res = await self.crawler.crawl(
                    website_id=website.id,
                    root_url=website.url,
                    max_pages=task.max_pages_per_site,
                    max_depth=task.crawl_depth,
                    follow_internal_links=task.follow_internal_links,
                    prioritize_contact=task.prioritize_contact,
                    prioritize_about=task.prioritize_about,
                    prioritize_admissions=task.prioritize_admissions,
                    prioritize_staff_management=task.prioritize_staff_management,
                    on_event=site_event_cb,
                )
            except Exception as exc:
                logger.error("Error crawling website %s: %s", website.url, exc)
                crawl_res = WebsiteCrawlResult(
                    website_id=website.id,
                    url=website.url,
                    domain=website.domain,
                    status="FAILED",
                    error_reason=str(exc),
                    duration_seconds=0.0,
                )

            playwright_total += crawl_res.playwright_used_count

            # Update website status and persist pages
            if crawl_res.status == "CRAWLED":
                website.status = "CRAWLED"
                website.last_crawled_at = datetime.now(timezone.utc)
                websites_crawled_count += 1

                # Upsert SourcePages
                for page in crawl_res.pages:
                    stmt_page = select(SourcePage).where(
                        SourcePage.website_id == website.id,
                        SourcePage.normalized_url == page.normalized_url,
                    )
                    res_page = await self.session.execute(stmt_page)
                    existing_page = res_page.scalar_one_or_none()

                    if existing_page is not None:
                        existing_page.page_title = page.page_title
                        existing_page.page_type = page.page_type
                        existing_page.http_status = page.status_code
                        existing_page.crawled_at = page.crawled_at
                    else:
                        new_page = SourcePage(
                            organization_id=website.organization_id,
                            website_id=website.id,
                            task_id=task.id,
                            url=page.url,
                            normalized_url=page.normalized_url,
                            page_title=page.page_title,
                            page_type=page.page_type,
                            http_status=page.status_code,
                            discovered_at=page.discovered_at,
                            crawled_at=page.crawled_at,
                        )
                        self.session.add(new_page)
                        total_pages_stored += 1

                await log_crawler_event(
                    event_type="WEBSITE_CRAWL_COMPLETED",
                    message=f"Website {website.url} crawled successfully: {len(crawl_res.pages)} pages stored.",
                    page_url=website.url,
                    website_id=website.id,
                )
            elif crawl_res.status == "BLOCKED":
                website.status = "BLOCKED"
                blocked_websites_count += 1
                failed_websites_count += 1
                await log_crawler_event(
                    event_type="CRAWL_FAILED",
                    message=f"Website {website.url} blocked access: {crawl_res.error_reason}",
                    page_url=website.url,
                    website_id=website.id,
                )
            else:
                website.status = "FAILED"
                failed_websites_count += 1
                await log_crawler_event(
                    event_type="CRAWL_FAILED",
                    message=f"Website {website.url} crawl failed: {crawl_res.error_reason}",
                    page_url=website.url,
                    website_id=website.id,
                )

            # Update task intermediate metrics and progress
            task.websites_crawled = websites_crawled_count
            task.failed_websites = failed_websites_count
            if total_websites > 0:
                fraction = (websites_crawled_count + failed_websites_count) / total_websites
                task.progress = min(50, 20 + int(fraction * 30))

            await self.session.commit()

            try:
                from app.realtime.publisher import get_event_publisher
                from app.realtime.events import extract_task_metrics
                publisher = get_event_publisher()
                if crawl_res.status in {"BLOCKED", "FAILED"}:
                    await publisher.publish_activity(
                        task.task_id,
                        message=f"Website {website.domain} failed: {crawl_res.error_reason or 'Access issue'}",
                        stage=task.current_stage,
                    )
                await publisher.publish_progress(
                    task.task_id,
                    progress=task.progress,
                    stage=task.current_stage,
                    status=task.status,
                    metrics=extract_task_metrics(task),
                )
            except Exception as pe:
                logger.debug("Realtime publish failed during crawl loop: %s", pe)

        # ── 4. Finalize Task Stage ────────────────────────────────────────────
        task.websites_crawled = websites_crawled_count
        task.failed_websites = failed_websites_count
        task.current_stage = "EXTRACTING"
        task.progress = 50

        total_duration = time.monotonic() - start_time
        summary_msg = (
            f"Crawling completed in {total_duration:.1f}s. "
            f"Websites: {total_websites}, Crawled: {websites_crawled_count}, "
            f"Failed: {failed_websites_count}, Blocked: {blocked_websites_count}, "
            f"Pages Stored: {total_pages_stored}, Playwright: {playwright_total}."
        )

        self.session.add(
            ScrapingLog(
                task_id=task.id,
                level="INFO",
                event_type="CRAWL_COMPLETED",
                message=summary_msg,
            )
        )
        await self.session.commit()
        logger.info("Task %s crawl completed. Next stage: EXTRACTING", task.task_id)

        return TaskCrawlSummary(
            task_id=task.task_id,
            total_websites=total_websites,
            websites_crawled=websites_crawled_count,
            failed_websites=failed_websites_count,
            blocked_websites=blocked_websites_count,
            total_pages_stored=total_pages_stored,
            playwright_total=playwright_total,
            duration_seconds=total_duration,
            status="Crawling completed",
            next_stage="EXTRACTING",
        )
