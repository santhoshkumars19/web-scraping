"""
app/services/cleaning/merge_service.py

Safe organization merging with canonical selection, zero provenance loss,
child entity re-parenting, and audit logging via OrganizationMergeEvent.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.models.email_address import EmailAddress
from app.models.extracted_field import ExtractedField
from app.models.lead import Lead
from app.models.lead_verification import LeadVerification
from app.models.organization import Organization, task_organizations
from app.models.organization_merge_event import OrganizationMergeEvent
from app.models.phone_number import PhoneNumber
from app.models.scraping_log import ScrapingLog
from app.models.social_link import SocialLink
from app.models.source_page import SourcePage
from app.models.website import Website
from app.services.cleaning.deduplication_service import DeduplicationService


class MergeService:
    """Handles the safe merging of two duplicate organizations into one canonical record."""

    @classmethod
    async def select_canonical(
        cls,
        session: AsyncSession,
        org1: Organization,
        org2: Organization,
    ) -> tuple[Organization, Organization]:
        """Select the canonical organization and source organization based on deterministic criteria.

        Priority:
        1. Official website presence
        2. Field completeness (category, address, city, state, pincode)
        3. Total child records count
        4. Older record creation timestamp
        """

        async def get_score(org: Organization) -> tuple[int, int, int, float]:
            # 1. Official website
            stmt_w = select(func.count()).select_from(Website).where(
                Website.organization_id == org.id,
                Website.is_official.is_(True),
            )
            official_count = (await session.execute(stmt_w)).scalar() or 0
            has_official = 1 if official_count > 0 else 0

            # 2. Field completeness
            completeness = sum(
                1
                for f in [org.category, org.address, org.city, org.state, org.pincode]
                if f and f.strip()
            )

            # 3. Child counts
            w_cnt = (await session.execute(select(func.count()).select_from(Website).where(Website.organization_id == org.id))).scalar() or 0
            p_cnt = (await session.execute(select(func.count()).select_from(PhoneNumber).where(PhoneNumber.organization_id == org.id))).scalar() or 0
            e_cnt = (await session.execute(select(func.count()).select_from(EmailAddress).where(EmailAddress.organization_id == org.id))).scalar() or 0
            c_cnt = (await session.execute(select(func.count()).select_from(Contact).where(Contact.organization_id == org.id))).scalar() or 0
            total_children = w_cnt + p_cnt + e_cnt + c_cnt

            created_ts = -org.created_at.timestamp() if org.created_at else 0.0
            return (has_official, completeness, total_children, created_ts)

        score1 = await get_score(org1)
        score2 = await get_score(org2)

        if score1 >= score2:
            return org1, org2
        return org2, org1

    @classmethod
    async def merge_organizations(
        cls,
        session: AsyncSession,
        org1: Organization,
        org2: Organization,
        match_score: int,
        match_reasons: list[str],
    ) -> dict[str, Any]:
        """Safely merge two duplicate organizations.

        Preserves all child entities and provenance logs under the canonical organization,
        records an OrganizationMergeEvent audit log, and deletes the duplicate organization.

        Returns:
            Dictionary containing canonical_organization, merged_source_id, and dedup_counts.
        """
        canonical_org, source_org = await cls.select_canonical(session, org1, org2)
        source_id = source_org.id
        canonical_id = canonical_org.id

        # ── 1. Backfill Missing Core Fields on Canonical Org ──────────────────
        if not canonical_org.category and source_org.category:
            canonical_org.category = source_org.category
        if not canonical_org.address and source_org.address:
            canonical_org.address = source_org.address
        if not canonical_org.city and source_org.city:
            canonical_org.city = source_org.city
        if not canonical_org.state and source_org.state:
            canonical_org.state = source_org.state
        if not canonical_org.pincode and source_org.pincode:
            canonical_org.pincode = source_org.pincode

        # ── 2. Re-parent / Deduplicate Websites ────────────────────────────────
        stmt_cw = select(Website).where(Website.organization_id == canonical_id)
        canon_webs = {w.normalized_url: w for w in (await session.execute(stmt_cw)).scalars().all()}

        stmt_sw = select(Website).where(Website.organization_id == source_id)
        source_webs = list((await session.execute(stmt_sw)).scalars().all())

        for w in source_webs:
            if w.normalized_url in canon_webs:
                canon_w = canon_webs[w.normalized_url]
                if w.is_official and not canon_w.is_official:
                    canon_w.is_official = True
                # Re-parent any source pages pointing to w.id to canon_w.id
                stmt_sp_reparent = select(SourcePage).where(SourcePage.website_id == w.id)
                for sp in (await session.execute(stmt_sp_reparent)).scalars().all():
                    sp.website_id = canon_w.id
                await session.delete(w)
            else:
                w.organization_id = canonical_id
                canon_webs[w.normalized_url] = w

        # ── 3. Re-parent / Deduplicate Phone Numbers ───────────────────────────
        stmt_cp = select(PhoneNumber).where(PhoneNumber.organization_id == canonical_id)
        canon_phones = {p.normalized_phone: p for p in (await session.execute(stmt_cp)).scalars().all()}

        stmt_sp = select(PhoneNumber).where(PhoneNumber.organization_id == source_id)
        source_phones = list((await session.execute(stmt_sp)).scalars().all())

        for p in source_phones:
            if p.normalized_phone in canon_phones:
                canon_p = canon_phones[p.normalized_phone]
                if p.is_primary and not canon_p.is_primary:
                    canon_p.is_primary = True
                if p.is_whatsapp and not canon_p.is_whatsapp:
                    canon_p.is_whatsapp = True
                await session.delete(p)
            else:
                p.organization_id = canonical_id
                canon_phones[p.normalized_phone] = p

        # ── 4. Re-parent / Deduplicate Email Addresses ─────────────────────────
        stmt_ce = select(EmailAddress).where(EmailAddress.organization_id == canonical_id)
        canon_emails = {
            e.normalized_email.lower(): e
            for e in (await session.execute(stmt_ce)).scalars().all()
        }

        stmt_se = select(EmailAddress).where(EmailAddress.organization_id == source_id)
        source_emails = list((await session.execute(stmt_se)).scalars().all())

        for e in source_emails:
            norm_e = e.normalized_email.lower()
            if norm_e in canon_emails:
                canon_e = canon_emails[norm_e]
                if e.is_primary and not canon_e.is_primary:
                    canon_e.is_primary = True
                await session.delete(e)
            else:
                e.organization_id = canonical_id
                canon_emails[norm_e] = e

        # ── 5. Re-parent / Deduplicate Social Links ───────────────────────────
        stmt_cs = select(SocialLink).where(SocialLink.organization_id == canonical_id)
        canon_socials = {s.normalized_url: s for s in (await session.execute(stmt_cs)).scalars().all()}

        stmt_ss = select(SocialLink).where(SocialLink.organization_id == source_id)
        source_socials = list((await session.execute(stmt_ss)).scalars().all())

        for s in source_socials:
            if s.normalized_url in canon_socials:
                canon_s = canon_socials[s.normalized_url]
                if s.is_official and not canon_s.is_official:
                    canon_s.is_official = True
                await session.delete(s)
            else:
                s.organization_id = canonical_id
                canon_socials[s.normalized_url] = s

        # ── 6. Re-parent Contacts ─────────────────────────────────────────────
        stmt_sc = select(Contact).where(Contact.organization_id == source_id)
        source_contacts = list((await session.execute(stmt_sc)).scalars().all())
        for c in source_contacts:
            c.organization_id = canonical_id

        # ── 7. Re-parent Source Pages ─────────────────────────────────────────
        stmt_csp = select(SourcePage).where(SourcePage.organization_id == canonical_id)
        canon_pages = {
            (sp.website_id, sp.normalized_url): sp
            for sp in (await session.execute(stmt_csp)).scalars().all()
        }

        stmt_ssp = select(SourcePage).where(SourcePage.organization_id == source_id)
        source_pages = list((await session.execute(stmt_ssp)).scalars().all())

        for sp in source_pages:
            key = (sp.website_id, sp.normalized_url)
            if key in canon_pages:
                canon_sp = canon_pages[key]
                stmt_ef = select(ExtractedField).where(ExtractedField.source_page_id == sp.id)
                for ef in (await session.execute(stmt_ef)).scalars().all():
                    ef.source_page_id = canon_sp.id
                    ef.source_page = canon_sp
                if "extracted_fields" in sp.__dict__:
                    sp.extracted_fields.clear()
                await session.delete(sp)
            else:
                sp.organization_id = canonical_id
                canon_pages[key] = sp

        # ── 8. Re-parent ExtractedField Provenance Records ────────────────────
        stmt_ef = select(ExtractedField).where(ExtractedField.organization_id == source_id)
        for ef in (await session.execute(stmt_ef)).scalars().all():
            ef.organization_id = canonical_id

        # ── 9. Re-parent ScrapingLogs ─────────────────────────────────────────
        stmt_sl = select(ScrapingLog).where(ScrapingLog.organization_id == source_id)
        for sl in (await session.execute(stmt_sl)).scalars().all():
            sl.organization_id = canonical_id

        # Also update any pending uncommitted ScrapingLog objects in session.new
        for obj in list(session.new):
            if isinstance(obj, ScrapingLog) and getattr(obj, "organization_id", None) == source_id:
                obj.organization_id = canonical_id

        # ── 10. Re-link Task Organizations (M2M) ──────────────────────────────
        stmt_c_tasks = select(task_organizations.c.task_id).where(
            task_organizations.c.organization_id == canonical_id
        )
        canon_task_ids = set((await session.execute(stmt_c_tasks)).scalars().all())

        stmt_s_tasks = select(task_organizations.c.task_id).where(
            task_organizations.c.organization_id == source_id
        )
        source_task_ids = set((await session.execute(stmt_s_tasks)).scalars().all())

        for tid in source_task_ids:
            if tid not in canon_task_ids:
                await session.execute(
                    task_organizations.insert().values(
                        task_id=tid,
                        organization_id=canonical_id,
                    )
                )
                canon_task_ids.add(tid)

        if "tasks" in source_org.__dict__:
            source_org.tasks.clear()
        else:
            await session.execute(
                delete(task_organizations).where(
                    task_organizations.c.organization_id == source_id
                )
            )

        # ── 11. Deduplicate & Re-parent Lead Records ──────────────────────────
        stmt_c_leads = select(Lead).where(Lead.organization_id == canonical_id)
        canon_leads = list((await session.execute(stmt_c_leads)).scalars().all())
        canon_lead_task_ids = {l.task_id for l in canon_leads}

        stmt_s_leads = select(Lead).where(Lead.organization_id == source_id)
        source_leads = list((await session.execute(stmt_s_leads)).scalars().all())

        for s_lead in source_leads:
            if s_lead.task_id in canon_lead_task_ids:
                await session.delete(s_lead)
            else:
                s_lead.organization_id = canonical_id

        # ── 12. LeadVerification Migration ────────────────────────────────────
        stmt_sv = select(LeadVerification).where(LeadVerification.organization_id == source_id)
        source_verif = (await session.execute(stmt_sv)).scalar_one_or_none()
        if source_verif:
            stmt_cv = select(LeadVerification).where(LeadVerification.organization_id == canonical_id)
            canon_verif = (await session.execute(stmt_cv)).scalar_one_or_none()
            if not canon_verif:
                source_verif.organization_id = canonical_id
            else:
                await session.delete(source_verif)

        # ── 13. Record Audit Log in OrganizationMergeEvent ────────────────────
        merge_event = OrganizationMergeEvent(
            source_organization_id=source_id,
            target_organization_id=canonical_id,
            match_score=match_score,
            match_reasons=match_reasons,
        )
        session.add(merge_event)

        # ── 14. Delete Duplicate Source Organization ──────────────────────────
        # Do not call .clear() on delete-orphan relationships because re-parented children
        # now belong to canonical_id. Simply delete the source organization object.
        await session.delete(source_org)
        await session.flush()

        # ── 15. Final Child Deduplication on Canonical Org ────────────────────
        dedup_counts = await DeduplicationService.deduplicate_organization(
            session, canonical_id
        )

        return {
            "canonical_organization": canonical_org,
            "merged_source_id": source_id,
            "match_score": match_score,
            "dedup_counts": dedup_counts,
        }
