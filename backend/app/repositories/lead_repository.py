"""
app/repositories/lead_repository.py

LeadRepository — data access layer for Lead records with optimized eager-loading,
multi-criteria search, boolean facet filters, sorting, and database-level pagination.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Sequence

import sqlalchemy as sa
from sqlalchemy import distinct, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.contact import Contact
from app.models.email_address import EmailAddress
from app.models.extracted_field import ExtractedField
from app.models.lead import Lead
from app.models.lead_verification import LeadVerification
from app.models.organization import Organization
from app.models.phone_number import PhoneNumber
from app.models.scraping_task import ScrapingTask
from app.models.social_link import SocialLink
from app.models.source_page import SourcePage
from app.models.website import Website


class LeadRepository:
    """Repository handling querying and retrieval of Lead records."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(
        self,
        lead_id: uuid.UUID | str,
        user_id: uuid.UUID | None = None,
    ) -> Lead | None:
        """Fetch a single Lead by its primary key with complete relationship graph eagerly loaded."""
        if isinstance(lead_id, str):
            try:
                lead_id = uuid.UUID(lead_id)
            except ValueError:
                return None

        stmt = (
            select(Lead)
            .join(Lead.task)
            .where(Lead.id == lead_id, Lead.deleted_at.is_(None))
            .options(
                selectinload(Lead.task),
                selectinload(Lead.verification),
                selectinload(Lead.organization).selectinload(Organization.websites),
                selectinload(Lead.organization).selectinload(Organization.phone_numbers),
                selectinload(Lead.organization).selectinload(Organization.email_addresses),
                selectinload(Lead.organization).selectinload(Organization.contacts),
                selectinload(Lead.organization).selectinload(Organization.social_links),
                selectinload(Lead.organization)
                .selectinload(Organization.source_pages)
                .selectinload(SourcePage.extracted_fields),
            )
        )
        if user_id is not None:
            stmt = stmt.where(ScrapingTask.user_id == user_id)

        result = await self.db.execute(stmt)
        return result.scalars().first()

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
    ) -> tuple[Sequence[Lead], int]:
        """Query leads with filtering, search, sorting, and database-level pagination.

        Returns (leads, total_count).
        """
        # Base query joining Organization and ScrapingTask
        base_query = (
            select(Lead)
            .join(Lead.organization)
            .join(Lead.task)
            .where(Lead.deleted_at.is_(None))
        )

        conditions: list[sa.sql.elements.BinaryExpression | sa.sql.elements.BooleanClauseList] = []

        # ── User scoping ──────────────────────────────────────────────────────
        if user_id is not None:
            conditions.append(ScrapingTask.user_id == user_id)

        # ── Task scoping ──────────────────────────────────────────────────────
        if task_id is not None:
            if isinstance(task_id, str):
                if task_id.startswith("TASK-"):
                    conditions.append(ScrapingTask.task_id == task_id)
                else:
                    try:
                        task_uuid = uuid.UUID(task_id)
                        conditions.append(or_(Lead.task_id == task_uuid, ScrapingTask.task_id == task_id))
                    except ValueError:
                        conditions.append(ScrapingTask.task_id == task_id)
            elif isinstance(task_id, uuid.UUID):
                conditions.append(Lead.task_id == task_id)

        # ── Multi-field case-insensitive search ──────────────────────────────
        if search and search.strip():
            term = f"%{search.strip()}%"
            search_predicates = [
                Organization.name.ilike(term),
                Organization.category.ilike(term),
                Organization.city.ilike(term),
                Organization.state.ilike(term),
                Organization.address.ilike(term),
                select(1)
                .select_from(Website)
                .where(Website.organization_id == Organization.id, Website.url.ilike(term))
                .exists(),
                select(1)
                .select_from(PhoneNumber)
                .where(
                    PhoneNumber.organization_id == Organization.id,
                    or_(
                        PhoneNumber.phone_number.ilike(term),
                        PhoneNumber.normalized_phone.ilike(term),
                    ),
                )
                .exists(),
                select(1)
                .select_from(EmailAddress)
                .where(
                    EmailAddress.organization_id == Organization.id,
                    or_(
                        EmailAddress.email.ilike(term),
                        EmailAddress.normalized_email.ilike(term),
                    ),
                )
                .exists(),
                select(1)
                .select_from(Contact)
                .where(Contact.organization_id == Organization.id, Contact.name.ilike(term))
                .exists(),
            ]
            conditions.append(or_(*search_predicates))

        # ── Specific field filters ───────────────────────────────────────────
        if category and category.strip():
            conditions.append(Organization.category.ilike(f"%{category.strip()}%"))

        if location and location.strip():
            loc_term = f"%{location.strip()}%"
            conditions.append(
                or_(
                    Organization.city.ilike(loc_term),
                    Organization.state.ilike(loc_term),
                    Organization.address.ilike(loc_term),
                )
            )

        if verification and verification.strip():
            v_val = verification.strip().upper()
            conditions.append(Lead.verification_status == v_val)

        # ── Data Availability Facets (EXISTS subqueries) ──────────────────────
        if has_phone is not None:
            phone_exists = (
                select(1)
                .select_from(PhoneNumber)
                .where(PhoneNumber.organization_id == Organization.id)
                .exists()
            )
            conditions.append(phone_exists if has_phone else ~phone_exists)

        if has_email is not None:
            email_exists = (
                select(1)
                .select_from(EmailAddress)
                .where(EmailAddress.organization_id == Organization.id)
                .exists()
            )
            conditions.append(email_exists if has_email else ~email_exists)

        if has_website is not None:
            website_exists = (
                select(1)
                .select_from(Website)
                .where(Website.organization_id == Organization.id)
                .exists()
            )
            conditions.append(website_exists if has_website else ~website_exists)

        if has_whatsapp is not None:
            whatsapp_exists = (
                select(1)
                .select_from(PhoneNumber)
                .where(
                    PhoneNumber.organization_id == Organization.id,
                    PhoneNumber.is_whatsapp.is_(True),
                )
                .exists()
            )
            conditions.append(whatsapp_exists if has_whatsapp else ~whatsapp_exists)

        if has_contact is not None:
            contact_exists = (
                select(1)
                .select_from(Contact)
                .where(Contact.organization_id == Organization.id)
                .exists()
            )
            conditions.append(contact_exists if has_contact else ~contact_exists)

        if has_social is not None:
            social_exists = (
                select(1)
                .select_from(SocialLink)
                .where(SocialLink.organization_id == Organization.id)
                .exists()
            )
            conditions.append(social_exists if has_social else ~social_exists)

        # ── Date range filters ───────────────────────────────────────────────
        if scraped_from is not None:
            conditions.append(Lead.created_at >= scraped_from)

        if scraped_to is not None:
            conditions.append(Lead.created_at <= scraped_to)

        # Apply all filter predicates
        if conditions:
            base_query = base_query.where(*conditions)

        # ── Total count query ────────────────────────────────────────────────
        count_stmt = (
            select(func.count(distinct(Lead.id)))
            .join(Lead.organization)
            .join(Lead.task)
            .where(Lead.deleted_at.is_(None))
        )
        if conditions:
            count_stmt = count_stmt.where(*conditions)

        total_count = (await self.db.execute(count_stmt)).scalar() or 0

        # ── Sorting ──────────────────────────────────────────────────────────
        is_desc = sort_order.lower() == "desc"

        if sort_by == "organization":
            sort_column = Organization.name.desc() if is_desc else Organization.name.asc()
        elif sort_by == "category":
            sort_column = Organization.category.desc() if is_desc else Organization.category.asc()
        elif sort_by == "location":
            sort_column = Organization.city.desc() if is_desc else Organization.city.asc()
        elif sort_by == "verification":
            sort_column = Lead.verification_status.desc() if is_desc else Lead.verification_status.asc()
        else:  # "scraped_date" or default
            sort_column = Lead.created_at.desc() if is_desc else Lead.created_at.asc()

        query = (
            base_query.order_by(sort_column, Lead.id.desc())
            .offset((page - 1) * limit)
            .limit(limit)
            .options(
                selectinload(Lead.task),
                selectinload(Lead.verification),
                selectinload(Lead.organization).selectinload(Organization.websites),
                selectinload(Lead.organization).selectinload(Organization.phone_numbers),
                selectinload(Lead.organization).selectinload(Organization.email_addresses),
                selectinload(Lead.organization).selectinload(Organization.contacts),
                selectinload(Lead.organization).selectinload(Organization.social_links),
            )
        )

        result = await self.db.execute(query)
        leads = result.scalars().all()
        return leads, total_count
