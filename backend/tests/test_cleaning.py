"""
tests/test_cleaning.py

Comprehensive test suite for Backend Step 7:
Data Cleaning, Normalization & Organization Deduplication Pipeline.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.models.email_address import EmailAddress
from app.models.extracted_field import ExtractedField
from app.models.lead import Lead
from app.models.organization import Organization, task_organizations
from app.models.organization_merge_event import OrganizationMergeEvent
from app.models.phone_number import PhoneNumber
from app.models.scraping_log import ScrapingLog
from app.models.scraping_task import ScrapingTask
from app.models.social_link import SocialLink
from app.models.source_page import SourcePage
from app.models.user import User
from app.models.website import Website
from app.services.cleaning.address_cleaner import clean_address, clean_pincode
from app.services.cleaning.cleaning_service import CleaningService
from app.services.cleaning.deduplication_service import DeduplicationService
from app.services.cleaning.email_cleaner import clean_email
from app.services.cleaning.merge_service import MergeService
from app.services.cleaning.organization_cleaner import (
    clean_organization_name,
    normalize_organization_name_for_match,
)
from app.services.cleaning.organization_matcher import OrganizationMatcher
from app.services.cleaning.phone_cleaner import clean_phone_number
from app.services.cleaning.text_cleaner import clean_text, is_placeholder
from app.services.cleaning.url_cleaner import clean_social_url, clean_url


# ── 1. Text & Placeholder Cleaner Tests ─────────────────────────────────────────


def test_clean_text_and_html_unescape():
    raw = "  ABC &amp; Sons&#39;   High\tSchool \n\n  "
    cleaned = clean_text(raw)
    assert cleaned == "ABC & Sons' High School"


def test_is_placeholder_detection():
    assert is_placeholder("N/A") is True
    assert is_placeholder("n/a") is True
    assert is_placeholder("null") is True
    assert is_placeholder("None") is True
    assert is_placeholder("undefined") is True
    assert is_placeholder("Not Available") is True
    assert is_placeholder("dummy") is True
    assert is_placeholder("  --  ") is True
    assert is_placeholder("St. Joseph High School") is False


# ── 2. Phone Cleaner Tests ─────────────────────────────────────────────────────


def test_clean_phone_number_indian_mobile():
    res = clean_phone_number("9876543210")
    assert res is not None
    assert res.e164 == "+919876543210"
    assert "98765" in res.display


def test_clean_phone_number_with_std_and_dashes():
    res = clean_phone_number("+91 (0413) 2233445")
    assert res is not None
    assert res.e164 == "+914132233445"


def test_clean_phone_number_garbage_rejection():
    assert clean_phone_number("123") is None
    assert clean_phone_number("0000000000") is None
    assert clean_phone_number("1111111111") is None
    assert clean_phone_number("abcdef") is None
    assert clean_phone_number("") is None


# ── 3. Email Cleaner Tests ─────────────────────────────────────────────────────


def test_clean_email_valid_and_normalization():
    res = clean_email("  Contact@LeadScout.App  ")
    assert res is not None
    assert res.normalized == "contact@leadscout.app"
    assert res.domain == "leadscout.app"


def test_clean_email_deobfuscation():
    res = clean_email("principal [at] abcacademy [dot] in")
    assert res is not None
    assert res.normalized == "principal@abcacademy.in"


def test_clean_email_asset_and_dummy_rejection():
    assert clean_email("logo.png@website.com") is None
    assert clean_email("banner.jpg") is None
    assert clean_email("style.css") is None
    assert clean_email("info@example.com") is None
    assert clean_email("alert@sentry.io") is None
    assert clean_email("not-an-email") is None


# ── 4. URL & Social Cleaner Tests ──────────────────────────────────────────────


def test_clean_url_strips_tracking_params():
    url = "https://www.myschool.edu/home?utm_source=facebook&utm_medium=cpc&gclid=12345#contact"
    cleaned = clean_url(url)
    assert cleaned == "https://myschool.edu/home"


def test_clean_social_url():
    fb = "https://www.facebook.com/MySchoolPage/?ref=bookmarks&fbclid=abcdef"
    cleaned = clean_social_url(fb)
    assert "fbclid" not in cleaned
    assert "ref" not in cleaned
    assert "facebook.com/MySchoolPage" in cleaned


# ── 5. Address & Pincode Cleaner Tests ─────────────────────────────────────────


def test_clean_address():
    raw = "No. 12, Mission St.,,\n  Near Beach Road,   Puducherry - 605001"
    cleaned = clean_address(raw)
    assert ",," not in cleaned
    assert "\n" not in cleaned
    assert "No. 12, Mission St., Near Beach Road, Puducherry - 605001" in cleaned


def test_clean_pincode():
    assert clean_pincode("605001") == "605001"
    assert clean_pincode("Pincode: 605001.") == "605001"
    assert clean_pincode("12345") is None  # only 5 digits
    assert clean_pincode("012345") is None  # leading 0
    assert clean_pincode("abcdef") is None


# ── 6. Organization Cleaner Tests ──────────────────────────────────────────────


def test_clean_organization_name():
    raw = "  - ABC International School -  "
    assert clean_organization_name(raw) == "ABC International School"


def test_normalize_organization_name_for_match():
    name1 = "ABC International School Pvt. Ltd."
    name2 = "ABC International School"
    norm1 = normalize_organization_name_for_match(name1)
    norm2 = normalize_organization_name_for_match(name2)
    assert norm1 == norm2
    assert norm1 == "abc international school"

    # Preserves differentiators
    norm3 = normalize_organization_name_for_match("ABC Academy")
    assert norm3 != norm1


# ── 7. Organization Matcher & Branch Safety Tests ──────────────────────────────


def test_organization_matcher_scoring():
    org1 = Organization(name="St. Patrick School", city="Puducherry", pincode="605001")
    org1.websites = [Website(url="https://stpatrickschool.edu", normalized_url="https://stpatrickschool.edu", is_official=True)]
    org1.phone_numbers = [PhoneNumber(phone_number="+91 413 2223344", normalized_phone="+914132223344")]
    org1.email_addresses = [EmailAddress(email="office@stpatrickschool.edu", normalized_email="office@stpatrickschool.edu")]

    org2 = Organization(name="St Patrick School Pvt Ltd", city="Puducherry", pincode="605001")
    org2.websites = [Website(url="https://www.stpatrickschool.edu/contact", normalized_url="https://stpatrickschool.edu/contact", is_official=False)]
    org2.phone_numbers = [PhoneNumber(phone_number="0413-2223344", normalized_phone="+914132223344")]
    org2.email_addresses = [EmailAddress(email="info@stpatrickschool.edu", normalized_email="info@stpatrickschool.edu")]

    res = OrganizationMatcher.match(org1, org2)
    assert res.score == 100
    assert res.is_duplicate is True
    assert res.is_branch_conflict is False
    assert any("domain" in r for r in res.reasons)
    assert any("phone" in r for r in res.reasons)


def test_organization_matcher_branch_safety():
    """Identical school names in different cities without shared domain or phone must NOT merge."""
    org_chennai = Organization(name="Don Bosco Matriculation School", city="Chennai")
    org_chennai.websites = [Website(url="https://donboscochennai.edu", normalized_url="https://donboscochennai.edu")]
    org_chennai.phone_numbers = [PhoneNumber(phone_number="+91 44 11223344", normalized_phone="+914411223344")]

    org_pondy = Organization(name="Don Bosco Matriculation School", city="Puducherry")
    org_pondy.websites = [Website(url="https://donboscopondy.edu", normalized_url="https://donboscopondy.edu")]
    org_pondy.phone_numbers = [PhoneNumber(phone_number="+91 413 5566778", normalized_phone="+914135566778")]

    res = OrganizationMatcher.match(org_chennai, org_pondy)
    assert res.is_branch_conflict is True
    assert res.is_duplicate is False
    assert res.is_potential is False
    assert res.score <= 40
    assert any("Branch safety" in r for r in res.reasons)


# ── 8. Child Entity Exact Deduplication Tests ──────────────────────────────────


@pytest.mark.asyncio
async def test_deduplication_service(db_session: AsyncSession):
    org = Organization(name="Test Academy", city="Puducherry")
    db_session.add(org)
    await db_session.flush()

    # Pre-cleaning unnormalized entries that map to the same normalized key
    p1 = PhoneNumber(organization_id=org.id, phone_number="+91 98765 43210", normalized_phone="+91 98765 43210", is_primary=True)
    p2 = PhoneNumber(organization_id=org.id, phone_number="9876543210", normalized_phone="9876543210", is_primary=False)
    e1 = EmailAddress(organization_id=org.id, email="info@academy.edu", normalized_email="info@academy.edu")
    e2 = EmailAddress(organization_id=org.id, email="INFO@ACADEMY.EDU", normalized_email="INFO@ACADEMY.EDU")
    w = Website(organization_id=org.id, url="https://academy.edu", normalized_url="https://academy.edu")
    db_session.add_all([p1, p2, e1, e2, w])
    await db_session.flush()

    sp1 = SourcePage(organization_id=org.id, website_id=w.id, url="https://academy.edu/about", normalized_url="https://academy.edu/about")
    sp2 = SourcePage(organization_id=org.id, website_id=w.id, url="https://academy.edu/about/", normalized_url="https://academy.edu/about/")
    db_session.add_all([sp1, sp2])
    await db_session.flush()

    # ExtractedField pointing to sp2
    ef = ExtractedField(organization_id=org.id, source_page_id=sp2.id, field_name="phone", field_value="9876543210")
    db_session.add(ef)
    await db_session.flush()
    ef_id = ef.id

    counts = await DeduplicationService.deduplicate_organization(db_session, org.id)
    assert counts["emails"] == 1
    assert counts["source_pages"] == 1

    # Verify provenance preserved: ef source_page_id is now sp1.id
    ef_saved = await db_session.get(ExtractedField, ef_id)
    assert ef_saved is not None
    assert ef_saved.source_page_id == sp1.id


# ── 9. Safe Organization Merge Tests ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_safe_organization_merge(db_session: AsyncSession):
    # Setup User & Task
    user = User(
        id=uuid.uuid4(),
        name="Scout Admin",
        email=f"admin_{uuid.uuid4().hex[:6]}@leadscout.app",
        password_hash="hash",
    )
    db_session.add(user)
    await db_session.flush()

    task = ScrapingTask(
        task_id="TASK-CLEAN-001",
        user_id=user.id,
        keyword="Schools",
        location="Puducherry",
        status="RUNNING",
    )
    db_session.add(task)
    await db_session.flush()

    # Org A: Has official website, phone 1
    org_a = Organization(name="Modern Academy", city="Puducherry")
    db_session.add(org_a)
    await db_session.flush()
    web_a = Website(organization_id=org_a.id, url="https://modernacademy.edu", normalized_url="https://modernacademy.edu", is_official=True)
    phone_a = PhoneNumber(organization_id=org_a.id, phone_number="+91 413 2221111", normalized_phone="+914132221111", is_primary=True)
    db_session.add_all([web_a, phone_a])

    # Org B: Has address, pincode, contact, phone 2
    org_b = Organization(name="Modern Academy Pvt Ltd", address="10 Main Road", pincode="605001")
    db_session.add(org_b)
    await db_session.flush()
    contact_b = Contact(organization_id=org_b.id, name="Dr. Rao", designation="Principal")
    phone_b = PhoneNumber(organization_id=org_b.id, phone_number="+91 413 2229999", normalized_phone="+914132229999")
    db_session.add_all([contact_b, phone_b])
    await db_session.flush()

    # Link both orgs to task & leads
    await db_session.execute(task_organizations.insert().values([
        {"task_id": task.id, "organization_id": org_a.id},
        {"task_id": task.id, "organization_id": org_b.id},
    ]))
    lead_a = Lead(task_id=task.id, organization_id=org_a.id)
    lead_b = Lead(task_id=task.id, organization_id=org_b.id)
    db_session.add_all([lead_a, lead_b])
    await db_session.flush()

    # Execute merge
    merge_res = await MergeService.merge_organizations(
        session=db_session,
        org1=org_a,
        org2=org_b,
        match_score=95,
        match_reasons=["Matching normalized name", "Shared domain"],
    )

    canonical = merge_res["canonical_organization"]
    assert canonical.id == org_a.id
    assert canonical.address == "10 Main Road"
    assert canonical.pincode == "605001"

    # Org B deleted
    deleted_org = await db_session.get(Organization, org_b.id)
    assert deleted_org is None

    # Child records re-parented
    await db_session.refresh(contact_b)
    assert contact_b.organization_id == org_a.id
    await db_session.refresh(phone_b)
    assert phone_b.organization_id == org_a.id

    # Verify OrganizationMergeEvent was recorded
    stmt_ev = select(OrganizationMergeEvent).where(OrganizationMergeEvent.target_organization_id == org_a.id)
    ev = (await db_session.execute(stmt_ev)).scalar_one()
    assert ev.source_organization_id == org_b.id
    assert ev.match_score == 95


# ── 10. Task-Level CleaningService Integration Tests ──────────────────────────


@pytest.mark.asyncio
async def test_cleaning_service_task_workflow(db_session: AsyncSession):
    user = User(
        id=uuid.uuid4(),
        name="User Clean",
        email=f"clean_{uuid.uuid4().hex[:6]}@leadscout.app",
        password_hash="hash",
    )
    db_session.add(user)
    await db_session.flush()

    task = ScrapingTask(
        task_id="TASK-CLEAN-002",
        user_id=user.id,
        keyword="Hospitals",
        location="Puducherry",
        status="RUNNING",
        current_stage="EXTRACTING",
        progress=70,
    )
    db_session.add(task)
    await db_session.flush()

    # Org 1: Apex Hospital with garbage phone ("123") and valid phone
    org1 = Organization(name="  Apex Hospital &amp; Research  ", city="Puducherry", address="10 Beach Rd")
    db_session.add(org1)
    await db_session.flush()
    w1 = Website(organization_id=org1.id, url="https://apexhospital.example", normalized_url="https://apexhospital.example", is_official=True)
    p_invalid = PhoneNumber(organization_id=org1.id, phone_number="123", normalized_phone="123")
    p_valid = PhoneNumber(organization_id=org1.id, phone_number="9876543210", normalized_phone="+919876543210")
    db_session.add_all([w1, p_invalid, p_valid])

    # Org 2: Duplicate of Org 1 (same domain, phone & name)
    org2 = Organization(name="Apex Hospital &amp; Research Pvt Ltd", city="Puducherry", pincode="605001")
    db_session.add(org2)
    await db_session.flush()
    w2 = Website(organization_id=org2.id, url="https://www.apexhospital.example/contact", normalized_url="https://apexhospital.example/contact")
    p2 = PhoneNumber(organization_id=org2.id, phone_number="9876543210", normalized_phone="+919876543210")
    e_invalid = EmailAddress(organization_id=org2.id, email="logo.png@apexhospital.example", normalized_email="logo.png@apexhospital.example")
    e_valid = EmailAddress(organization_id=org2.id, email="contact@apexhospital.example", normalized_email="contact@apexhospital.example")
    db_session.add_all([w2, p2, e_invalid, e_valid])

    # Org 3: Distinct organization (City Clinic)
    org3 = Organization(name="City Clinic", city="Puducherry")
    db_session.add(org3)
    await db_session.flush()
    w3 = Website(organization_id=org3.id, url="https://cityclinic.example", normalized_url="https://cityclinic.example", is_official=True)
    p3 = PhoneNumber(organization_id=org3.id, phone_number="9443322110", normalized_phone="+919443322110")
    db_session.add_all([w3, p3])
    await db_session.flush()

    # Link all 3 orgs to task & leads
    await db_session.execute(task_organizations.insert().values([
        {"task_id": task.id, "organization_id": org1.id},
        {"task_id": task.id, "organization_id": org2.id},
        {"task_id": task.id, "organization_id": org3.id},
    ]))
    db_session.add_all([
        Lead(task_id=task.id, organization_id=org1.id),
        Lead(task_id=task.id, organization_id=org2.id),
        Lead(task_id=task.id, organization_id=org3.id),
    ])
    await db_session.flush()

    # Execute cleaning pipeline
    service = CleaningService(db_session)
    result = await service.clean_task(task.task_id)

    assert result.status == "Cleaning completed"
    assert result.next_stage == "VERIFYING"
    assert result.organizations_merged == 1
    assert result.invalid_phones_removed == 1
    assert result.invalid_emails_removed == 1
    assert result.phones_cleaned >= 1
    assert result.emails_cleaned >= 1
    assert result.total_duplicates_removed > 0

    # Verify task state in database
    await db_session.refresh(task)
    assert task.current_stage == "VERIFYING"
    assert task.progress == 85
    assert task.status == "RUNNING"
    assert task.duplicates_removed > 0

    # Verify logs
    stmt_logs = select(ScrapingLog).where(ScrapingLog.task_id == task.id)
    logs = list((await db_session.execute(stmt_logs)).scalars().all())
    event_types = {l.event_type for l in logs}
    assert "ORGANIZATION_MERGED" in event_types
    assert "CLEANING_COMPLETED" in event_types


# ── 11. Idempotency Test ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cleaning_service_idempotency(db_session: AsyncSession):
    user = User(
        id=uuid.uuid4(),
        name="User Idempotent",
        email=f"idem_{uuid.uuid4().hex[:6]}@leadscout.app",
        password_hash="hash",
    )
    db_session.add(user)
    await db_session.flush()

    task = ScrapingTask(
        task_id="TASK-CLEAN-IDEM",
        user_id=user.id,
        keyword="Hotels",
        location="Puducherry",
        status="RUNNING",
    )
    db_session.add(task)
    await db_session.flush()

    org = Organization(name="Grand Hotel", city="Puducherry")
    db_session.add(org)
    await db_session.flush()
    await db_session.execute(task_organizations.insert().values([
        {"task_id": task.id, "organization_id": org.id}
    ]))
    db_session.add(Lead(task_id=task.id, organization_id=org.id))
    await db_session.flush()

    service = CleaningService(db_session)
    res1 = await service.clean_task(task.task_id)
    res2 = await service.clean_task(task.task_id)

    assert res2.organizations_merged == 0
    assert res2.next_stage == "VERIFYING"
    await db_session.refresh(task)
    assert task.current_stage == "VERIFYING"
    assert task.progress == 85


# ── 12. Cross-Task Organization Preservation Test ─────────────────────────────


@pytest.mark.asyncio
async def test_cross_task_preservation(db_session: AsyncSession):
    user = User(
        id=uuid.uuid4(),
        name="Multi Task User",
        email=f"multi_{uuid.uuid4().hex[:6]}@leadscout.app",
        password_hash="hash",
    )
    db_session.add(user)
    await db_session.flush()

    task1 = ScrapingTask(
        task_id="TASK-CROSS-1",
        user_id=user.id,
        keyword="Schools",
        location="Puducherry",
        status="RUNNING",
    )
    task2 = ScrapingTask(
        task_id="TASK-CROSS-2",
        user_id=user.id,
        keyword="Education",
        location="Puducherry",
        status="RUNNING",
    )
    db_session.add_all([task1, task2])
    await db_session.flush()

    org_a = Organization(name="Preserved Academy", city="Puducherry")
    org_b = Organization(name="Preserved Academy Pvt Ltd", city="Puducherry")
    db_session.add_all([org_a, org_b])
    await db_session.flush()

    w_a = Website(organization_id=org_a.id, url="https://preserved.edu", normalized_url="https://preserved.edu", is_official=True)
    p_a = PhoneNumber(organization_id=org_a.id, phone_number="9876543210", normalized_phone="+919876543210")
    w_b = Website(organization_id=org_b.id, url="https://preserved.edu/about", normalized_url="https://preserved.edu/about")
    p_b = PhoneNumber(organization_id=org_b.id, phone_number="9876543210", normalized_phone="+919876543210")
    db_session.add_all([w_a, p_a, w_b, p_b])
    await db_session.flush()

    # Link org_a and org_b to task1
    # AND link org_a to task2
    await db_session.execute(task_organizations.insert().values([
        {"task_id": task1.id, "organization_id": org_a.id},
        {"task_id": task1.id, "organization_id": org_b.id},
        {"task_id": task2.id, "organization_id": org_a.id},
    ]))
    db_session.add_all([
        Lead(task_id=task1.id, organization_id=org_a.id),
        Lead(task_id=task1.id, organization_id=org_b.id),
        Lead(task_id=task2.id, organization_id=org_a.id),
    ])
    await db_session.flush()

    # Clean task1 only
    service = CleaningService(db_session)
    res = await service.clean_task(task1.task_id)
    assert res.organizations_merged == 1

    # Verify task2 is STILL linked to canonical org_a!
    stmt_t2 = select(task_organizations.c.organization_id).where(
        task_organizations.c.task_id == task2.id
    )
    t2_org_ids = list((await db_session.execute(stmt_t2)).scalars().all())
    assert org_a.id in t2_org_ids


# ── 13. CLI Runner Execution Test ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_run_cleaning_cli_runner(monkeypatch, capsys, db_session: AsyncSession):
    from app.jobs.run_cleaning import main as run_cleaning_main

    async def mock_dispose():
        pass

    monkeypatch.setattr("app.jobs.run_cleaning.create_engine_and_factory", lambda: None)
    monkeypatch.setattr("app.jobs.run_cleaning.dispose_engine", mock_dispose)

    class MockContext:
        async def __aenter__(self):
            return db_session

        async def __aexit__(self, *args):
            pass

    monkeypatch.setattr("app.jobs.run_cleaning.get_session_factory", lambda: lambda: MockContext())

    user = User(
        id=uuid.uuid4(),
        name="CLI User",
        email=f"cli_{uuid.uuid4().hex[:6]}@leadscout.app",
        password_hash="hash",
    )
    db_session.add(user)
    await db_session.flush()

    task = ScrapingTask(
        task_id="TASK-CLI-CLEAN",
        user_id=user.id,
        keyword="Colleges",
        location="Puducherry",
        status="RUNNING",
    )
    db_session.add(task)
    await db_session.flush()

    await run_cleaning_main(task.task_id)

    captured = capsys.readouterr().out
    assert "Task: TASK-CLI-CLEAN" in captured
    assert "Organizations Processed: 0" in captured
    assert "Organizations Merged: 0" in captured
    assert "Status: Cleaning completed" in captured
    assert "Next Stage: VERIFYING" in captured
