"""
tests/test_extraction.py

Comprehensive unit and integration tests for the Data Extraction Engine (Backend Step 6):
  • Phone extraction, validation, E.164 normalization, and type classification
  • WhatsApp link and text detection
  • Email extraction, de-obfuscation, and false-positive filtering
  • Physical address, city, state, and pincode extraction
  • Contact person and designation extraction
  • Social media profile extraction and platform mapping
  • JSON-LD structured data extraction
  • Provenance tracking via ExtractedField records
  • ExtractionService database persistence, task metrics, and stage transitions
  • Idempotency of re-extracting
  • CLI runner execution and output format
"""

from __future__ import annotations

import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.models.email_address import EmailAddress
from app.models.extracted_field import ExtractedField
from app.models.organization import Organization, task_organizations
from app.models.phone_number import PhoneNumber
from app.models.scraping_task import ScrapingTask
from app.models.social_link import SocialLink
from app.models.source_page import SourcePage
from app.models.user import User
from app.models.website import Website
from app.services.extraction import (
    AddressExtractor,
    ContactExtractor,
    EmailExtractor,
    PageContext,
    PageDataExtractor,
    ParsedPage,
    PhoneExtractor,
    SocialExtractor,
)
from app.services.extraction.normalizer import deobfuscate_email, normalize_phone_number
from app.services.extraction_service import ExtractionService


# ── 1. Phone & WhatsApp Extraction Tests ──────────────────────────────────────

def test_normalize_phone_number_formats() -> None:
    # Standard 10-digit Indian mobile
    disp, e164, valid = normalize_phone_number("9876543210")
    assert valid is True
    assert e164 == "+919876543210"

    # Leading zero domestic format
    disp, e164, valid = normalize_phone_number("09876543210")
    assert valid is True
    assert e164 == "+919876543210"

    # Landline with STD code (e.g. Puducherry 0413)
    disp, e164, valid = normalize_phone_number("0413-2655123")
    assert valid is True
    assert "+914132655123" in e164 or "+91" in e164

    # International format
    disp, e164, valid = normalize_phone_number("+1 (555) 234-5678", default_region="US")
    assert valid is True
    assert e164 == "+15552345678"


def test_phone_extractor_tel_and_whatsapp_links() -> None:
    html = """
    <html>
        <body>
            <p>Admissions Office: <a href="tel:+919876543210">+91 98765 43210</a></p>
            <p>Main Desk: <span>0413-2655123</span></p>
            <p><a href="https://wa.me/919944556677">Chat on WhatsApp</a></p>
            <a href="tel:08028450001">Call Reception</a>
        </body>
    </html>
    """
    ctx = PageContext(
        task_id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        source_page_id=uuid.uuid4(),
        source_url="https://school.example/contact",
        page_type="CONTACT",
    )
    parsed = ParsedPage(html, base_url=ctx.source_url)
    items = PhoneExtractor.extract(parsed, ctx)

    norm_nums = {item.normalized_value for item in items}
    assert "+919876543210" in norm_nums
    assert "+919944556677" in norm_nums

    # Check WhatsApp metadata
    wa_item = next(it for it in items if it.normalized_value == "+919944556677")
    assert wa_item.metadata["is_whatsapp"] is True
    assert wa_item.metadata["phone_type"] == "WHATSAPP"

    # Check Admissions metadata
    adm_item = next(it for it in items if it.normalized_value == "+919876543210")
    assert adm_item.metadata["phone_type"] == "ADMISSIONS"


# ── 2. Email Extraction & De-obfuscation Tests ────────────────────────────────

def test_deobfuscate_email() -> None:
    assert deobfuscate_email("info [at] school [dot] com") == "info@school.com"
    assert deobfuscate_email("contact(at)example.edu.in") == "contact@example.edu.in"
    assert deobfuscate_email("principal [AT] college [DOT] org") == "principal@college.org"
    assert deobfuscate_email("hello@school.org.") == "hello@school.org"


