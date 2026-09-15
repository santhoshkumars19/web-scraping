"""
tests/test_verification.py

Comprehensive test suite for Backend Step 8:
Lead Data-Quality Verification & Confidence Scoring Engine.
"""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.jobs.verification_job import run_verification
from app.models.contact import Contact
from app.models.email_address import EmailAddress
from app.models.extracted_field import ExtractedField
from app.models.lead import Lead
from app.models.lead_verification import LeadVerification
from app.models.organization import Organization, task_organizations
from app.models.phone_number import PhoneNumber
from app.models.scraping_log import ScrapingLog
from app.models.scraping_task import ScrapingTask
from app.models.social_link import SocialLink
from app.models.source_page import SourcePage
from app.models.user import User
from app.models.website import Website
from app.services.verification.confidence_scorer import ConfidenceScorer
from app.services.verification.consistency_checker import (
    ConsistencyResult,
    check_consistency,
)
from app.services.verification.field_completeness import (
    CompletenessResult,
    calculate_field_completeness,
)
from app.services.verification.source_quality import (
    FieldSourceInfo,
    SourceQualityResult,
    assess_source_quality,
)
from app.services.verification.verification_rules import (
    HIGH_THRESHOLD,
    MEDIUM_THRESHOLD,
)
from app.services.verification.verification_service import VerificationService


# ── 1. Field Completeness Calculation Tests ────────────────────────────────────


def test_field_completeness_all_fields_present():
    """Verify 100% completeness when all requested fields exist."""
    org = Organization(
        name="Oakridge International School",
        address="123 Main Road",
        city="Puducherry",
        state="Puducherry",
        pincode="605001",
    )
    org.websites = [Website(url="https://oakridge.example", normalized_url="https://oakridge.example")]
    org.phone_numbers = [PhoneNumber(phone_number="+91 98765 43210", normalized_phone="+919876543210", is_whatsapp=True)]
    org.email_addresses = [EmailAddress(email="admissions@oakridge.example", normalized_email="admissions@oakridge.example")]
    org.contacts = [Contact(name="Dr. Jane Smith", designation="Principal")]
    org.social_links = [SocialLink(platform="FACEBOOK", url="https://facebook.com/oakridge")]

    result = calculate_field_completeness(
        org=org,
        selected_fields=["name", "website", "phone", "email", "address", "whatsapp", "contact_person", "social_links"],
    )

    assert result.fields_found == 8
    assert result.total_fields == 8
    assert result.percentage == 100.0
    assert result.weighted_score == 100.0
    assert all(result.field_availability.values())


def test_field_completeness_selected_fields_filtering():
    """Verify completeness is strictly evaluated against selected fields only."""
    org = Organization(name="St. Paul High School")
    org.phone_numbers = [PhoneNumber(phone_number="+91 413 2234567", normalized_phone="+914132234567")]
    org.email_addresses = [EmailAddress(email="info@stpaul.example", normalized_email="info@stpaul.example")]
    # Note: no website, no address, no social links, no contacts

    # User task only asked for phone and email
    result = calculate_field_completeness(
        org=org,
        selected_fields=["phone", "email"],
    )

    assert result.fields_found == 2
    assert result.total_fields == 2
    assert result.percentage == 100.0
    assert result.weighted_score == 100.0
    assert result.field_availability["phone"] is True
    assert result.field_availability["email"] is True
    # Unrequested fields must not be in the evaluation
    assert "website" not in result.field_availability
    assert "address" not in result.field_availability


def test_field_completeness_partial():
    """Verify partial completeness calculation when some requested fields are missing."""
    org = Organization(name="Sunshine Preschool")
    org.phone_numbers = [PhoneNumber(phone_number="+91 98765 00000", normalized_phone="+919876500000")]

    result = calculate_field_completeness(
        org=org,
        selected_fields=["name", "website", "phone", "email"],
    )

    assert result.fields_found == 2  # name and phone
    assert result.total_fields == 4
    assert result.percentage == 50.0
    assert result.field_availability["name"] is True
    assert result.field_availability["phone"] is True
    assert result.field_availability["website"] is False
    assert result.field_availability["email"] is False


