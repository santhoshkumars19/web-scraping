"""
scripts/verify_live_discovery.py

Safe development CLI command to execute and verify the live public-web discovery pipeline
with zero mock data.

Usage:
    python scripts/verify_live_discovery.py --location "Ooty" --category "Restaurants" --limit 10
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import uuid

import sys

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure backend root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import create_engine_and_factory, get_session_factory
from app.jobs.cleaning_job import run_cleaning
from app.jobs.crawl_job import run_crawl
from app.jobs.discovery_job import run_discovery
from app.jobs.extraction_job import run_extraction
from app.jobs.finalization_job import run_finalize
from app.jobs.verification_job import run_verification
from app.models.contact import Contact
from app.models.email_address import EmailAddress
from app.models.lead import Lead
from app.models.organization import Organization, task_organizations
from app.models.phone_number import PhoneNumber
from app.models.scraping_task import ScrapingTask
from app.models.source_page import SourcePage
from app.models.user import User
from app.models.website import Website
from app.schemas.task import ScrapingTaskCreate
from app.services.task_service import TaskService


async def main() -> None:
    parser = argparse.ArgumentParser(description="Verify live discovery pipeline")
    parser.add_argument("--location", default="Ooty", help="Location (default: Ooty)")
    parser.add_argument("--category", default="Restaurants", help="Category / Keyword (default: Restaurants)")
    parser.add_argument("--limit", type=int, default=10, help="Max results limit (default: 10)")
    parser.add_argument("--max-pages", type=int, default=5, help="Max crawl pages per website (default: 5)")
    args = parser.parse_args()

    print("=" * 70)
    print("LEADSCOUT -- LIVE PUBLIC-WEB DISCOVERY VERIFICATION")
    print(f"Location: {args.location} | Category: {args.category} | Limit: {args.limit}")
    print("=" * 70)

    # Strictly ensure fixtures are disabled
    settings.DISCOVERY_ENABLE_FIXTURES = False

    create_engine_and_factory()
    factory = get_session_factory()

    async with factory() as session:
        # 1. Ensure user exists
        stmt_u = select(User).limit(1)
        res_u = await session.execute(stmt_u)
        user = res_u.scalar_one_or_none()
        if not user:
            user = User(
                name="Verification User",
                email=f"verify_{uuid.uuid4().hex[:8]}@example.com",
                password_hash="verified",
            )
            session.add(user)
            await session.flush()

        # 2. Initialize ScrapingTask
        task_service = TaskService(session)
        task_create_data = ScrapingTaskCreate(
            location=args.location,
            keyword=args.category,
            search_radius=25,
            max_results=args.limit,
            max_pages_per_site=args.max_pages,
            crawl_depth=2,
            follow_internal_links=True,
            prioritize_contact=True,
            prioritize_about=True,
            prioritize_admissions=False,
            prioritize_staff_management=False,
            selected_fields=[
                "name",
                "category",
                "phone",
                "email",
                "website",
                "address",
                "whatsapp",
                "contact_person",
                "social_links",
            ],
        )
        task_record = await task_service.create_task(task_create_data, user_id=user.id)
        task_id = task_record.task_id
        task_uuid = task_record.id

        print(f"\n[1/6] Created Task: {task_id}")

        # 3. Discovery Stage
        print(f"\n[2/6] Running Live Public Discovery for '{args.category}' in '{args.location}'...")
        discovery_res = await run_discovery(task_id, session)
        print(f"      Candidates discovered: {discovery_res.total_candidates}")
        print(f"      Candidates accepted:   {discovery_res.accepted_candidates}")
        print(f"      Duplicates removed:    {discovery_res.duplicates_removed}")
        print(f"      Websites found:        {discovery_res.websites_found}")

        # 4. Crawl Stage
        print(f"\n[3/6] Running Crawler Stage...")
        crawl_res = await run_crawl(task_id, session)
        print(f"      Websites crawled:      {crawl_res.websites_crawled}")
        print(f"      Pages crawled/stored:  {crawl_res.total_pages_stored}")
        print(f"      Failed websites:       {crawl_res.failed_websites}")

        # 5. Extraction Stage
        print(f"\n[4/6] Running Extraction Stage...")
        extraction_res = await run_extraction(task_id, session)
        print(f"      Phones extracted:      {extraction_res.phones_extracted}")
        print(f"      Emails extracted:      {extraction_res.emails_extracted}")
        print(f"      Addresses extracted:   {extraction_res.addresses_extracted}")

        # 6. Cleaning & Deduplication Stage
        print(f"\n[5/6] Running Cleaning & Deduplication...")
        cleaning_res = await run_cleaning(task_id, session)
        print(f"      Organizations merged:  {cleaning_res.organizations_merged}")

        # 7. Verification & Finalization
        print(f"\n[6/6] Running Verification & Finalization...")
        await run_verification(task_id, session)
        await run_finalize(task_id, session)

        # ── Collect Final Metrics ─────────────────────────────────────────────
        # Organizations
        stmt_orgs = (
            select(Organization)
            .join(task_organizations, task_organizations.c.organization_id == Organization.id)
            .where(task_organizations.c.task_id == task_uuid)
        )
        orgs = list((await session.execute(stmt_orgs)).scalars().all())

        # Leads
        stmt_leads = select(Lead).where(Lead.task_id == task_uuid)
        leads = list((await session.execute(stmt_leads)).scalars().all())

        # Websites
        stmt_all_sites = (
            select(Website)
            .join(Organization, Website.organization_id == Organization.id)
            .join(task_organizations, task_organizations.c.organization_id == Organization.id)
            .where(task_organizations.c.task_id == task_uuid)
        )
        all_sites = list((await session.execute(stmt_all_sites)).scalars().all())
        reachable_sites = [s for s in all_sites if s.status in ("CRAWLED", "PENDING")]
        failed_sites = [s for s in all_sites if s.status == "FAILED"]
        official_sites = [s for s in all_sites if s.is_official]

        # Contacts, phones, emails
        phones_count = extraction_res.phones_extracted
        emails_count = extraction_res.emails_extracted
        addresses_count = extraction_res.addresses_extracted

        print("\n" + "=" * 70)
        print("EXECUTION SUMMARY")
        print("=" * 70)
        print(f"Task:                    {task_id}")
        print(f"Candidates discovered:   {discovery_res.total_candidates}")
        print(f"Organizations discovered:{len(orgs)}")
        print(f"Official websites found: {len(official_sites)}")
        print(f"Reachable websites:      {len(reachable_sites)}")
        print(f"Websites crawled:        {crawl_res.websites_crawled}")
        print(f"Phones extracted:        {phones_count}")
        print(f"Emails extracted:        {emails_count}")
        print(f"Addresses extracted:     {addresses_count}")
        print(f"Leads created:           {len(leads)}")
        print(f"Duplicates removed:      {discovery_res.duplicates_removed + cleaning_res.total_duplicates_removed}")
        print(f"Failed websites:         {len(failed_sites)}")
        print("=" * 70)

        # ── Display Discovered Leads ──────────────────────────────────────────
        print("\nDISCOVERED REAL LEADS:")
        for idx, org in enumerate(orgs[:args.limit], 1):
            stmt_org_sites = select(Website).where(Website.organization_id == org.id)
            org_sites = list((await session.execute(stmt_org_sites)).scalars().all())
            official_site = next((s.url for s in org_sites if s.is_official), None)
            any_site = official_site or (org_sites[0].url if org_sites else None)

            stmt_p = select(PhoneNumber).where(PhoneNumber.organization_id == org.id)
            phones = list((await session.execute(stmt_p)).scalars().all())
            phone_val = phones[0].phone_number if phones else "—"
            wa_val = next((p.phone_number for p in phones if p.is_whatsapp), "—")

            stmt_e = select(EmailAddress).where(EmailAddress.organization_id == org.id)
            emails = list((await session.execute(stmt_e)).scalars().all())
            email_val = emails[0].email if emails else "—"

            stmt_c = select(Contact).where(Contact.organization_id == org.id)
            contacts = list((await session.execute(stmt_c)).scalars().all())
            contact_val = contacts[0].name if contacts else "—"

            stmt_sp = select(SourcePage).where(SourcePage.organization_id == org.id)
            src_pages = list((await session.execute(stmt_sp)).scalars().all())
            src_val = src_pages[0].url if src_pages else (any_site or "OpenStreetMap Nominatim")

            stmt_l = select(Lead).where(Lead.task_id == task_uuid, Lead.organization_id == org.id)
            lead_rec = (await session.execute(stmt_l)).scalar_one_or_none()
            verif_tier = lead_rec.verification_status if lead_rec else "PENDING"

            print(f"\n--- [Lead #{idx}] ---")
            print(f"Organization: {org.name}")
            print(f"Location:     {org.city or args.location}")
            print(f"Phone:        {phone_val}")
            print(f"Email:        {email_val}")
            print(f"Website:      {any_site or '—'}")
            print(f"Address:      {org.address or '—'}")
            print(f"WhatsApp:     {wa_val}")
            print(f"Contact:      {contact_val}")
            print(f"Verification: {verif_tier}")
            print(f"Source:       {src_val}")

            # Safety assertions on output
            assert ".example" not in (any_site or ""), f"Found .example domain in {any_site}"
            assert "Main Street" not in (org.address or ""), f"Found fake 'Main Street' address in {org.address}"
            assert not org.name.endswith("1") or "Ooty Restaurants" not in org.name, f"Found mock name {org.name}"


if __name__ == "__main__":
    asyncio.run(main())