def test_email_extractor_and_false_positive_filtering() -> None:
    html = """
    <html>
        <body>
            <a href="mailto:admissions@school.edu">Admissions Enquiry</a>
            <p>General queries: info [at] school.edu</p>
            <p>False positive images: icon@2x.png, logo@3x.jpg, styles@v2.css</p>
            <p>Placeholder: test@example.com, fake@domain.com</p>
            <p>Principal Desk: principal@school.edu</p>
        </body>
    </html>
    """
    ctx = PageContext(
        task_id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        source_page_id=uuid.uuid4(),
        source_url="https://school.example/contact",
        page_type="CONTACT",
    )
    parsed = ParsedPage(html, base_url=ctx.source_url)
    items = EmailExtractor.extract(parsed, ctx)

    emails = {it.normalized_value: it for it in items}

    assert "admissions@school.edu" in emails
    assert "info@school.edu" in emails
    assert "principal@school.edu" in emails

    # False positives must be excluded
    assert "icon@2x.png" not in emails
    assert "styles@v2.css" not in emails
    assert "test@example.com" not in emails
    assert "fake@domain.com" not in emails

    # Check classification
    assert emails["admissions@school.edu"].metadata["email_type"] == "ADMISSIONS"
    assert emails["principal@school.edu"].metadata["email_type"] == "MANAGEMENT"
    assert emails["info@school.edu"].metadata["email_type"] == "GENERAL"


# ── 3. Address & Pincode Extraction Tests ─────────────────────────────────────

def test_address_extractor_tags_and_pincode() -> None:
    html = """
    <html>
        <body>
            <address>
                No. 14, Kamaraj Salai, Near New Bus Stand,
                Puducherry - 605001, Tamil Nadu
            </address>
            <div class="footer-address">
                Branch: Whitefield Main Road, Bengaluru, Karnataka 560066
            </div>
        </body>
    </html>
    """
    ctx = PageContext(
        task_id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        source_page_id=uuid.uuid4(),
        source_url="https://school.example/contact",
        page_type="CONTACT",
    )
    parsed = ParsedPage(html, base_url=ctx.source_url)
    items = AddressExtractor.extract(parsed, ctx)

    assert len(items) >= 1
    addr_item = items[0]
    assert "605001" in addr_item.normalized_value
    assert addr_item.metadata["pincode"] == "605001"
    assert addr_item.metadata["state"] in ("Puducherry", "Tamil Nadu")


# ── 4. Contact Person Extraction Tests ────────────────────────────────────────

def test_contact_extractor_staff_and_designations() -> None:
    html = """
    <html>
        <body>
            <div class="leadership-section">
                <h2>Our Leadership</h2>
                <div class="staff-card">
                    <h3 class="name">Dr. Ananya Sharma</h3>
                    <p class="role">Principal & Director</p>
                </div>
                <div class="staff-card">
                    <h3 class="name">Rajesh Narang</h3>
                    <p class="role">Admissions Coordinator</p>
                </div>
            </div>
            <p>Principal: Ramesh Kumar</p>
        </body>
    </html>
    """
    ctx = PageContext(
        task_id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        source_page_id=uuid.uuid4(),
        source_url="https://school.example/about",
        page_type="ABOUT",
    )
    parsed = ParsedPage(html, base_url=ctx.source_url)
    items = ContactExtractor.extract(parsed, ctx)

    names = {it.metadata["name"]: it.metadata["designation"] for it in items}
    assert any("Ananya Sharma" in n for n in names)
    assert any("Rajesh Narang" in n for n in names)
    assert any("Ramesh Kumar" in n for n in names)


# ── 5. Social Link Extraction Tests ───────────────────────────────────────────

