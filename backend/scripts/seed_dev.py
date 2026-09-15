"""
scripts/seed_dev.py

Development database seeder for LeadScout.

Seeds a realistic fictional dataset:
- 1 demo user
- 2 scraping tasks
- 5 organizations
- Websites
- Contacts
- Phone numbers
- Email addresses
- Social links
- Source pages
- Extracted field provenance records
- Lead verifications
- Scraping logs

Usage:
    # Run against configured database:
    python scripts/seed_dev.py

    # Or specify custom DB URL:
    python scripts/seed_dev.py --db-url "sqlite+aiosqlite:///dev.db"
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Ensure backend root is on sys.path
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.db.base import Base
from app.models import (
    Contact,
    EmailAddress,
    ExtractedField,
    Lead,
    LeadVerification,
    Organization,
    PhoneNumber,
    ScrapingLog,
    ScrapingTask,
    SocialLink,
    SourcePage,
    User,
    Website,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def seed(database_url: str | None = None) -> None:
    url = database_url or settings.DATABASE_URL
    print(f"Connecting to: {url.split('://')[0]}://...")

    engine = create_async_engine(url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    # For SQLite dev testing, create tables if not present
    if "sqlite" in url:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        print("Seeding demo data...")

        # ── 1. Demo User ──────────────────────────────────────────────────────
        user = User(
            id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            name="Demo Scout",
            email="demo@leadscout.app",
            email_normalized="demo@leadscout.app",
            password_hash="$2b$12$e8Y2gqg92iV2EaHhZq9vIOG5w38iM5d5g1h6k4m2n3p4q5r6s7t8u",  # bcrypt mock
            company="LeadScout Technologies",
            role="USER",
            is_active=True,
        )
        session.add(user)

        # ── 2. Scraping Tasks ─────────────────────────────────────────────────
        task1 = ScrapingTask(
            id=uuid.UUID("22222222-2222-2222-2222-222222222221"),
            task_id="TASK-000101",
            user_id=user.id,
            location="Bengaluru, Karnataka",
            keyword="International Schools",
            search_radius=25,
            max_results=50,
            max_pages_per_site=5,
            crawl_depth=2,
            follow_internal_links=True,
            prioritize_contact=True,
            prioritize_about=True,
            status="COMPLETED",
            current_stage="COMPLETED",
            progress=100,
            results_discovered=3,
            websites_found=3,
            websites_crawled=3,
            phones_found=6,
            emails_found=4,
            addresses_found=3,
            duplicates_removed=1,
            failed_websites=0,
            started_at=utc_now(),
            completed_at=utc_now(),
        )

        task2 = ScrapingTask(
            id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
            task_id="TASK-000102",
            user_id=user.id,
            location="Mumbai, Maharashtra",
            keyword="Tech Academies & Colleges",
            search_radius=30,
            max_results=100,
            max_pages_per_site=8,
            crawl_depth=3,
            follow_internal_links=True,
            prioritize_contact=True,
            prioritize_about=True,
            prioritize_admissions=True,
            status="RUNNING",
            current_stage="CRAWLING",
            progress=45,
            results_discovered=2,
            websites_found=2,
            websites_crawled=1,
            phones_found=3,
            emails_found=2,
            addresses_found=2,
            duplicates_removed=0,
            failed_websites=0,
            started_at=utc_now(),
        )
        session.add_all([task1, task2])

        # ── 3. Organizations & Associated Entities ────────────────────────────
        org_data = [
            {
                "name": "Oakridge International Academy",
                "category": "Education",
                "address": "Sy No 8/2, Varthur Road, Whitefield",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pincode": "560066",
                "website": "https://www.oakridge-mock.edu",
                "domain": "oakridge-mock.edu",
                "contact": ("Dr. Ananya Sharma", "Principal & Director"),
                "phone": ("+91 80 2845 0001", "+918028450001", "MAIN", False),
                "email": ("admissions@oakridge-mock.edu", "ADMISSIONS"),
                "social": ("FACEBOOK", "https://facebook.com/oakridgemock"),
                "tasks": [task1],
                "verif": ("HIGH", 8, 8),
            },
            {
                "name": "Greenwood Valley High",
                "category": "Education",
                "address": "45 Sarjapur Main Road",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pincode": "560035",
                "website": "https://www.greenwoodvalley-mock.edu",
                "domain": "greenwoodvalley-mock.edu",
                "contact": ("Rajesh Narang", "Admissions Officer"),
                "phone": ("+91 98450 12345", "+919845012345", "ADMISSIONS", True),
                "email": ("contact@greenwoodvalley-mock.edu", "GENERAL"),
                "social": ("LINKEDIN", "https://linkedin.com/school/greenwoodvalleymock"),
                "tasks": [task1],
                "verif": ("MEDIUM", 6, 8),
            },
            {
                "name": "Silver Oaks Global School",
                "category": "Education",
                "address": "Sector 3, HSR Layout",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pincode": "560102",
                "website": "https://www.silveroaks-mock.edu",
                "domain": "silveroaks-mock.edu",
                "contact": ("Sumanth Rao", "Head of Administration"),
                "phone": ("+91 80 4123 9876", "+918041239876", "OFFICE", False),
                "email": ("info@silveroaks-mock.edu", "GENERAL"),
                "social": ("INSTAGRAM", "https://instagram.com/silveroaksmock"),
                "tasks": [task1, task2],  # Appears in both tasks
                "verif": ("HIGH", 7, 8),
            },
            {
                "name": "Bombay Institute of Technology",
                "category": "Higher Education",
                "address": "Powai Campus, Technology Street",
                "city": "Mumbai",
                "state": "Maharashtra",
                "pincode": "400076",
                "website": "https://www.bit-mumbai-mock.ac.in",
                "domain": "bit-mumbai-mock.ac.in",
                "contact": ("Prof. Vikram Mehra", "Dean of Academic Affairs"),
                "phone": ("+91 22 2576 0000", "+912225760000", "MAIN", False),
                "email": ("dean.academic@bit-mumbai-mock.ac.in", "MANAGEMENT"),
                "social": ("TWITTER", "https://twitter.com/bitmumbaimock"),
                "tasks": [task2],
                "verif": ("HIGH", 8, 8),
            },
            {
                "name": "Metro Apex Engineering College",
                "category": "Higher Education",
                "address": "Andheri Kurla Road",
                "city": "Mumbai",
                "state": "Maharashtra",
                "pincode": "400059",
                "website": "https://www.metroapex-mock.edu.in",
                "domain": "metroapex-mock.edu.in",
                "contact": ("Kavita Deshmukh", "Registrar"),
                "phone": ("+91 99201 55667", "+919920155667", "MAIN", True),
                "email": ("registrar@metroapex-mock.edu.in", "CONTACT"),
                "social": ("LINKEDIN", "https://linkedin.com/school/metroapexmock"),
                "tasks": [task2],
                "verif": ("MEDIUM", 5, 8),
            },
        ]

        for item in org_data:
            org = Organization(
                name=item["name"],
                category=item["category"],
                address=item["address"],
                city=item["city"],
                state=item["state"],
                pincode=item["pincode"],
                tasks=item["tasks"],
            )
            session.add(org)
            await session.flush()  # assign org.id

            # Lead records
            for t in item["tasks"]:
                lead = Lead(
                    task_id=t.id,
                    organization_id=org.id,
                    status="ACTIVE",
                    verification_status=item["verif"][0],
                )
                session.add(lead)

            # Website
            website = Website(
                organization_id=org.id,
                url=item["website"],
                normalized_url=item["website"].rstrip("/"),
                domain=item["domain"],
                is_official=True,
                status="CRAWLED",
                last_crawled_at=utc_now(),
            )
            session.add(website)
            await session.flush()

            # Source Page
            sp = SourcePage(
                organization_id=org.id,
                website_id=website.id,
                task_id=item["tasks"][0].id,
                url=f"{item['website']}/contact",
                normalized_url=f"{item['website'].rstrip('/')}/contact",
                page_title=f"Contact Us — {item['name']}",
                page_type="CONTACT",
                http_status=200,
                discovered_at=utc_now(),
                crawled_at=utc_now(),
            )
            session.add(sp)
            await session.flush()

            # Contact
            contact = Contact(
                organization_id=org.id,
                name=item["contact"][0],
                designation=item["contact"][1],
            )
            session.add(contact)
            await session.flush()

            # Phone Number
            phone = PhoneNumber(
                organization_id=org.id,
                contact_id=contact.id,
                phone_number=item["phone"][0],
                normalized_phone=item["phone"][1],
                phone_type=item["phone"][2],
                is_whatsapp=item["phone"][3],
                is_primary=True,
            )
            session.add(phone)

            # Email Address
            email = EmailAddress(
                organization_id=org.id,
                contact_id=contact.id,
                email=item["email"][0],
                normalized_email=item["email"][0].lower(),
                email_type=item["email"][1],
                is_primary=True,
            )
            session.add(email)

            # Social Link
            social = SocialLink(
                organization_id=org.id,
                platform=item["social"][0],
                url=item["social"][1],
                normalized_url=item["social"][1].rstrip("/"),
                is_official=True,
            )
            session.add(social)

            # Extracted Field Provenance
            extracted_phone = ExtractedField(
                organization_id=org.id,
                source_page_id=sp.id,
                field_name="PHONE",
                field_value=item["phone"][0],
                normalized_value=item["phone"][1],
            )
            extracted_email = ExtractedField(
                organization_id=org.id,
                source_page_id=sp.id,
                field_name="EMAIL",
                field_value=item["email"][0],
                normalized_value=item["email"][0].lower(),
            )
            session.add_all([extracted_phone, extracted_email])

            # Lead Verification
            verif = LeadVerification(
                organization_id=org.id,
                status=item["verif"][0],
                fields_found=item["verif"][1],
                total_fields=item["verif"][2],
                verified_at=utc_now(),
            )
            session.add(verif)

        # ── 4. Scraping Logs ──────────────────────────────────────────────────
        logs = [
            ScrapingLog(
                task_id=task1.id,
                level="INFO",
                event_type="TASK_CREATED",
                message="Task TASK-000101 initialized by user Demo Scout.",
            ),
            ScrapingLog(
                task_id=task1.id,
                level="INFO",
                event_type="DISCOVERY_STARTED",
                message="Querying location 'Bengaluru, Karnataka' for keyword 'International Schools'.",
            ),
            ScrapingLog(
                task_id=task1.id,
                level="INFO",
                event_type="CRAWL_STARTED",
                message="Crawling 3 discovered websites up to depth 2.",
            ),
            ScrapingLog(
                task_id=task1.id,
                level="INFO",
                event_type="TASK_COMPLETED",
                message="Task completed: 3 organizations discovered, 6 phones extracted, 4 emails verified.",
            ),
            ScrapingLog(
                task_id=task2.id,
                level="INFO",
                event_type="TASK_CREATED",
                message="Task TASK-000102 initialized by user Demo Scout.",
            ),
            ScrapingLog(
                task_id=task2.id,
                level="INFO",
                event_type="CRAWL_STARTED",
                message="Active crawl running on Mumbai educational institutions.",
            ),
        ]
        session.add_all(logs)

        await session.commit()
        print("[SUCCESS] Development seed data successfully written!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed LeadScout development database.")
    parser.add_argument("--db-url", help="Database URL override")
    args = parser.parse_args()

    asyncio.run(seed(args.db_url))
