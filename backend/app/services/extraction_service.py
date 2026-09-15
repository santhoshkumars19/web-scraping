"""
app/services/extraction_service.py

Service orchestrating the data extraction phase for a ScrapingTask.
Processes all SourcePages, runs modular extractors, persists entities in PostgreSQL,
creates ExtractedField provenance audit trails, and advances task stage to CLEANING.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.models.contact import Contact
from app.models.email_address import EmailAddress
from app.models.extracted_field import ExtractedField
from app.models.organization import Organization
from app.models.phone_number import PhoneNumber
from app.models.scraping_log import ScrapingLog
from app.models.social_link import SocialLink
from app.models.source_page import SourcePage
from app.repositories.task_repository import TaskRepository
from app.schemas.extraction import TaskExtractionSummary
from app.services.extraction.base import PageContext
from app.services.extraction.extractor import PageDataExtractor

logger = get_logger(__name__)


class ExtractionService:
    """Orchestrates entity and contact extraction for all SourcePages in a task."""

    def __init__(
        self,
        session: AsyncSession,
        extractor: PageDataExtractor | None = None,
    ) -> None:
        self.session = session
        self.repository = TaskRepository(session)
        self.extractor = extractor or PageDataExtractor()

    async def extract_for_task(
        self,
        task_id: str,
        client: httpx.AsyncClient | None = None,
        html_cache: dict[str, str] | None = None,
    ) -> TaskExtractionSummary:
        """Extract public information from all SourcePages associated with a task.

        Args:
            task_id: Human-readable task identifier (e.g. "TASK-000124").
            client: Optional injected httpx client (e.g. mock transport in tests).
            html_cache: Optional dictionary mapping URL -> HTML text.

        Returns:
            TaskExtractionSummary execution summary.
        """
        start_time = time.monotonic()
        task = await self.repository.get_by_task_id(task_id)
        if task is None:
            raise AppException(
                message="Scraping task not found.",
                status_code=404,
                code="TASK_NOT_FOUND",
            )

        logger.info("Task %s data extraction started", task.task_id)

        # ── 1. Update task stage to EXTRACTING ─────────────────────────────────
        task.status = "RUNNING"
        task.current_stage = "EXTRACTING"
        task.progress = max(task.progress, 55)

        self.session.add(
            ScrapingLog(
                task_id=task.id,
                level="INFO",
                event_type="EXTRACTION_STARTED",
                message=f"Beginning data extraction for task {task.task_id}.",
            )
        )
        await self.session.flush()

        # ── 2. Retrieve all SourcePages for this task ─────────────────────────
        stmt_pages = select(SourcePage).where(SourcePage.task_id == task.id)
        res_pages = await self.session.execute(stmt_pages)
        source_pages = list(res_pages.scalars().all())

        total_pages = len(source_pages)
        phones_count = 0
        emails_count = 0
        addresses_count = 0
        contacts_count = 0
        socials_count = 0
        provenance_count = 0

        # Helper to fetch HTML if not already cached
        async def get_html(page_url: str, active_client: httpx.AsyncClient | None) -> str:
            if html_cache and page_url in html_cache:
                return html_cache[page_url]
            if html_cache and page_url.rstrip("/") in html_cache:
                return html_cache[page_url.rstrip("/")]

            if active_client is not None:
                try:
                    resp = await active_client.get(page_url, timeout=10.0)
                    return resp.text if resp.status_code == 200 else ""
                except Exception as e:
                    logger.debug("Failed to fetch HTML for %s: %s", page_url, e)
                    return ""

            try:
                async with httpx.AsyncClient(
                    headers={"User-Agent": settings.CRAWLER_USER_AGENT},
                    timeout=10.0,
                ) as default_client:
                    resp = await default_client.get(page_url)
                    return resp.text if resp.status_code == 200 else ""
            except Exception as e:
                logger.debug("Failed to fetch HTML for %s: %s", page_url, e)
                return ""

        # ── 3. Extract Data from Each SourcePage ───────────────────────────────
        for idx, page in enumerate(source_pages, 1):
            logger.debug(
                "Task %s: Extracting page [%d/%d] %s (%s)",
                task.task_id,
                idx,
                total_pages,
                page.url,
                page.page_type,
            )

            html_text = await get_html(page.url, client)
            if not html_text:
                continue

            ctx = PageContext(
                task_id=task.id,
                organization_id=page.organization_id,
                website_id=page.website_id,
                source_page_id=page.id,
                source_url=page.url,
                page_type=page.page_type,
                page_title=page.page_title,
            )

            try:
                extraction_res = self.extractor.extract(html=html_text, context=ctx)
            except Exception as e:
                logger.warning("Extraction failed on page %s: %s", page.url, e)
                continue

            # Persist items
            for item in extraction_res.items:
                # Always create provenance record
                self.session.add(
                    ExtractedField(
                        organization_id=page.organization_id,
                        source_page_id=page.id,
                        field_name=item.field_name,
                        field_value=item.raw_value,
                        normalized_value=item.normalized_value,
                    )
                )
                provenance_count += 1

                # 1. Phone number persistence
                if item.field_name == "PHONE":
                    stmt_phone = select(PhoneNumber).where(
                        PhoneNumber.organization_id == page.organization_id,
                        PhoneNumber.normalized_phone == item.normalized_value,
                    )
                    res_p = await self.session.execute(stmt_phone)
                    if res_p.scalar_one_or_none() is None:
                        new_phone = PhoneNumber(
                            organization_id=page.organization_id,
                            phone_number=item.metadata.get("display_phone", item.raw_value),
                            normalized_phone=item.normalized_value,
                            phone_type=item.metadata.get("phone_type", "MAIN"),
                            is_whatsapp=item.metadata.get("is_whatsapp", False),
                            is_primary=item.metadata.get("is_primary", False),
                        )
                        self.session.add(new_phone)
                        phones_count += 1

                # 2. Email persistence
                elif item.field_name == "EMAIL":
                    stmt_mail = select(EmailAddress).where(
                        EmailAddress.organization_id == page.organization_id,
                        EmailAddress.normalized_email == item.normalized_value,
                    )
                    res_m = await self.session.execute(stmt_mail)
                    if res_m.scalar_one_or_none() is None:
                        new_mail = EmailAddress(
                            organization_id=page.organization_id,
                            email=item.raw_value,
                            normalized_email=item.normalized_value,
                            email_type=item.metadata.get("email_type", "GENERAL"),
                            is_primary=item.metadata.get("is_primary", False),
                        )
                        self.session.add(new_mail)
                        emails_count += 1

                # 3. Contact Person persistence
                elif item.field_name == "CONTACT_PERSON":
                    name = item.metadata.get("name", item.normalized_value)
                    designation = item.metadata.get("designation")
                    stmt_cont = select(Contact).where(
                        Contact.organization_id == page.organization_id,
                        Contact.name == name,
                    )
                    res_c = await self.session.execute(stmt_cont)
                    if res_c.scalar_one_or_none() is None:
                        new_contact = Contact(
                            organization_id=page.organization_id,
                            name=name,
                            designation=designation,
                        )
                        self.session.add(new_contact)
                        contacts_count += 1

                # 4. Social Link persistence
                elif item.field_name == "SOCIAL_LINK":
                    stmt_soc = select(SocialLink).where(
                        SocialLink.organization_id == page.organization_id,
                        SocialLink.normalized_url == item.normalized_value,
                    )
                    res_s = await self.session.execute(stmt_soc)
                    if res_s.scalar_one_or_none() is None:
                        new_soc = SocialLink(
                            organization_id=page.organization_id,
                            platform=item.metadata.get("platform", "OTHER"),
                            url=item.raw_value,
                            normalized_url=item.normalized_value,
                            is_official=True,
                        )
                        self.session.add(new_soc)
                        socials_count += 1

                # 5. Organization Address persistence
                elif item.field_name == "ADDRESS":
                    org = await self.session.get(Organization, page.organization_id)
                    if org:
                        updated = False
                        if not org.address:
                            org.address = item.normalized_value
                            updated = True
                        if not org.city and item.metadata.get("city"):
                            org.city = item.metadata["city"]
                            updated = True
                        if not org.state and item.metadata.get("state"):
                            org.state = item.metadata["state"]
                            updated = True
                        if not org.pincode and item.metadata.get("pincode"):
                            org.pincode = item.metadata["pincode"]
                            updated = True
                        if updated:
                            addresses_count += 1

            await self.session.flush()

        # ── 4. Finalize Task Metrics and Advance to CLEANING ───────────────────
        task.phones_found += phones_count
        task.emails_found += emails_count
        task.addresses_found += addresses_count
        task.current_stage = "CLEANING"
        task.progress = 70

        total_duration = time.monotonic() - start_time
        summary_msg = (
            f"Data extraction completed in {total_duration:.1f}s. "
            f"Pages Processed: {total_pages}, Phones: {phones_count}, "
            f"Emails: {emails_count}, Addresses: {addresses_count}, "
            f"Contacts: {contacts_count}, Social Links: {socials_count}, "
            f"Provenance Records: {provenance_count}."
        )

        self.session.add(
            ScrapingLog(
                task_id=task.id,
                level="INFO",
                event_type="EXTRACTION_COMPLETED",
                message=summary_msg,
            )
        )
        await self.session.commit()
        logger.info("Task %s extraction completed. Next stage: CLEANING", task.task_id)

        return TaskExtractionSummary(
            task_id=task.task_id,
            pages_processed=total_pages,
            phones_extracted=phones_count,
            emails_extracted=emails_count,
            addresses_extracted=addresses_count,
            contacts_extracted=contacts_count,
            social_links_extracted=socials_count,
            provenance_records_created=provenance_count,
            duration_seconds=total_duration,
            status="Extraction completed",
            next_stage="CLEANING",
        )