def test_social_extractor_filtering_and_platforms() -> None:
    html = """
    <html>
        <footer>
            <a href="https://www.facebook.com/StPaulsSchoolOfficial">Facebook</a>
            <a href="https://instagram.com/stpauls_academy/">Instagram</a>
            <a href="https://linkedin.com/school/st-pauls-school/">LinkedIn</a>
            <a href="https://youtube.com/@StPaulsChannel">YouTube</a>
            <a href="https://twitter.com/stpauls_edu">Twitter</a>
            <a href="https://www.facebook.com/sharer/sharer.php?u=school">Share Button</a>
            <a href="https://youtube.com/">Generic YouTube</a>
        </footer>
    </html>
    """
    ctx = PageContext(
        task_id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        source_page_id=uuid.uuid4(),
        source_url="https://school.example",
    )
    parsed = ParsedPage(html, base_url=ctx.source_url)
    items = SocialExtractor.extract(parsed, ctx)

    platforms = {it.metadata["platform"]: it.normalized_value for it in items}
    assert "FACEBOOK" in platforms
    assert "INSTAGRAM" in platforms
    assert "LINKEDIN" in platforms
    assert "YOUTUBE" in platforms
    assert "TWITTER" in platforms

    # Exclude share button
    urls = [it.normalized_value for it in items]
    assert not any("sharer.php" in u for u in urls)


# ── 6. JSON-LD Structured Data Extraction Tests ───────────────────────────────

def test_json_ld_structured_data_extraction() -> None:
    html = """
    <html>
        <head>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "EducationalOrganization",
                "name": "St. Paul International School",
                "telephone": "+91-98765-43210",
                "email": "contact@stpaul.edu",
                "address": {
                    "@type": "PostalAddress",
                    "streetAddress": "100 MG Road",
                    "addressLocality": "Puducherry",
                    "postalCode": "605001"
                }
            }
            </script>
        </head>
        <body><h1>Welcome</h1></body>
    </html>
    """
    ctx = PageContext(
        task_id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        source_page_id=uuid.uuid4(),
        source_url="https://stpaul.edu",
        page_type="HOME",
    )
    extractor = PageDataExtractor()
    res = extractor.extract(html=html, context=ctx)

    fields = {item.field_name: item for item in res.items}
    assert "ORGANIZATION_NAME" in fields
    assert fields["ORGANIZATION_NAME"].normalized_value == "St. Paul International School"

    phones = [it for it in res.items if it.field_name == "PHONE"]
    assert len(phones) >= 1
    assert phones[0].normalized_value == "+919876543210"

    emails = [it for it in res.items if it.field_name == "EMAIL"]
    assert len(emails) >= 1
    assert emails[0].normalized_value == "contact@stpaul.edu"

    addresses = [it for it in res.items if it.field_name == "ADDRESS"]
    assert len(addresses) >= 1
    assert addresses[0].metadata["pincode"] == "605001"


# ── 7. ExtractionService Integration & DB Persistence Tests ───────────────────