def test_field_completeness_ignores_placeholders():
    """Verify placeholder values like 'N/A' or 'None' are treated as missing."""
    org = Organization(
        name="Real Academy",
        address="N/A",
        city="none",
        pincode="undefined",
    )
    org.contacts = [Contact(name="dummy")]

    result = calculate_field_completeness(
        org=org,
        selected_fields=["name", "address", "contact_person"],
    )

    assert result.field_availability["name"] is True
    assert result.field_availability["address"] is False
    assert result.field_availability["contact_person"] is False
    assert result.fields_found == 1
    assert result.total_fields == 3


# ── 2. Source Quality Assessment Tests ─────────────────────────────────────────


def test_source_quality_official_pages():
    """Verify high source quality score when data originates from official contact/about pages."""
    org_id = uuid.uuid4()
    page_id = uuid.uuid4()
    org = Organization(id=org_id, name="Greenfield Academy")
    org.websites = [Website(url="https://greenfield.edu", is_official=True)]

    sp = SourcePage(
        id=page_id,
        organization_id=org_id,
        url="https://greenfield.edu/contact-us",
        page_type="CONTACT",
    )
    org.source_pages = [sp]

    ef_phone = ExtractedField(
        organization_id=org_id,
        source_page_id=page_id,
        field_name="phone",
        field_value="+91 413 2221111",
    )
    ef_email = ExtractedField(
        organization_id=org_id,
        source_page_id=page_id,
        field_name="email",
        field_value="principal@greenfield.edu",
    )

    field_avail = {"name": True, "phone": True, "email": True}
    res = assess_source_quality(
        org=org,
        field_availability=field_avail,
        extracted_fields=[ef_phone, ef_email],
        source_pages=[sp],
    )

    assert res.score >= 90.0
    assert res.details.official_website_fields == 2
    assert res.details.directory_fields == 0
    assert res.details.fields_with_source == 2
    assert res.field_sources["phone"].source_page_type == "CONTACT"
    assert res.field_sources["phone"].score == 100.0


def test_source_quality_directory_source():
    """Verify directory-sourced data receives appropriate directory quality score (60.0)."""
    org_id = uuid.uuid4()
    page_id = uuid.uuid4()
    org = Organization(id=org_id, name="City Clinic")

    sp = SourcePage(
        id=page_id,
        organization_id=org_id,
        url="https://www.justdial.com/Puducherry/City-Clinic",
        page_type="OTHER",
    )
    org.source_pages = [sp]

    ef = ExtractedField(
        organization_id=org_id,
        source_page_id=page_id,
        field_name="phone",
        field_value="+91 413 9999999",
    )

    res = assess_source_quality(
        org=org,
        field_availability={"phone": True},
        extracted_fields=[ef],
        source_pages=[sp],
    )

    assert res.score == 60.0
    assert res.details.directory_fields == 1
    assert res.details.official_website_fields == 0
    assert res.field_sources["phone"].source_type == "DIRECTORY"


def test_source_quality_no_provenance_fallback():
    """Verify fallback scores when provenance records are missing."""
    org = Organization(name="Unknown Org")
    res = assess_source_quality(
        org=org,
        field_availability={"phone": True, "email": True},
        extracted_fields=[],
        source_pages=[],
    )

    # Without official website or source pages, basic fallback score is applied
    assert res.score <= 70.0
    assert res.details.fields_with_source == 0
    assert res.field_sources["phone"].source_present is False


# ── 3. Cross-Field Consistency Tests ──────────────────────────────────────────


def test_consistency_domain_match():
    """Verify 100 score and EMAIL_DOMAIN_MATCH flag when website and email share root domain."""
    org = Organization(name="Excel Academy")
    org.websites = [Website(url="https://excelacademy.org", normalized_url="https://excelacademy.org")]
    org.email_addresses = [EmailAddress(email="admissions@excelacademy.org", normalized_email="admissions@excelacademy.org")]
    org.phone_numbers = [PhoneNumber(phone_number="+91 98765 43210", normalized_phone="+919876543210")]

    res = check_consistency(org)

    assert res.score == 100.0
    assert "EMAIL_DOMAIN_MATCH" in res.flags
    assert len(res.conflicts) == 0


