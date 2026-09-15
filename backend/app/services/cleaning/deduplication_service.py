"""
app/services/cleaning/deduplication_service.py

Exact duplicate removal for child entities (phones, emails, websites, social links, source pages)
within an individual organization, ensuring zero loss of provenance and resolving primary designations.
"""

from __future__ import annotations

import uuid
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_address import EmailAddress
from app.models.extracted_field import ExtractedField
from app.models.phone_number import PhoneNumber
from app.models.social_link import SocialLink
from app.models.source_page import SourcePage
from app.models.website import Website


class DeduplicationService:
    """Removes exact duplicate records within an organization while preserving provenance."""

    @classmethod
    async def deduplicate_organization(
        cls,
        session: AsyncSession,
        organization_id: uuid.UUID,
    ) -> dict[str, int]:
        """Deduplicate all child entities for a specific organization.

        Returns:
            Dictionary of counts removed per entity type.
        """
        counts = {
            "phones": 0,
            "emails": 0,
            "websites": 0,
            "socials": 0,
            "source_pages": 0,
        }

        # ── 1. Deduplicate Phone Numbers ──────────────────────────────────────
        stmt_p = select(PhoneNumber).where(PhoneNumber.organization_id == organization_id)
        phones = list((await session.execute(stmt_p)).scalars().all())

        phones_by_norm: dict[str, list[PhoneNumber]] = defaultdict(list)
        for p in phones:
            norm_p = (p.normalized_phone or p.phone_number or "").strip()
            phones_by_norm[norm_p].append(p)

        for norm_phone, group in phones_by_norm.items():
            if len(group) > 1:
                group.sort(
                    key=lambda x: (
                        1 if x.is_primary else 0,
                        1 if x.is_whatsapp else 0,
                        1 if x.phone_type in ("MAIN", "OFFICE", "ADMISSIONS") else 0,
                    ),
                    reverse=True,
                )
                canonical_p = group[0]
                for dup in group[1:]:
                    if dup.is_whatsapp:
                        canonical_p.is_whatsapp = True
                    await session.delete(dup)
                    counts["phones"] += 1

        # Resolve primary phone if none set
        remaining_phones = list((await session.execute(stmt_p)).scalars().all())
        if remaining_phones and not any(p.is_primary for p in remaining_phones):
            remaining_phones.sort(
                key=lambda x: 1 if x.phone_type in ("MAIN", "OFFICE", "ADMISSIONS") else 0,
                reverse=True,
            )
            remaining_phones[0].is_primary = True

        # ── 2. Deduplicate Email Addresses ────────────────────────────────────
        stmt_e = select(EmailAddress).where(EmailAddress.organization_id == organization_id)
        emails = list((await session.execute(stmt_e)).scalars().all())

        emails_by_norm: dict[str, list[EmailAddress]] = defaultdict(list)
        for e in emails:
            norm_e = (e.normalized_email or e.email or "").lower().strip()
            emails_by_norm[norm_e].append(e)

        for norm_email, group in emails_by_norm.items():
            if len(group) > 1:
                group.sort(
                    key=lambda x: (
                        1 if x.is_primary else 0,
                        1 if x.email_type in ("GENERAL", "CONTACT", "ADMISSIONS") else 0,
                    ),
                    reverse=True,
                )
                for dup in group[1:]:
                    await session.delete(dup)
                    counts["emails"] += 1

        # Resolve primary email if none set
        remaining_emails = list((await session.execute(stmt_e)).scalars().all())
        if remaining_emails and not any(e.is_primary for e in remaining_emails):
            remaining_emails.sort(
                key=lambda x: 1 if x.email_type in ("GENERAL", "CONTACT", "ADMISSIONS") else 0,
                reverse=True,
            )
            remaining_emails[0].is_primary = True

        # ── 3. Deduplicate Websites ───────────────────────────────────────────
        stmt_w = select(Website).where(Website.organization_id == organization_id)
        websites = list((await session.execute(stmt_w)).scalars().all())

        web_by_norm: dict[str, list[Website]] = defaultdict(list)
        for w in websites:
            norm_url = (w.normalized_url or w.url or "").rstrip("/")
            web_by_norm[norm_url].append(w)

        for norm_url, group in web_by_norm.items():
            if len(group) > 1:
                group.sort(key=lambda x: 1 if x.is_official else 0, reverse=True)
                canonical_w = group[0]
                for dup in group[1:]:
                    stmt_sp_reparent = select(SourcePage).where(SourcePage.website_id == dup.id)
                    sp_list = list((await session.execute(stmt_sp_reparent)).scalars().all())
                    for sp in sp_list:
                        sp.website_id = canonical_w.id
                    await session.delete(dup)
                    counts["websites"] += 1

        # ── 4. Deduplicate Social Links ───────────────────────────────────────
        stmt_s = select(SocialLink).where(SocialLink.organization_id == organization_id)
        socials = list((await session.execute(stmt_s)).scalars().all())

        soc_by_norm: dict[str, list[SocialLink]] = defaultdict(list)
        for s in socials:
            norm_url = (s.normalized_url or s.url or "").rstrip("/")
            soc_by_norm[norm_url].append(s)

        for norm_url, group in soc_by_norm.items():
            if len(group) > 1:
                group.sort(key=lambda x: 1 if x.is_official else 0, reverse=True)
                for dup in group[1:]:
                    await session.delete(dup)
                    counts["socials"] += 1

        # ── 5. Deduplicate Source Pages ───────────────────────────────────────
        stmt_sp = select(SourcePage).where(SourcePage.organization_id == organization_id)
        source_pages = list((await session.execute(stmt_sp)).scalars().all())

        sp_by_norm: dict[str, list[SourcePage]] = defaultdict(list)
        for sp in source_pages:
            norm_url = (sp.normalized_url or sp.url or "").rstrip("/")
            sp_by_norm[norm_url].append(sp)

        for norm_url, group in sp_by_norm.items():
            if len(group) > 1:
                canonical_sp = group[0]
                for dup in group[1:]:
                    stmt_ef = select(ExtractedField).where(ExtractedField.source_page_id == dup.id)
                    ef_list = list((await session.execute(stmt_ef)).scalars().all())
                    for ef in ef_list:
                        ef.source_page_id = canonical_sp.id
                        ef.source_page = canonical_sp
                    if "extracted_fields" in dup.__dict__:
                        dup.extracted_fields.clear()
                    await session.delete(dup)
                    counts["source_pages"] += 1

        await session.flush()
        return counts
