"""
app/services/cleaning/cleaning_service.py

Task orchestrator executing data cleaning, field normalization,
exact duplicate removal, organization matching with branch safety,
safe merging, and task stage advancement to VERIFYING.
"""

from __future__ import annotations

import time
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.models.lead import Lead
from app.models.organization import Organization, task_organizations
from app.models.scraping_log import ScrapingLog
from app.models.scraping_task import ScrapingTask
from app.repositories.task_repository import TaskRepository
from app.schemas.cleaning import CleaningResult
from app.services.cleaning.address_cleaner import clean_address, clean_pincode
from app.services.cleaning.deduplication_service import DeduplicationService
from app.services.cleaning.email_cleaner import clean_email
from app.services.cleaning.merge_service import MergeService
from app.services.cleaning.organization_cleaner import clean_organization_name
from app.services.cleaning.organization_matcher import OrganizationMatcher
from app.services.cleaning.phone_cleaner import clean_phone_number
from app.services.cleaning.text_cleaner import clean_text, is_placeholder
from app.services.cleaning.url_cleaner import clean_social_url, clean_url

logger = get_logger(__name__)


class CleaningService:
    """Orchestrates the cleaning, normalization, and deduplication pipeline for a task."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = TaskRepository(session)

    async def clean_task(self, task_id: str | uuid.UUID) -> CleaningResult:
        """Run the comprehensive cleaning and deduplication pipeline on a task.

        Args:
            task_id: Human-readable task ID (e.g. "TASK-000124") or task UUID.

        Returns:
            CleaningResult containing execution statistics and next stage confirmation.
        """
        start_time = time.monotonic()

        # ── 1. Resolve Task ───────────────────────────────────────────────────
        task: ScrapingTask | None = None
        if isinstance(task_id, uuid.UUID):
            task = await self.repository.get_by_id(task_id)
        elif isinstance(task_id, str):
            if task_id.startswith("TASK-"):
                task = await self.repository.get_by_task_id(task_id)
            else:
                try:
                    uid = uuid.UUID(task_id)
                    task = await self.repository.get_by_id(uid)
                except ValueError:
                    task = await self.repository.get_by_task_id(task_id)

        if task is None:
            raise AppException(
                message="Scraping task not found.",
                status_code=404,
                code="TASK_NOT_FOUND",
            )

        logger.info("Starting cleaning pipeline for task %s", task.task_id)

        # ── 2. Query Associated Organizations ─────────────────────────────────
        stmt_orgs = (
            select(Organization)
            .join(task_organizations, task_organizations.c.organization_id == Organization.id)
            .where(task_organizations.c.task_id == task.id)
            .options(
                selectinload(Organization.websites),
                selectinload(Organization.phone_numbers),
                selectinload(Organization.email_addresses),
                selectinload(Organization.social_links),
                selectinload(Organization.contacts),
                selectinload(Organization.source_pages),
            )
        )
        task_orgs = list((await self.session.execute(stmt_orgs)).scalars().all())

        organizations_processed = len(task_orgs)
        phones_cleaned = 0
        emails_cleaned = 0
        addresses_cleaned = 0
        invalid_phones_removed = 0
        invalid_emails_removed = 0
        exact_duplicates_removed = 0
        organizations_merged = 0
        potential_duplicates_flagged = 0

        # ── Phase 1: Field Cleaning & Child Exact Deduplication ───────────────
        for org in task_orgs:
            # Clean Name
            if org.name:
                org.name = clean_organization_name(org.name)

            # Clean Category
            if org.category:
                if is_placeholder(org.category):
                    org.category = None
                else:
                    org.category = clean_text(org.category)

            # Clean Address
            if org.address:
                if is_placeholder(org.address):
                    org.address = None
                else:
                    org.address = clean_address(org.address)
                    addresses_cleaned += 1

            # Clean City
            if org.city:
                if is_placeholder(org.city):
                    org.city = None
                else:
                    org.city = clean_text(org.city)

            # Clean State
            if org.state:
                if is_placeholder(org.state):
                    org.state = None
                else:
                    org.state = clean_text(org.state)

            # Clean Pincode
            if org.pincode:
                cleaned_pin = clean_pincode(org.pincode)
                org.pincode = cleaned_pin

            # Clean Websites
            for w in list(org.websites):
                if is_placeholder(w.url):
                    await self.session.delete(w)
                else:
                    w.normalized_url = clean_url(w.url)
                    w.domain = OrganizationMatcher.extract_clean_domain(w.normalized_url)

            # Clean Phone Numbers
            for p in list(org.phone_numbers):
                cleaned_p = clean_phone_number(p.phone_number)
                if not cleaned_p:
                    await self.session.delete(p)
                    invalid_phones_removed += 1
                else:
                    p.normalized_phone = cleaned_p.e164
                    p.phone_number = cleaned_p.display
                    phones_cleaned += 1

            # Clean Email Addresses
            for e in list(org.email_addresses):
                cleaned_e = clean_email(e.email)
                if not cleaned_e:
                    await self.session.delete(e)
                    invalid_emails_removed += 1
                else:
                    e.normalized_email = cleaned_e.normalized
                    e.email = cleaned_e.normalized
                    emails_cleaned += 1

            # Clean Social Links
            for s in list(org.social_links):
                cleaned_s = clean_social_url(s.url)
                if not cleaned_s:
                    await self.session.delete(s)
                else:
                    s.normalized_url = cleaned_s

            # Clean Contacts
            for c in list(org.contacts):
                c.name = clean_text(c.name)
                if c.designation:
                    c.designation = clean_text(c.designation)

            # Clean Source Pages
            for sp in list(org.source_pages):
                if sp.url:
                    sp.normalized_url = clean_url(sp.url)

            # Exact duplicate removal for this organization
            dedup_counts = await DeduplicationService.deduplicate_organization(
                self.session, org.id
            )
            exact_duplicates_removed += sum(dedup_counts.values())

        await self.session.flush()

        # ── Phase 2: Organization Duplicate Detection & Merging ───────────────
        merged_any = True
        while merged_any:
            merged_any = False
            active_orgs = list((await self.session.execute(stmt_orgs)).scalars().all())
            n = len(active_orgs)

            for i in range(n):
                for j in range(i + 1, n):
                    org_a = active_orgs[i]
                    org_b = active_orgs[j]
                    match_result = OrganizationMatcher.match(org_a, org_b)

                    if match_result.is_duplicate:
                        merge_res = await MergeService.merge_organizations(
                            session=self.session,
                            org1=org_a,
                            org2=org_b,
                            match_score=match_result.score,
                            match_reasons=match_result.reasons,
                        )
                        organizations_merged += 1
                        exact_duplicates_removed += sum(merge_res["dedup_counts"].values())

                        canonical_org = merge_res["canonical_organization"]
                        self.session.add(
                            ScrapingLog(
                                task_id=task.id,
                                organization_id=canonical_org.id,
                                level="INFO",
                                event_type="ORGANIZATION_MERGED",
                                message=(
                                    f"Merged duplicate organization into canonical '{canonical_org.name}' "
                                    f"(score {match_result.score}): {'; '.join(match_result.reasons)}"
                                ),
                            )
                        )
                        merged_any = True
                        break
                if merged_any:
                    break

        # Log potential duplicates among surviving organizations post-merge
        final_orgs = list((await self.session.execute(stmt_orgs)).scalars().all())
        num_final = len(final_orgs)
        for i in range(num_final):
            for j in range(i + 1, num_final):
                org_a = final_orgs[i]
                org_b = final_orgs[j]
                match_result = OrganizationMatcher.match(org_a, org_b)
                if match_result.is_potential:
                    potential_duplicates_flagged += 1
                    self.session.add(
                        ScrapingLog(
                            task_id=task.id,
                            organization_id=org_a.id,
                            level="WARNING",
                            event_type="POTENTIAL_DUPLICATE",
                            message=(
                                f"Potential duplicate detected between '{org_a.name}' and '{org_b.name}' "
                                f"(score {match_result.score}): {'; '.join(match_result.reasons)}"
                            ),
                        )
                    )

        # ── Phase 3: Lead Deduplication for Task ───────────────────────────────
        stmt_leads = select(Lead).where(Lead.task_id == task.id)
        task_leads = list((await self.session.execute(stmt_leads)).scalars().all())
        seen_lead_org_ids: set[uuid.UUID] = set()
        for lead in task_leads:
            if lead.organization_id in seen_lead_org_ids:
                await self.session.delete(lead)
                exact_duplicates_removed += 1
            else:
                seen_lead_org_ids.add(lead.organization_id)

        await self.session.flush()

        # ── Phase 4: Advance Task Stage & Update Metrics ──────────────────────
        total_duplicates = (
            exact_duplicates_removed
            + organizations_merged
            + invalid_phones_removed
            + invalid_emails_removed
        )
        task.duplicates_removed = (task.duplicates_removed or 0) + total_duplicates
        task.current_stage = "VERIFYING"
        task.progress = 85
        if task.status != "CANCELLED":
            task.status = "RUNNING"

        duration = time.monotonic() - start_time

        self.session.add(
            ScrapingLog(
                task_id=task.id,
                level="INFO",
                event_type="CLEANING_COMPLETED",
                message=(
                    f"Data cleaning completed in {duration:.2f}s. "
                    f"Processed {organizations_processed} orgs, merged {organizations_merged}, "
                    f"removed {total_duplicates} duplicates. Advanced to VERIFYING."
                ),
            )
        )
        await self.session.commit()
        logger.info(
            "Task %s cleaning completed in %.2fs. Stage advanced to VERIFYING",
            task.task_id,
            duration,
        )

        return CleaningResult(
            task_id=task.task_id,
            organizations_processed=organizations_processed,
            organizations_merged=organizations_merged,
            exact_duplicates_removed=exact_duplicates_removed,
            phones_cleaned=phones_cleaned,
            emails_cleaned=emails_cleaned,
            addresses_cleaned=addresses_cleaned,
            invalid_phones_removed=invalid_phones_removed,
            invalid_emails_removed=invalid_emails_removed,
            potential_duplicates_flagged=potential_duplicates_flagged,
            total_duplicates_removed=total_duplicates,
            duration_seconds=round(duration, 3),
            status="Cleaning completed",
            next_stage="VERIFYING",
        )