def test_consistency_generic_email_domain():
    """Verify WEAK_CONSISTENCY_SIGNAL and moderate score when using Gmail/Yahoo."""
    org = Organization(name="Little Stars Kindergarten")
    org.websites = [Website(url="https://littlestars.com", normalized_url="https://littlestars.com")]
    org.email_addresses = [EmailAddress(email="littlestars@gmail.com", normalized_email="littlestars@gmail.com")]

    res = check_consistency(org)

    assert "WEAK_CONSISTENCY_SIGNAL" in res.flags
    assert 70.0 <= res.score <= 85.0


def test_consistency_conflicting_phones_flagged():
    """Verify POSSIBLE_CONFLICT is flagged without deleting data when distinct phones exist."""
    org = Organization(name="Metro Hospital")
    org.phone_numbers = [
        PhoneNumber(phone_number="+91 413 2220001", normalized_phone="+914132220001", phone_type="OFFICE"),
        PhoneNumber(phone_number="+91 413 2220002", normalized_phone="+914132220002", phone_type="OFFICE"),
    ]

    res = check_consistency(org)

    assert "POSSIBLE_CONFLICT" in res.flags
    assert any("Multiple" in c and "phone numbers" in c for c in res.conflicts)
    assert res.score < 100.0


# ── 4. Confidence Scorer Tests ────────────────────────────────────────────────


def test_confidence_scorer_deterministic_formula():
    """Verify formula: Score = (Completeness * 50%) + (Source Quality * 30%) + (Consistency * 20%)."""
    org_id = uuid.uuid4()
    comp = CompletenessResult(
        fields_found=4,
        total_fields=4,
        percentage=100.0,
        weighted_score=100.0,
        field_availability={"phone": True, "email": True, "website": True, "name": True},
    )
    src = SourceQualityResult(
        score=90.0,
        details=None,  # will be handled
        field_sources={},
    )
    from app.schemas.verification import SourceQualityDetails
    src.details = SourceQualityDetails(official_website_fields=2, total_evaluated_fields=4)

    cons = ConsistencyResult(
        score=80.0,
        flags=["EMAIL_DOMAIN_MATCH"],
        conflicts=[],
        field_consistency={},
    )

    # Expected: (100 * 0.50) + (90 * 0.30) + (80 * 0.20) = 50 + 27 + 16 = 93
    res = ConfidenceScorer.compute(
        task_id="TASK-001",
        organization_id=org_id,
        completeness=comp,
        source_quality=src,
        consistency=cons,
    )

    assert res.score == 93
    assert res.status == "HIGH"
    assert "completeness" in res.reasons
    assert "sources" in res.reasons
    assert "consistency" in res.reasons


def test_confidence_scorer_threshold_tiers():
    """Verify threshold boundary mappings: HIGH >= 80, MEDIUM 60-79, LOW < 60."""
    org_id = uuid.uuid4()
    from app.schemas.verification import SourceQualityDetails

    def make_res(comp_score: float, src_score: float, cons_score: float):
        comp = CompletenessResult(
            fields_found=1, total_fields=1, percentage=comp_score,
            weighted_score=comp_score, field_availability={"phone": True},
        )
        src = SourceQualityResult(
            score=src_score, details=SourceQualityDetails(), field_sources={},
        )
        cons = ConsistencyResult(
            score=cons_score, flags=[], conflicts=[], field_consistency={},
        )
        return ConfidenceScorer.compute(
            task_id="TASK-TEST",
            organization_id=org_id,
            completeness=comp,
            source_quality=src,
            consistency=cons,
        )

    # 1. High Tier (>= 80)
    high_res = make_res(80.0, 80.0, 80.0)
    assert high_res.score == 80
    assert high_res.status == "HIGH"

    # 2. Medium Tier (60 - 79)
    med_res = make_res(65.0, 60.0, 60.0)
    assert 60 <= med_res.score < 80
    assert med_res.status == "MEDIUM"

    # 3. Low Tier (< 60)
    low_res = make_res(40.0, 40.0, 40.0)
    assert low_res.score < 60
    assert low_res.status == "LOW"


# ── 5. VerificationService End-to-End Database Tests ──────────────────────────