@pytest.mark.asyncio
async def test_extraction_service_database_workflow(db_session: AsyncSession) -> None:
    # 1. Setup User & Task
    user = User(name="Extract User", email="extract@example.com", password_hash="hash", role="USER")
    db_session.add(user)
    await db_session.flush()

    task = ScrapingTask(
        task_id="TASK-000601",
        user_id=user.id,
        location="Puducherry",
        keyword="Schools",
        status="RUNNING",
        current_stage="EXTRACTING",
        progress=50,
    )
    db_session.add(task)
    await db_session.flush()

    # 2. Setup Organization & Website
    org = Organization(name="St. Jude Academy", city="Puducherry")
    db_session.add(org)
    await db_session.flush()

    await db_session.execute(task_organizations.insert().values(task_id=task.id, organization_id=org.id))

    web = Website(
        organization_id=org.id,
        url="https://stjude.example",
        normalized_url="https://stjude.example",
        domain="stjude.example",
        status="CRAWLED",
    )
    db_session.add(web)
    await db_session.flush()

    # 3. Setup SourcePages
    sp_contact = SourcePage(
        organization_id=org.id,
        website_id=web.id,
        task_id=task.id,
        url="https://stjude.example/contact",
        normalized_url="https://stjude.example/contact",
        page_title="Contact St. Jude Academy",
        page_type="CONTACT",
        http_status=200,
    )
    db_session.add(sp_contact)
    await db_session.commit()

    # Provide mock HTML content
    contact_html = """
    <html>
        <head><title>Contact St. Jude Academy</title></head>
        <body>
            <h1>Contact Us</h1>
            <p>Admissions Helpline: <a href="tel:+919876543210">+91 98765 43210</a></p>
            <p>Office Email: <a href="mailto:info@stjude.example">info@stjude.example</a></p>
            <p>Admissions Email: <a href="mailto:admissions@stjude.example">admissions@stjude.example</a></p>
            <address>42 Sea Face Road, Puducherry - 605001</address>
            <div class="staff-card">
                <p>Sister Mary</p>
                <p>Principal</p>
            </div>
            <footer>
                <a href="https://facebook.com/stjudeofficial">Facebook</a>
                <a href="https://wa.me/919876543210">WhatsApp</a>
            </footer>
        </body>
    </html>
    """

    html_cache = {
        "https://stjude.example/contact": contact_html,
    }

    service = ExtractionService(session=db_session)
    summary = await service.extract_for_task(task.task_id, html_cache=html_cache)

    # Verify Summary Output
    assert summary.task_id == task.task_id
    assert summary.pages_processed == 1
    assert summary.phones_extracted >= 1
    assert summary.emails_extracted >= 2
    assert summary.addresses_extracted >= 1
    assert summary.contacts_extracted >= 1
    assert summary.social_links_extracted >= 1
    assert summary.next_stage == "CLEANING"

    # Verify DB Task State
    refreshed_task = await db_session.get(ScrapingTask, task.id)
    assert refreshed_task.current_stage == "CLEANING"
    assert refreshed_task.progress == 70
    assert refreshed_task.phones_found >= 1
    assert refreshed_task.emails_found >= 2

    # Verify PhoneNumbers in DB
    stmt_p = select(PhoneNumber).where(PhoneNumber.organization_id == org.id)
    res_p = (await db_session.execute(stmt_p)).scalars().all()
    assert len(res_p) >= 1
    assert any(p.normalized_phone == "+919876543210" for p in res_p)

    # Verify EmailAddresses in DB
    stmt_e = select(EmailAddress).where(EmailAddress.organization_id == org.id)
    res_e = (await db_session.execute(stmt_e)).scalars().all()
    assert len(res_e) >= 2
    email_texts = {e.normalized_email for e in res_e}
    assert "info@stjude.example" in email_texts
    assert "admissions@stjude.example" in email_texts

    # Verify Contacts in DB
    stmt_c = select(Contact).where(Contact.organization_id == org.id)
    res_c = (await db_session.execute(stmt_c)).scalars().all()
    assert len(res_c) >= 1
    assert any("Sister Mary" in c.name for c in res_c)

    # Verify SocialLinks in DB
    stmt_s = select(SocialLink).where(SocialLink.organization_id == org.id)
    res_s = (await db_session.execute(stmt_s)).scalars().all()
    assert len(res_s) >= 1
    assert any(s.platform == "FACEBOOK" for s in res_s)

    # Verify ExtractedFields Provenance records
    stmt_ef = select(ExtractedField).where(ExtractedField.organization_id == org.id)
    res_ef = (await db_session.execute(stmt_ef)).scalars().all()
    assert len(res_ef) >= 5

    field_names = {ef.field_name for ef in res_ef}
    assert "PHONE" in field_names
    assert "EMAIL" in field_names
    assert "ADDRESS" in field_names
    assert "CONTACT_PERSON" in field_names
    assert "SOCIAL_LINK" in field_names

    # Verify Organization address updated
    refreshed_org = await db_session.get(Organization, org.id)
    assert refreshed_org.pincode == "605001"


