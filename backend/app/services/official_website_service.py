"""
app/services/official_website_service.py

Dedicated service for identifying and verifying official website URLs for candidate organizations
discovered in Step 2, moving the pipeline through Step 3 ("Finding official websites").

Features:
  • Queries candidate organizations for a task
  • Validates candidate URLs using bounded HTTP reachability probes
  • Isolates individual probe failures without stalling the stage
  • Structured logging matching platform event standards:
      - official_website_stage_started
      - candidate_count
      - candidate_processing_started
      - candidate_processing_completed
      - official_website_found
      - official_website_not_found
      - official_website_stage_completed
      - crawl_stage_queued
  • Monotonic progress advancement: 20% -> 30%
  • Clean database session transaction boundaries
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.models.organization import Organization, task_organizations
from app.models.scraping_log import ScrapingLog
from app.models.scraping_task import ScrapingTask
from app.models.website import Website
from app.repositories.task_repository import TaskRepository
from app.services.discovery.ranking import DIRECTORY_DOMAINS
from app.services.discovery.website_validator import validate_website_reachability
from app.utils.url import extract_domain, normalize_url

logger = get_logger(__name__)


class OfficialWebsiteService:
    """Service orchestrating candidate official website identification and verification."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = TaskRepository(session)

    async def find_official_websites_for_task(self, task_id: str) -> dict[str, Any]:
        """Identify, probe, and record official websites for all organizations in a task.

        Args:
            task_id: Human-readable task identifier (e.g. "TASK-000005").

        Returns:
            Dict summary of processed candidates and identified websites.
        """
        start_time = time.monotonic()
        task = await self.repository.get_by_task_id(task_id)
        if task is None:
            raise AppException(
                message=f"Scraping task '{task_id}' not found.",
                status_code=404,
                code="TASK_NOT_FOUND",
            )

        # ── 1. Set Stage & Progress Floor (20%) ──────────────────────────────
        task.status = "RUNNING"
        task.current_stage = "FINDING_WEBSITES"
        task.progress = max(task.progress, 20)

        logger.info("[%s] official website stage started", task.task_id)

        self.session.add(
            ScrapingLog(
                task_id=task.id,
                level="INFO",
                event_type="OFFICIAL_WEBSITE_STAGE_STARTED",
                message=f"Started identifying official websites for task {task.task_id}.",
            )
        )
        await self.session.commit()

        try:
            from app.realtime.publisher import get_event_publisher
            await get_event_publisher().publish_stage_changed(
                task.task_id,
                stage="FINDING_WEBSITES",
                progress=task.progress,
                status=task.status,
            )
        except Exception as pe:
            logger.debug("Realtime publish failed for FINDING_WEBSITES stage: %s", pe)

        # ── 2. Retrieve Candidate Organizations for this Task ─────────────────
        stmt_orgs = (
            select(Organization)
            .join(task_organizations, task_organizations.c.organization_id == Organization.id)
            .where(task_organizations.c.task_id == task.id)
            .order_by(Organization.created_at.asc())
        )
        res_orgs = await self.session.execute(stmt_orgs)
        candidates = list(res_orgs.scalars().all())
        total_candidates = len(candidates)

        logger.info("[%s] candidate_count: %d", task.task_id, total_candidates)

        self.session.add(
            ScrapingLog(
                task_id=task.id,
                level="INFO",
                event_type="CANDIDATE_COUNT",
                message=f"Found {total_candidates} candidate organizations for official website identification.",
            )
        )
        await self.session.commit()

        # ── 3. Check Existing Websites & Probe Missing Candidate Websites ─────
        websites_found_count = 0
        reach_sem = asyncio.Semaphore(10)
        fixtures_enabled = getattr(settings, "DISCOVERY_ENABLE_FIXTURES", False)

        # Configure bounded timeouts
        probe_timeout = httpx.Timeout(connect=3.0, read=4.0, write=3.0, pool=3.0)

        for idx, org in enumerate(candidates, start=1):
            logger.info(
                "[%s] candidate_processing_started: candidate_id=%s, organization_name=%s",
                task.task_id,
                org.id,
                org.name,
            )
            self.session.add(
                ScrapingLog(
                    task_id=task.id,
                    organization_id=org.id,
                    level="INFO",
                    event_type="CANDIDATE_PROCESSING_STARTED",
                    message=f"Processing candidate organization '{org.name}' ({idx}/{total_candidates}).",
                )
            )

            # Check if organization already has an official or pending website attached
            stmt_site = select(Website).where(Website.organization_id == org.id)
            res_site = await self.session.execute(stmt_site)
            existing_website = res_site.scalar_one_or_none()

            website_url_to_save: str | None = None
            website_domain: str | None = None
            is_official = False

            if existing_website:
                website_url_to_save = existing_website.url
                website_domain = existing_website.domain
                is_official = existing_website.is_official
            else:
                # If organization has a website candidate URL in its raw data or name search
                cand_url = getattr(org, "website", None) or getattr(org, "url", None) or ""
                cand_url_str = cand_url.strip() if isinstance(cand_url, str) else ""

                if cand_url_str and not cand_url_str.startswith("https://www.openstreetmap.org"):
                    if fixtures_enabled and (cand_url_str.startswith("fixture://") or cand_url_str.endswith(".example")):
                        website_url_to_save = cand_url_str
                        website_domain = extract_domain(cand_url_str)
                        is_official = True
                    else:
                        try:
                            async with reach_sem:
                                async with httpx.AsyncClient(
                                    headers={"User-Agent": settings.CRAWLER_USER_AGENT},
                                    timeout=probe_timeout,
                                    follow_redirects=True,
                                ) as client:
                                    reach_res = await validate_website_reachability(
                                        cand_url_str,
                                        timeout=4.0,
                                        client=client,
                                    )
                                    if reach_res and reach_res.is_reachable:
                                        website_url_to_save = reach_res.final_url or reach_res.normalized_url
                                        website_domain = reach_res.domain
                                        is_official = True
                        except Exception as probe_err:
                            logger.debug(
                                "[%s] Probe error for %s: %s",
                                task.task_id,
                                cand_url_str,
                                probe_err,
                            )

            if website_url_to_save:
                norm_site_url = normalize_url(website_url_to_save)
                stmt_find = select(Website).where(
                    Website.organization_id == org.id,
                    Website.normalized_url == norm_site_url,
                )
                res_find = await self.session.execute(stmt_find)
                target_web = res_find.scalar_one_or_none()

                if target_web is None:
                    target_web = Website(
                        organization_id=org.id,
                        url=website_url_to_save,
                        normalized_url=norm_site_url,
                        domain=website_domain or extract_domain(norm_site_url),
                        is_official=is_official,
                        status="PENDING",
                    )
                    self.session.add(target_web)
                    await self.session.flush()

                websites_found_count += 1
                logger.info(
                    "[%s] official_website_found: candidate_id=%s, organization_name=%s, url=%s",
                    task.task_id,
                    org.id,
                    org.name,
                    target_web.url,
                )
                self.session.add(
                    ScrapingLog(
                        task_id=task.id,
                        organization_id=org.id,
                        website_id=target_web.id,
                        level="INFO",
                        event_type="OFFICIAL_WEBSITE_FOUND",
                        message=f"Official website identified for '{org.name}': {target_web.url}",
                        url=target_web.url,
                    )
                )
            else:
                logger.info(
                    "[%s] official_website_not_found: candidate_id=%s, organization_name=%s",
                    task.task_id,
                    org.id,
                    org.name,
                )
                self.session.add(
                    ScrapingLog(
                        task_id=task.id,
                        organization_id=org.id,
                        level="INFO",
                        event_type="OFFICIAL_WEBSITE_NOT_FOUND",
                        message=f"No official website found for candidate organization '{org.name}'.",
                    )
                )

            logger.info(
                "[%s] candidate_processing_completed: candidate_id=%s",
                task.task_id,
                org.id,
            )
            self.session.add(
                ScrapingLog(
                    task_id=task.id,
                    organization_id=org.id,
                    level="INFO",
                    event_type="CANDIDATE_PROCESSING_COMPLETED",
                    message=f"Candidate processing completed for '{org.name}'.",
                )
            )

            # Incremental progress between 20% and 30%
            if total_candidates > 0:
                fraction = idx / total_candidates
                task.progress = min(30, 20 + int(fraction * 10))

            await self.session.commit()

        # ── 4. Finalize Official Website Stage ────────────────────────────────
        task.websites_found = websites_found_count
        task.progress = 30
        task.current_stage = "CRAWLING"

        total_duration = time.monotonic() - start_time
        logger.info(
            "[%s] official_website_stage_completed: %d candidates, %d websites found in %.2fs",
            task.task_id,
            total_candidates,
            websites_found_count,
            total_duration,
        )
        self.session.add(
            ScrapingLog(
                task_id=task.id,
                level="INFO",
                event_type="OFFICIAL_WEBSITE_STAGE_COMPLETED",
                message=(
                    f"Official website identification completed in {total_duration:.1f}s. "
                    f"{total_candidates} candidates evaluated, {websites_found_count} official websites verified."
                ),
            )
        )

        logger.info(
            "[%s] crawl_stage_queued: %d websites to crawl",
            task.task_id,
            websites_found_count,
        )
        self.session.add(
            ScrapingLog(
                task_id=task.id,
                level="INFO",
                event_type="CRAWL_STAGE_QUEUED",
                message=f"Queuing website crawl stage for {websites_found_count} candidate websites.",
            )
        )
        await self.session.commit()

        try:
            from app.realtime.publisher import get_event_publisher
            await get_event_publisher().publish_progress(
                task.task_id,
                progress=30,
                stage="CRAWLING",
                status=task.status,
            )
        except Exception as pe:
            logger.debug("Realtime publish failed for official website stage completion: %s", pe)

        return {
            "task_id": task.task_id,
            "total_candidates": total_candidates,
            "websites_found": websites_found_count,
            "duration_seconds": total_duration,
            "status": "COMPLETED",
            "next_stage": "CRAWLING",
        }