@pytest.mark.asyncio
async def test_verification_service_full_workflow(db_session: AsyncSession):
    """Verify full end-to-end verification execution, DB persistence, and stage advancement."""
    # 1. Setup User and Task
    user = User(name="Scout Master", email="master@example.com", password_hash="hash")
    db_session.add(user)
    await db_session.commit()

    task = ScrapingTask(
        task_id="TASK-VERIFY-01",
        user_id=user.id,
        location="Puducherry",
        keyword="Schools",
        selected_fields=["name", "website", "phone", "email"],
        status="RUNNING",
        current_stage="VERIFYING",
        progress=85,
    )
    db_session.add(task)
    await db_session.commit()

    # 2. Setup Organization with rich data and provenance
    org = Organization(
        name="Puducherry Central School",
        address="10 Mission Street",
        city="Puducherry",
        state="Puducherry",
        pincode="605001",
    )
    db_session.add(org)
    await db_session.commit()

    # Link via task_organizations and create Lead
    await db_session.execute(
        task_organizations.insert().values(task_id=task.id, organization_id=org.id)
    )
    lead = Lead(
        task_id=task.id,
        organization_id=org.id,
        status="ACTIVE",
        verification_status="PENDING",
    )
    db_session.add(lead)

    # Add child models
    website = Website(
        organization_id=org.id,
        url="https://pcschool.org",
        normalized_url="https://pcschool.org",
        is_official=True,
    )
    phone = PhoneNumber(
        organization_id=org.id,
        phone_number="+91 413 2224444",
        normalized_phone="+914132224444",
        phone_type="OFFICE",
        is_primary=True,
    )
    email = EmailAddress(
        organization_id=org.id,
        email="info@pcschool.org",
        normalized_email="info@pcschool.org",
        email_type="GENERAL",
        is_primary=True,
    )
    source_page = SourcePage(
        organization_id=org.id,
        website_id=website.id,
        url="https://pcschool.org/contact",
        normalized_url="https://pcschool.org/contact",
        page_type="CONTACT",
        http_status=200,
    )
    db_session.add_all([website, phone, email, source_page])
    await db_session.commit()

    ef = ExtractedField(
        organization_id=org.id,
        source_page_id=source_page.id,
        field_name="phone",
        field_value="+91 413 2224444",
        normalized_value="+914132224444",
    )
    db_session.add(ef)
    await db_session.commit()

    # 3. Execute Verification Service
    service = VerificationService(db_session)
    summary = await service.verify_task(task.task_id)

    # 4. Verify Summary Results
    assert summary.task_id == task.task_id
    assert summary.leads_processed == 1
    assert summary.high_confidence_count == 1
    assert summary.medium_confidence_count == 0
    assert summary.low_confidence_count == 0
    assert summary.pending_count == 0
    assert summary.next_stage == "SAVING"
    assert summary.average_completeness == 100.0

    # 5. Verify Database State
    stmt_v = select(LeadVerification).where(LeadVerification.lead_id == lead.id)
    v_record = (await db_session.execute(stmt_v)).scalar_one_or_none()
    assert v_record is not None
    assert v_record.status == "HIGH"
    assert v_record.score >= HIGH_THRESHOLD
    assert v_record.completeness_percentage == 100.0
    assert v_record.verified_at is not None
    assert "completeness" in v_record.verification_reasons
    assert v_record.source_quality_details["fields_with_source"] >= 1

    # Verify Lead model state
    stmt_lead = select(Lead).where(Lead.id == lead.id)
    updated_lead = (await db_session.execute(stmt_lead)).scalar_one()
    assert updated_lead.verification_status == "HIGH"

    # Verify ScrapingTask state
    stmt_t = select(ScrapingTask).where(ScrapingTask.id == task.id)
    updated_task = (await db_session.execute(stmt_t)).scalar_one()
    assert updated_task.current_stage == "SAVING"
    assert updated_task.progress == 95
    assert updated_task.status == "RUNNING"
    assert updated_task.verified_count == 1
    assert updated_task.high_confidence_count == 1

    # Verify audit logs
    stmt_logs = select(ScrapingLog).where(ScrapingLog.task_id == task.id)
    logs = list((await db_session.execute(stmt_logs)).scalars().all())
    assert any(l.event_type == "VERIFICATION_COMPLETED" for l in logs)


