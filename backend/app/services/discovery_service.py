"""
app/services/discovery_service.py

Service orchestrating the discovery phase for scraping tasks.
Discovers candidate organizations and official websites, deduplicates, ranks,
persists records to PostgreSQL, and updates task metrics and logs.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.models.lead import Lead
from app.models.organization import Organization, task_organizations
from app.models.scraping_log import ScrapingLog
from app.models.website import Website
from app.repositories.task_repository import TaskRepository
from app.schemas.discovery import DiscoveryResult
from app.services.discovery.manager import DiscoveryManager
from app.services.discovery.ranking import DIRECTORY_DOMAINS
from app.services.discovery.website_validator import validate_website_reachability
from app.utils.url import extract_domain, normalize_url

logger = get_logger(__name__)


class DiscoveryService:
    """Orchestrates candidate discovery, deduplication, and database persistence for a ScrapingTask."""

    def __init__(
        self,
        session: AsyncSession,
        manager: DiscoveryManager | None = None,
    ) -> None:
        self.session = session
        self.repository = TaskRepository(session)
        self.manager = manager or DiscoveryManager()

    async def discover_for_task(self, task_id: str) -> DiscoveryResult:
        """Execute discovery for a task.

        Args:
            task_id: Human-readable task identifier (e.g. "TASK-000124").

        Returns:
            DiscoveryResult summary.
        """
        task = await self.repository.get_by_task_id(task_id)
        if task is None:
            raise AppException(
                message="Scraping task not found.",
                status_code=404,
                code="TASK_NOT_FOUND",
            )

        logger.info("Task %s discovery started", task.task_id)

        # ── 1. Transition task to RUNNING / DISCOVERING ────────────────────────
        task.status = "RUNNING"
        task.current_stage = "DISCOVERING"
        task.progress = 5
        if not task.started_at:
            task.started_at = datetime.now(timezone.utc)

        self.session.add(
            ScrapingLog(
                task_id=task.id,
                level="INFO",
                event_type="DISCOVERY_STARTED",
                message=f"Discovery started for keyword '{task.keyword}' in location '{task.location}'.",
            )
        )
        await self.session.flush()

        # ── 2. Query Discovery Providers via DiscoveryManager ─────────────────
        candidates, duplicates_removed, provider_stats, errors = await self.manager.discover(
            keyword=task.keyword,
            location=task.location,
            max_results=task.max_results,
        )

        total_candidates = sum(provider_stats.values())

        if duplicates_removed > 0:
            self.session.add(
                ScrapingLog(
                    task_id=task.id,
                    level="INFO",
                    event_type="DUPLICATE_DISCOVERY_REMOVED",
                    message=f"{duplicates_removed} duplicate candidates removed during discovery normalization.",
                )
            )

        # If all providers failed and no candidates could be found
        if not candidates and errors:
            failure_msg = f"All discovery providers failed: {'; '.join(errors)}"
            task.status = "FAILED"
            task.failure_reason = failure_msg
            self.session.add(
                ScrapingLog(
                    task_id=task.id,
                    level="ERROR",
                    event_type="DISCOVERY_FAILED",
                    message=failure_msg,
                )
            )
            await self.session.commit()
            return DiscoveryResult(
                task_id=task.task_id,
                total_candidates=total_candidates,
                accepted_candidates=0,
                duplicates_removed=duplicates_removed,
                organizations_created=0,
                organizations_reused=0,
                websites_found=0,
                provider_results=provider_stats,
                errors=errors,
            )

        # ── 3. Database Persistence & Candidate Website Probing ─────────────────
        task.current_stage = "FINDING_WEBSITES"
        task.progress = 10
        await self.session.commit()

        try:
            from app.realtime.publisher import get_event_publisher
            await get_event_publisher().publish_stage_changed(
                task.task_id,
                stage="FINDING_WEBSITES",
                progress=10,
                status=task.status,
            )
        except Exception as pe:
            logger.debug("Realtime publish failed for FINDING_WEBSITES stage: %s", pe)

        orgs_created = 0
        orgs_reused = 0
        websites_new = 0

        # Concurrently probe reachability for all candidates with non-portal URLs
        reach_sem = asyncio.Semaphore(10)
        fixtures_enabled = getattr(settings, "DISCOVERY_ENABLE_FIXTURES", False)

        async def _check_cand_reachability(cand_item: any, shared_client: httpx.AsyncClient) -> tuple[str, any]:
            cand_url_str = (cand_item.url or "").strip()
            if (
                not cand_url_str
                or cand_url_str.startswith("https://www.openstreetmap.org")
                or cand_url_str.startswith("fixture://")
            ):
                return cand_url_str, None
            if fixtures_enabled and getattr(cand_item, "source", None) == "FIXTURE":
                return cand_url_str, None
            try:
                async with reach_sem:
                    res = await validate_website_reachability(cand_url_str, timeout=4.0, client=shared_client)
                    return cand_url_str, res
            except Exception as e:
                logger.debug("Reachability probe failed for %s: %s", cand_url_str, e)
                return cand_url_str, None

        reachability_lookup: dict[str, any] = {}
        async with httpx.AsyncClient(
            headers={"User-Agent": settings.CRAWLER_USER_AGENT},
            follow_redirects=True,
            timeout=5.0,
        ) as probe_client:
            probe_tasks = [_check_cand_reachability(c, probe_client) for c in candidates if (c.url or "").strip()]
            if probe_tasks:
                probe_results = await asyncio.gather(*probe_tasks, return_exceptions=True)
                for item in probe_results:
                    if isinstance(item, tuple) and item[1] is not None:
                        reachability_lookup[item[0]] = item[1]

        for cand in candidates:
            # Check if organization already exists by domain or name
            org: Organization | None = None

            # First, check if a website with this domain is already attached to an org
            # (Only for distinct non-portal/non-directory domains)
            cand_domain = (cand.domain or "").lower()
            is_generic_domain = (
                not cand_domain
                or any(d in cand_domain for d in DIRECTORY_DOMAINS)
                or cand_domain in ("openstreetmap.org", "www.openstreetmap.org", "duckduckgo.com", "html.duckduckgo.com")
            )
            if not is_generic_domain:
                stmt_site = select(Website).where(Website.domain == cand_domain)
                res_site = await self.session.execute(stmt_site)
                existing_site = res_site.scalar_one_or_none()

                if existing_site is not None:
                    stmt_org = select(Organization).where(Organization.id == existing_site.organization_id)
                    res_org = await self.session.execute(stmt_org)
                    org = res_org.scalar_one_or_none()

            # Second, check by organization name
            if org is None:
                stmt_name = select(Organization).where(Organization.name.ilike(cand.name))
                res_name = await self.session.execute(stmt_name)
                org = res_name.scalar_one_or_none()

            if org is not None:
                orgs_reused += 1
            else:
                org = Organization(
                    name=cand.name,
                    category=cand.category or task.keyword,
                    address=cand.address,
                    city=task.location,
                )
                self.session.add(org)
                await self.session.flush()
                orgs_created += 1

            # Associate Organization with ScrapingTask (Idempotent check)
            stmt_m2m = select(task_organizations).where(
                task_organizations.c.task_id == task.id,
                task_organizations.c.organization_id == org.id,
            )
            res_m2m = await self.session.execute(stmt_m2m)
            if res_m2m.first() is None:
                await self.session.execute(
                    task_organizations.insert().values(
                        task_id=task.id,
                        organization_id=org.id,
                    )
                )

            # Associate Lead record for this task (Idempotent check)
            stmt_lead = select(Lead).where(
                Lead.task_id == task.id,
                Lead.organization_id == org.id,
            )
            res_lead = await self.session.execute(stmt_lead)
            if res_lead.scalar_one_or_none() is None:
                lead = Lead(
                    task_id=task.id,
                    organization_id=org.id,
                    status="ACTIVE",
                    verification_status="PENDING",
                )
                self.session.add(lead)

            # ── Website Validation & Persistence ──────────────────────────
            cand_url = (cand.url or "").strip()
            website_url_to_save: str | None = None
            website_domain: str | None = None
            is_official = getattr(cand, "is_official_candidate", False)

            if cand_url and not cand_url.startswith("https://www.openstreetmap.org") and not cand_url.startswith("fixture://"):
                if fixtures_enabled and cand.source == "FIXTURE":
                    website_url_to_save = cand_url
                    website_domain = cand.domain
                else:
                    reachability = reachability_lookup.get(cand_url)
                    if reachability and reachability.is_reachable:
                        website_url_to_save = reachability.final_url or reachability.normalized_url
                        website_domain = reachability.domain or cand.domain
                        is_official = True
                    else:
                        logger.info("Candidate website unreachable for %s (%s)", cand.name, cand_url)
            elif cand_url.startswith("fixture://") and getattr(settings, "DISCOVERY_ENABLE_FIXTURES", False):
                website_url_to_save = cand_url
                website_domain = cand.domain

            if website_url_to_save:
                norm_site_url = normalize_url(website_url_to_save)
                stmt_web = select(Website).where(
                    Website.organization_id == org.id,
                    Website.normalized_url == norm_site_url,
                )
                res_web = await self.session.execute(stmt_web)
                website = res_web.scalar_one_or_none()

                if website is None:
                    website = Website(
                        organization_id=org.id,
                        url=website_url_to_save,
                        normalized_url=norm_site_url,
                        domain=website_domain or extract_domain(norm_site_url),
                        is_official=is_official,
                        status="PENDING",
                    )
                    self.session.add(website)
                    await self.session.flush()
                    websites_new += 1

                    self.session.add(
                        ScrapingLog(
                            task_id=task.id,
                            organization_id=org.id,
                            website_id=website.id,
                            level="INFO",
                            event_type="ORGANIZATION_DISCOVERED",
                            message=f"Discovered organization '{org.name}' ({website.domain}).",
                            url=website.url,
                        )
                    )

                    if is_official:
                        self.session.add(
                            ScrapingLog(
                                task_id=task.id,
                                organization_id=org.id,
                                website_id=website.id,
                                level="INFO",
                                event_type="OFFICIAL_WEBSITE_CANDIDATE_FOUND",
                                message=f"Candidate official website identified and reachable: {website.url}",
                                url=website.url,
                            )
                        )

        # ── 4. Update Task Metrics and Progress ────────────────────────────────
        # Count total distinct organizations currently attached to this task
        stmt_count = select(task_organizations).where(task_organizations.c.task_id == task.id)
        res_count = await self.session.execute(stmt_count)
        total_task_orgs = len(res_count.all())

        task.results_discovered = total_task_orgs
        task.websites_found += websites_new
        task.duplicates_removed += duplicates_removed

        # Transition stage to FINDING_WEBSITES (ready for Step 3 official website identification)
        task.current_stage = "FINDING_WEBSITES"
        task.progress = 20

        self.session.add(
            ScrapingLog(
                task_id=task.id,
                level="INFO",
                event_type="DISCOVERY_COMPLETED",
                message=(
                    f"Discovery completed: {len(candidates)} candidates accepted, "
                    f"{duplicates_removed} duplicates removed, {websites_new} new websites registered."
                ),
            )
        )

        await self.session.commit()
        logger.info("Task %s discovery completed. %d organizations linked.", task.task_id, total_task_orgs)

        return DiscoveryResult(
            task_id=task.task_id,
            total_candidates=total_candidates,
            accepted_candidates=len(candidates),
            duplicates_removed=duplicates_removed,
            organizations_created=orgs_created,
            organizations_reused=orgs_reused,
            websites_found=websites_new,
            provider_results=provider_stats,
            errors=errors,
        )
