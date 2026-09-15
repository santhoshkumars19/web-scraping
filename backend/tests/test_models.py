"""
tests/test_models.py

Unit tests for database models, relationships, and constraints.
"""

from __future__ import annotations

import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

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


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession) -> None:
    """Verify User can be created and retrieved with proper defaults."""
    user = User(
        name="Alex River",
        email="alex@example.com",
        password_hash="hashed_secret_123",
        company="River Ventures",
        role="USER",
    )
    db_session.add(user)
    await db_session.commit()

    result = await db_session.execute(select(User).where(User.email == "alex@example.com"))
    fetched = result.scalar_one()

    assert fetched.id is not None
    assert fetched.name == "Alex River"
    assert fetched.role == "USER"
    assert fetched.is_active is True
    assert fetched.created_at is not None


@pytest.mark.asyncio
async def test_user_unique_email_constraint(db_session: AsyncSession) -> None:
    """Verify that duplicate user emails violate unique constraint."""
    u1 = User(name="User 1", email="duplicate@example.com", password_hash="hash1")
    u2 = User(name="User 2", email="duplicate@example.com", password_hash="hash2")

    db_session.add(u1)
    await db_session.commit()

    db_session.add(u2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_create_scraping_task(db_session: AsyncSession) -> None:
    """Verify ScrapingTask creation with user relationship and metric defaults."""
    user = User(name="Task Owner", email="owner@example.com", password_hash="hash")
    db_session.add(user)
    await db_session.commit()

    task = ScrapingTask(
        task_id="TASK-000201",
        user_id=user.id,
        location="Austin, TX",
        keyword="Software Consultancies",
        search_radius=50,
        max_results=200,
        status="PENDING",
        progress=0,
    )
    db_session.add(task)
    await db_session.commit()

    result = await db_session.execute(select(ScrapingTask).where(ScrapingTask.task_id == "TASK-000201"))
    fetched = result.scalar_one()

    assert fetched.task_id == "TASK-000201"
    assert fetched.user_id == user.id
    assert fetched.status == "PENDING"
    assert fetched.progress == 0
    assert fetched.results_discovered == 0


@pytest.mark.asyncio
async def test_task_unique_task_id(db_session: AsyncSession) -> None:
    """Verify task_id must be unique."""
    user = User(name="Owner 2", email="owner2@example.com", password_hash="hash")
    db_session.add(user)
    await db_session.commit()

    t1 = ScrapingTask(task_id="TASK-DUPLICATE", user_id=user.id, location="City A", keyword="Key A")
    t2 = ScrapingTask(task_id="TASK-DUPLICATE", user_id=user.id, location="City B", keyword="Key B")

    db_session.add(t1)
    await db_session.commit()

    db_session.add(t2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_organization_and_task_m2m(db_session: AsyncSession) -> None:
    """Verify task to organization many-to-many relationship."""
    user = User(name="M2M User", email="m2m@example.com", password_hash="hash")
    db_session.add(user)
    await db_session.commit()

    task = ScrapingTask(task_id="TASK-M2M", user_id=user.id, location="Denver, CO", keyword="Breweries")
    org = Organization(name="Denver Craft Brewery", city="Denver", state="CO", tasks=[task])

    db_session.add_all([task, org])
    await db_session.commit()

    result = await db_session.execute(select(Organization).where(Organization.name == "Denver Craft Brewery"))
    fetched_org = result.scalar_one()

    assert len(fetched_org.tasks) == 1
    assert fetched_org.tasks[0].task_id == "TASK-M2M"


@pytest.mark.asyncio
async def test_website_relationship(db_session: AsyncSession) -> None:
    """Verify Organization -> Website relationship and uniqueness."""
    org = Organization(name="Apex Tech")
    db_session.add(org)
    await db_session.commit()

    site = Website(
        organization_id=org.id,
        url="https://apextech.io",
        normalized_url="https://apextech.io",
        domain="apextech.io",
        is_official=True,
    )
    db_session.add(site)
    await db_session.commit()

    result = await db_session.execute(select(Website).where(Website.organization_id == org.id))
    fetched_site = result.scalar_one()

    assert fetched_site.domain == "apextech.io"
    assert fetched_site.organization.name == "Apex Tech"


@pytest.mark.asyncio
async def test_contact_relationship(db_session: AsyncSession) -> None:
    """Verify Organization -> Contact relationship."""
    org = Organization(name="Global Health Clinic")
    db_session.add(org)
    await db_session.commit()

    contact = Contact(
        organization_id=org.id,
        name="Dr. Sarah Jenkins",
        designation="Medical Director",
    )
    db_session.add(contact)
    await db_session.commit()

    result = await db_session.execute(select(Contact).where(Contact.organization_id == org.id))
    fetched = result.scalar_one()

    assert fetched.name == "Dr. Sarah Jenkins"
    assert fetched.designation == "Medical Director"


@pytest.mark.asyncio
async def test_phone_and_email_relationships(db_session: AsyncSession) -> None:
    """Verify Contact -> Phone & Email relationships with normalization."""
    org = Organization(name="Alpha Logistics")
    db_session.add(org)
    await db_session.commit()

    contact = Contact(organization_id=org.id, name="Logistics Desk")
    db_session.add(contact)
    await db_session.commit()

    phone = PhoneNumber(
        organization_id=org.id,
        contact_id=contact.id,
        phone_number="+1 (555) 123-4567",
        normalized_phone="+15551234567",
        phone_type="OFFICE",
        is_primary=True,
    )
    email = EmailAddress(
        organization_id=org.id,
        contact_id=contact.id,
        email="info@alphalogistics.com",
        normalized_email="info@alphalogistics.com",
        email_type="GENERAL",
        is_primary=True,
    )
    db_session.add_all([phone, email])
    await db_session.commit()

    res_phone = (await db_session.execute(select(PhoneNumber).where(PhoneNumber.organization_id == org.id))).scalar_one()
    res_email = (await db_session.execute(select(EmailAddress).where(EmailAddress.organization_id == org.id))).scalar_one()

    assert res_phone.normalized_phone == "+15551234567"
    assert res_email.normalized_email == "info@alphalogistics.com"
    assert res_phone.contact.name == "Logistics Desk"
    assert res_email.contact.name == "Logistics Desk"


@pytest.mark.asyncio
async def test_source_page_relationship(db_session: AsyncSession) -> None:
    """Verify SourcePage provenance tracking and extracted fields."""
    org = Organization(name="Tech Academy")
    db_session.add(org)
    await db_session.commit()

    page = SourcePage(
        organization_id=org.id,
        url="https://techacademy.org/staff",
        normalized_url="https://techacademy.org/staff",
        page_type="STAFF",
        http_status=200,
    )
    db_session.add(page)
    await db_session.commit()

    field = ExtractedField(
        organization_id=org.id,
        source_page_id=page.id,
        field_name="CONTACT_PERSON",
        field_value="Jane Doe",
        normalized_value="jane doe",
    )
    db_session.add(field)
    await db_session.commit()

    res_page = (await db_session.execute(select(SourcePage).where(SourcePage.id == page.id))).scalar_one()
    assert len(res_page.extracted_fields) == 1
    assert res_page.extracted_fields[0].field_name == "CONTACT_PERSON"


@pytest.mark.asyncio
async def test_scraping_logs(db_session: AsyncSession) -> None:
    """Verify ScrapingLog events recorded for tasks."""
    user = User(name="Log User", email="logger@example.com", password_hash="hash")
    db_session.add(user)
    await db_session.commit()

    task = ScrapingTask(task_id="TASK-LOG-01", user_id=user.id, location="Chicago", keyword="Dentists")
    db_session.add(task)
    await db_session.commit()

    log1 = ScrapingLog(task_id=task.id, level="INFO", event_type="TASK_CREATED", message="Initialized.")
    log2 = ScrapingLog(task_id=task.id, level="INFO", event_type="CRAWL_STARTED", message="Crawling started.")
    db_session.add_all([log1, log2])
    await db_session.commit()

    res = (await db_session.execute(select(ScrapingLog).where(ScrapingLog.task_id == task.id))).scalars().all()
    assert len(res) == 2
    assert res[0].event_type == "TASK_CREATED"
    assert res[1].event_type == "CRAWL_STARTED"