@pytest.mark.asyncio
async def test_verification_multi_task_isolation(db_session: AsyncSession):
    """Verify that the same organization in two different tasks has task-specific verification scores."""
    user = User(name="Test User", email="multi@example.com", password_hash="hash")
    db_session.add(user)
    await db_session.commit()

    # Org only has website and address, but NO phone and NO email
    org = Organization(name="MultiTask Academy", address="100 Boulevard", city="Puducherry")
    website = Website(url="https://multitask.edu", normalized_url="https://multitask.edu")
    org.websites = [website]
    db_session.add(org)
    await db_session.commit()

    # Task A wants phone and email (which org lacks) -> LOW score
    task_a = ScrapingTask(
        task_id="TASK-MULTI-A",
        user_id=user.id,
        location="Puducherry",
        keyword="Academy",
        selected_fields=["phone", "email"],
    )
    # Task B wants website and address (which org HAS) -> HIGH score
    task_b = ScrapingTask(
        task_id="TASK-MULTI-B",
        user_id=user.id,
        location="Puducherry",
        keyword="Academy",
        selected_fields=["website", "address"],
    )
    db_session.add_all([task_a, task_b])
    await db_session.commit()

    lead_a = Lead(task_id=task_a.id, organization_id=org.id, status="ACTIVE")
    lead_b = Lead(task_id=task_b.id, organization_id=org.id, status="ACTIVE")
    db_session.add_all([lead_a, lead_b])
    await db_session.commit()

    service = VerificationService(db_session)

    # Verify Task A
    summary_a = await service.verify_task(task_a.task_id)
    # Verify Task B
    summary_b = await service.verify_task(task_b.task_id)

    # Task A leads should have 0% completeness and LOW confidence
    assert summary_a.average_completeness == 0.0
    assert summary_a.low_confidence_count == 1

    # Task B leads should have 100% completeness and HIGH confidence
    assert summary_b.average_completeness == 100.0
    assert summary_b.high_confidence_count == 1

    # Both LeadVerifications exist independently
    stmt_v_a = select(LeadVerification).where(LeadVerification.lead_id == lead_a.id)
    stmt_v_b = select(LeadVerification).where(LeadVerification.lead_id == lead_b.id)
    v_a = (await db_session.execute(stmt_v_a)).scalar_one()
    v_b = (await db_session.execute(stmt_v_b)).scalar_one()

    assert v_a.status == "LOW"
    assert v_b.status == "HIGH"
    assert v_a.id != v_b.id


@pytest.mark.asyncio
async def test_verification_idempotency(db_session: AsyncSession):
    """Verify running verification twice updates the existing LeadVerification record without errors."""
    user = User(name="Idemp User", email="idemp@example.com", password_hash="hash")
    db_session.add(user)
    await db_session.commit()

    task = ScrapingTask(
        task_id="TASK-IDEMP-01",
        user_id=user.id,
        location="Puducherry",
        keyword="Colleges",
        selected_fields=["name", "website"],
    )
    db_session.add(task)
    await db_session.commit()

    org = Organization(name="Idempotent College")
    org.websites = [Website(url="https://idempcollege.edu", normalized_url="https://idempcollege.edu")]
    db_session.add(org)
    await db_session.commit()

    lead = Lead(task_id=task.id, organization_id=org.id, status="ACTIVE")
    db_session.add(lead)
    await db_session.commit()

    service = VerificationService(db_session)

    # Run 1
    summary_1 = await service.verify_task(task.task_id)
    assert summary_1.leads_processed == 1

    # Run 2
    summary_2 = await service.verify_task(task.task_id)
    assert summary_2.leads_processed == 1

    # Only 1 verification record should exist
    stmt_v = select(LeadVerification).where(LeadVerification.lead_id == lead.id)
    v_records = list((await db_session.execute(stmt_v)).scalars().all())
    assert len(v_records) == 1


