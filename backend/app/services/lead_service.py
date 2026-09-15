"""
app/services/lead_service.py

LeadService — business logic, access control, and DTO transformation
for the Leads REST API layer.
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.models.lead import Lead
from app.models.scraping_task import ScrapingTask
from app.repositories.lead_repository import LeadRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.lead import (
    LeadContact,
    LeadEmail,
    LeadListItem,
    LeadOrganization,
    LeadPhone,
    LeadResponse,
    LeadSocialLink,
    LeadSourceRecord,
    LeadTaskSummary,
    LeadVerificationDetail,
    LeadVerificationSummary,
    LeadWebsite,
)

logger = get_logger(__name__)

# Development demo user ID scoped for single-tenant / development use
DEMO_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


class LeadService:
    """Service handling lead retrieval, filtering, pagination, and response mapping."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = LeadRepository(db)
        self.task_repo = TaskRepository(db)

    # ── Mapping Helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _map_lead_to_list_item(lead: Lead) -> LeadListItem:
        """Transform a Lead model into a lightweight LeadListItem DTO."""
        org = lead.organization
        websites = org.websites if org else []
        phone_numbers = org.phone_numbers if org else []
        emails = org.email_addresses if org else []
        contacts = org.contacts if org else []

        # Website: prioritize official, exclude FAILED status or .example domains
        valid_websites = [
            w for w in websites
            if w.url and not w.url.endswith(".example") and ".example/" not in w.url and getattr(w, "status", "") != "FAILED"
        ]
        official = next((w.url for w in valid_websites if getattr(w, "is_official", False)), None)
        website_url = official or (valid_websites[0].url if valid_websites else None)

        # Phone numbers: primary or first available
        primary_phone = next((p.phone_number for p in phone_numbers if p.is_primary), None)
        if not primary_phone and phone_numbers:
            primary_phone = phone_numbers[0].phone_number

        # Alternate phone: first phone that is not the primary phone
        alternate_phones = [p.phone_number for p in phone_numbers if p.phone_number != primary_phone]
        alternate_phone = alternate_phones[0] if alternate_phones else None

        # WhatsApp
        whatsapp_phone = next((p.phone_number for p in phone_numbers if p.is_whatsapp), None)

        # Email: primary or first available
        primary_email = next((e.email for e in emails if e.is_primary), None)
        if not primary_email and emails:
            primary_email = emails[0].email

        # Contact person & designation
        contact_person = contacts[0].name if contacts else None
        designation = contacts[0].designation if contacts else None

        # Location string formatting
        location_parts = [p for p in (org.city if org else None, org.state if org else None) if p]
        location_str = ", ".join(location_parts) if location_parts else None

        # Verification summary
        v = lead.verification
        if v:
            verification_summary = LeadVerificationSummary(
                status=v.status,
                score=v.score,
                fields_found=v.fields_found,
                total_fields=v.total_fields,
            )
        else:
            verification_summary = LeadVerificationSummary(
                status=lead.verification_status,
                score=0,
                fields_found=0,
                total_fields=0,
            )

        lead_org = LeadOrganization(
            id=org.id if org else uuid.uuid4(),
            name=org.name if org else "Unknown",
            category=org.category if org else None,
            website=website_url,
            address=org.address if org else None,
            city=org.city if org else None,
            state=org.state if org else None,
            pincode=org.pincode if org else None,
        )

        task_id_str = lead.task.task_id if lead.task else ""

        return LeadListItem(
            id=str(lead.id),
            task_id=task_id_str,
            organization=lead_org,
            phone=primary_phone,
            alternate_phone=alternate_phone,
            whatsapp=whatsapp_phone,
            email=primary_email,
            website=website_url,
            location=location_str,
            contact_person=contact_person,
            designation=designation,
            verification=verification_summary,
            scraped_date=lead.created_at,
        )

    @staticmethod
    def _map_lead_to_detail(lead: Lead) -> LeadResponse:
        """Transform a Lead model into a full LeadResponse DTO with all relations and sources."""
        org = lead.organization
        websites = org.websites if org else []
        phones = org.phone_numbers if org else []
        emails = org.email_addresses if org else []
        contacts = org.contacts if org else []
        social_links = org.social_links if org else []
        source_pages = org.source_pages if org else []

        # Organization DTO
        valid_websites = [
            w for w in websites
            if w.url and not w.url.endswith(".example") and ".example/" not in w.url and getattr(w, "status", "") != "FAILED"
        ]
        official = next((w.url for w in valid_websites if getattr(w, "is_official", False)), None)
        primary_website = official or (valid_websites[0].url if valid_websites else None)
        lead_org = LeadOrganization(
            id=org.id if org else uuid.uuid4(),
            name=org.name if org else "Unknown",
            category=org.category if org else None,
            website=primary_website,
            address=org.address if org else None,
            city=org.city if org else None,
            state=org.state if org else None,
            pincode=org.pincode if org else None,
        )

        # Task summary
        task_summary = None
        if lead.task:
            task_summary = LeadTaskSummary(
                task_id=lead.task.task_id,
                keyword=lead.task.keyword,
                location=lead.task.location,
                status=lead.task.status,
                created_at=lead.task.created_at,
                completed_at=lead.task.completed_at,
            )

        # Related collections
        websites_dto = [
            LeadWebsite(
                id=w.id,
                url=w.url,
                domain=w.domain,
                is_official=w.is_official,
            )
            for w in websites
        ]

        phones_dto = [
            LeadPhone(
                id=p.id,
                number=p.phone_number,
                normalized_number=p.normalized_phone,
                type=p.phone_type,
                is_primary=p.is_primary,
                is_whatsapp=p.is_whatsapp,
            )
            for p in phones
        ]

        emails_dto = [
            LeadEmail(
                id=e.id,
                email=e.email,
                normalized_email=e.normalized_email,
                type=e.email_type,
                is_primary=e.is_primary,
            )
            for e in emails
        ]

        contacts_dto = [
            LeadContact(
                id=c.id,
                name=c.name,
                designation=c.designation,
            )
            for c in contacts
        ]

        social_dto = [
            LeadSocialLink(
                platform=s.platform,
                url=s.url,
                is_official=s.is_official,
            )
            for s in social_links
        ]

        # Field provenance sources
        sources_dto: list[LeadSourceRecord] = []
        for sp in source_pages:
            extracted_fields = getattr(sp, "extracted_fields", [])
            for ef in extracted_fields:
                sources_dto.append(
                    LeadSourceRecord(
                        field=ef.field_name,
                        value=ef.field_value,
                        source_url=sp.url,
                        page_type=sp.page_type,
                        page_title=sp.page_title,
                    )
                )
            if not extracted_fields:
                sources_dto.append(
                    LeadSourceRecord(
                        field="page",
                        value=sp.url,
                        source_url=sp.url,
                        page_type=sp.page_type,
                        page_title=sp.page_title,
                    )
                )

        # Verification detail
        v = lead.verification
        if v:
            verification_detail = LeadVerificationDetail(
                status=v.status,
                score=v.score,
                fields_found=v.fields_found,
                total_fields=v.total_fields,
                completeness_percentage=v.completeness_percentage,
                source_quality_score=v.source_quality_score,
                consistency_score=v.consistency_score,
                reasons=v.verification_reasons or {},
                source_quality_details=v.source_quality_details or {},
                verified_at=v.verified_at,
            )
        else:
            verification_detail = LeadVerificationDetail(
                status=lead.verification_status,
                score=0,
                fields_found=0,
                total_fields=0,
                completeness_percentage=0.0,
                source_quality_score=0.0,
                consistency_score=0.0,
                reasons={},
                source_quality_details={},
                verified_at=None,
            )

        task_id_str = lead.task.task_id if lead.task else ""

        return LeadResponse(
            id=str(lead.id),
            task_id=task_id_str,
            task=task_summary,
            organization=lead_org,
            websites=websites_dto,
            phones=phones_dto,
            emails=emails_dto,
            contacts=contacts_dto,
            social_links=social_dto,
            sources=sources_dto,
            verification=verification_detail,
            scraped_date=lead.created_at,
        )

    # ── Service Methods ────────────────────────────────────────────────────────

    async def get_lead(
        self,
        lead_id: str | uuid.UUID,
        user_id: uuid.UUID | None = None,
    ) -> LeadResponse:
        """Fetch a single lead profile with full provenance and relation details.

        Raises:
            AppException(404, "LEAD_NOT_FOUND") if not found.
        """
        lead = await self.repo.get_by_id(lead_id, user_id=user_id)
        if not lead:
            raise AppException(
                message=f"Lead '{lead_id}' not found.",
                status_code=404,
                code="LEAD_NOT_FOUND",
            )
        return self._map_lead_to_detail(lead)

    async def list_leads(
        self,
        *,
        task_id: str | uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
        search: str | None = None,
        category: str | None = None,
        location: str | None = None,
        verification: str | None = None,
        has_phone: bool | None = None,
        has_email: bool | None = None,
        has_website: bool | None = None,
        has_whatsapp: bool | None = None,
        has_contact: bool | None = None,
        has_social: bool | None = None,
        scraped_from: datetime | None = None,
        scraped_to: datetime | None = None,
        sort_by: str = "scraped_date",
        sort_order: str = "desc",
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[LeadListItem], int, int]:
        """Query leads with filtering, search, and pagination.

        Returns (items, total_count, total_pages).
        """
        leads, total_count = await self.repo.list_leads(
            task_id=task_id,
            user_id=user_id,
            search=search,
            category=category,
            location=location,
            verification=verification,
            has_phone=has_phone,
            has_email=has_email,
            has_website=has_website,
            has_whatsapp=has_whatsapp,
            has_contact=has_contact,
            has_social=has_social,
            scraped_from=scraped_from,
            scraped_to=scraped_to,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            limit=limit,
        )

        total_pages = math.ceil(total_count / limit) if total_count > 0 else 0
        items = [self._map_lead_to_list_item(lead) for lead in leads]
        return items, total_count, total_pages

    async def list_task_leads(
        self,
        task_id: str,
        *,
        user_id: uuid.UUID | None = None,
        search: str | None = None,
        category: str | None = None,
        location: str | None = None,
        verification: str | None = None,
        has_phone: bool | None = None,
        has_email: bool | None = None,
        has_website: bool | None = None,
        has_whatsapp: bool | None = None,
        has_contact: bool | None = None,
        has_social: bool | None = None,
        scraped_from: datetime | None = None,
        scraped_to: datetime | None = None,
        sort_by: str = "scraped_date",
        sort_order: str = "desc",
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[LeadListItem], int, int]:
        """Query leads scoped to a specific task.

        Validates task existence; raises 404 TASK_NOT_FOUND if task does not exist
        or does not belong to the user.
        Returns empty list with total_count=0 if task exists but has no leads.
        """
        # First verify task exists and belongs to user if user_id is provided
        task = await self.task_repo.get_by_task_id(task_id, user_id=user_id)
        if not task:
            # Check if task_id is a UUID
            try:
                task_uuid = uuid.UUID(task_id)
                stmt = select(ScrapingTask).where(ScrapingTask.id == task_uuid)
                if user_id is not None:
                    stmt = stmt.where(ScrapingTask.user_id == user_id)
                res = await self.db.execute(stmt)
                task = res.scalar_one_or_none()
            except ValueError:
                task = None

        if not task:
            raise AppException(
                message=f"Task '{task_id}' not found.",
                status_code=404,
                code="TASK_NOT_FOUND",
            )

        return await self.list_leads(
            task_id=task.task_id,
            user_id=user_id,
            search=search,
            category=category,
            location=location,
            verification=verification,
            has_phone=has_phone,
            has_email=has_email,
            has_website=has_website,
            has_whatsapp=has_whatsapp,
            has_contact=has_contact,
            has_social=has_social,
            scraped_from=scraped_from,
            scraped_to=scraped_to,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            limit=limit,
        )