# ── 8. Idempotency Test ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_extraction_service_idempotency(db_session: AsyncSession) -> None:
    """Repeated extraction does not duplicate phone numbers, emails, or social links."""
    user = User(name="Idemp User", email="idemp@example.com", password_hash="hash", role="USER")
    db_session.add(user)
    await db_session.flush()

    task = ScrapingTask(
        task_id="TASK-000602",
        user_id=user.id,
        location="Puducherry",
        keyword="Schools",
    )
    db_session.add(task)
    await db_session.flush()

    org = Organization(name="Idempotent Academy", city="Puducherry")
    db_session.add(org)
    await db_session.flush()

    web = Website(
        organization_id=org.id,
        url="https://idemp.example",
        normalized_url="https://idemp.example",
        domain="idemp.example",
        status="CRAWLED",
    )
    db_session.add(web)
    await db_session.flush()

    sp = SourcePage(
        organization_id=org.id,
        website_id=web.id,
        task_id=task.id,
        url="https://idemp.example/contact",
        normalized_url="https://idemp.example/contact",
        page_type="CONTACT",
    )
    db_session.add(sp)
    await db_session.commit()

    html = """
    <html>
        <body>
            <a href="tel:+919876543210">+91 98765 43210</a>
            <a href="mailto:info@idemp.example">info@idemp.example</a>
        </body>
    </html>
    """
    cache = {"https://idemp.example/contact": html}

    service = ExtractionService(session=db_session)

    # First run
    await service.extract_for_task(task.task_id, html_cache=cache)

    # Second run
    await service.extract_for_task(task.task_id, html_cache=cache)

    # Verify no duplicates
    phones = (await db_session.execute(select(PhoneNumber).where(PhoneNumber.organization_id == org.id))).scalars().all()
    emails = (await db_session.execute(select(EmailAddress).where(EmailAddress.organization_id == org.id))).scalars().all()

    assert len(phones) == 1
    assert len(emails) == 1


# ── 9. CLI Runner Output Format Test ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_extraction_cli_runner(db_session: AsyncSession, monkeypatch, capsys) -> None:
    from app.jobs.run_extraction import main as run_extraction_main
    from app.schemas.extraction import TaskExtractionSummary

    async def mock_run_extraction(task_id: str, session=None) -> TaskExtractionSummary:
        return TaskExtractionSummary(
            task_id=task_id,
            pages_processed=5,
            phones_extracted=3,
            emails_extracted=2,
            addresses_extracted=1,
            contacts_extracted=2,
            social_links_extracted=3,
            provenance_records_created=11,
            duration_seconds=1.2,
            status="Extraction completed",
            next_stage="CLEANING",
        )

    monkeypatch.setattr("app.jobs.run_extraction.run_extraction", mock_run_extraction)
    monkeypatch.setattr("app.jobs.run_extraction.create_engine_and_factory", lambda: None)

    async def dummy_dispose():
        pass

    monkeypatch.setattr("app.jobs.run_extraction.dispose_engine", dummy_dispose)

    class MockContext:
        async def __aenter__(self):
            return db_session

        async def __aexit__(self, *args):
            pass

    monkeypatch.setattr("app.jobs.run_extraction.get_session_factory", lambda: lambda: MockContext())

    user = User(name="CLI User 2", email="cli2@example.com", password_hash="hash", role="USER")
    db_session.add(user)
    await db_session.flush()

    task = ScrapingTask(
        task_id="TASK-000603",
        user_id=user.id,
        location="Puducherry",
        keyword="Schools",
    )
    db_session.add(task)
    await db_session.commit()

    await run_extraction_main(task.task_id)

    captured = capsys.readouterr().out
    assert "Task: TASK-000603" in captured
    assert "Pages Processed: 5" in captured
    assert "Phones Extracted: 3" in captured
    assert "Emails Extracted: 2" in captured
    assert "Addresses Extracted: 1" in captured
    assert "Contacts Extracted: 2" in captured
    assert "Social Links Extracted: 3" in captured
    assert "Status: Extraction completed" in captured
    assert "Next Stage: CLEANING" in captured