@pytest.mark.asyncio
async def test_verification_failure_isolation(db_session: AsyncSession):
    """Verify that an unexpected error on one lead does not crash the entire task."""
    user = User(name="Iso User", email="iso@example.com", password_hash="hash")
    db_session.add(user)
    await db_session.commit()

    task = ScrapingTask(
        task_id="TASK-FAIL-ISO",
        user_id=user.id,
        location="Puducherry",
        keyword="Clinics",
    )
    db_session.add(task)
    await db_session.commit()

    org1 = Organization(name="Good Clinic")
    org2 = Organization(name="Problematic Clinic")
    db_session.add_all([org1, org2])
    await db_session.commit()

    lead1 = Lead(task_id=task.id, organization_id=org1.id)
    lead2 = Lead(task_id=task.id, organization_id=org2.id)
    db_session.add_all([lead1, lead2])
    await db_session.commit()

    service = VerificationService(db_session)

    # Mock calculate_field_completeness to raise for org2
    original_calc = calculate_field_completeness

    def side_effect(org, selected_fields=None, custom_weights=None):
        if org.name == "Problematic Clinic":
            raise RuntimeError("Simulated corruption in organization data")
        return original_calc(org, selected_fields, custom_weights)

    with patch(
        "app.services.verification.verification_service.calculate_field_completeness",
        side_effect=side_effect,
    ):
        summary = await service.verify_task(task.task_id)

    # 1 succeeded, 1 pending
    assert summary.leads_processed == 1
    assert summary.pending_count == 1

    # Check lead statuses
    stmt_l1 = select(Lead).where(Lead.id == lead1.id)
    stmt_l2 = select(Lead).where(Lead.id == lead2.id)
    assert (await db_session.execute(stmt_l1)).scalar_one().verification_status in ("HIGH", "MEDIUM", "LOW")
    assert (await db_session.execute(stmt_l2)).scalar_one().verification_status == "PENDING"

    # ScrapingLog for failed lead
    stmt_log = select(ScrapingLog).where(
        ScrapingLog.task_id == task.id,
        ScrapingLog.event_type == "VERIFICATION_FAILED",
    )
    err_log = (await db_session.execute(stmt_log)).scalar_one_or_none()
    assert err_log is not None
    assert "Simulated corruption" in err_log.message


@pytest.mark.asyncio
async def test_run_verification_job(db_session: AsyncSession):
    """Verify run_verification job function behaves identically."""
    user = User(name="Job User", email="job@example.com", password_hash="hash")
    db_session.add(user)
    await db_session.commit()

    task = ScrapingTask(
        task_id="TASK-JOB-01",
        user_id=user.id,
        location="Chennai",
        keyword="Hotels",
        selected_fields=["name", "website"],
    )
    db_session.add(task)
    await db_session.commit()

    org = Organization(name="Grand Hotel")
    org.websites = [Website(url="https://grandhotel.example", normalized_url="https://grandhotel.example")]
    db_session.add(org)
    await db_session.commit()

    lead = Lead(task_id=task.id, organization_id=org.id)
    db_session.add(lead)
    await db_session.commit()

    summary = await run_verification(task.task_id, session=db_session)
    assert summary.task_id == task.task_id
    assert summary.leads_processed == 1
    assert summary.next_stage == "SAVING"


@pytest.mark.asyncio
async def test_run_verification_cli(db_session: AsyncSession, monkeypatch, capsys):
    """Verify run_verification development CLI runner executes and prints formatted metrics."""
    from app.jobs.run_verification import main as run_verification_main

    async def mock_dispose():
        pass

    monkeypatch.setattr("app.jobs.run_verification.create_engine_and_factory", lambda: None)
    monkeypatch.setattr("app.jobs.run_verification.dispose_engine", mock_dispose)

    class MockContext:
        async def __aenter__(self):
            return db_session

        async def __aexit__(self, *args):
            pass

    monkeypatch.setattr("app.jobs.run_verification.get_session_factory", lambda: lambda: MockContext())

    user = User(
        id=uuid.uuid4(),
        name="CLI Master",
        email=f"cli_ver_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="hash",
    )
    db_session.add(user)
    await db_session.commit()

    task = ScrapingTask(
        task_id="TASK-CLI-VERIFY",
        user_id=user.id,
        keyword="Schools",
        location="Puducherry",
        status="RUNNING",
        current_stage="VERIFYING",
        progress=85,
    )
    db_session.add(task)
    await db_session.commit()

    await run_verification_main(task.task_id)

    captured = capsys.readouterr().out
    assert "Task: TASK-CLI-VERIFY" in captured
    assert "Leads Processed: 0" in captured
    assert "Status: Verification completed" in captured
    assert "Next Stage: SAVING" in captured

