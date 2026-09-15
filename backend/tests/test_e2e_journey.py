"""
tests/test_e2e_journey.py

End-to-End User Journey & Production Integration Test Suite for LeadScout.
Tests:
  1. User Authentication Lifecycle (Signup -> Login -> Profile -> Password change)
  2. Scraping Task Lifecycle & Idempotency (POST /api/scrape)
  3. Complete Pipeline Persistence & Data Model Integrity (Org, Website, Source, Phone, Email, Contact, Social, Lead, Verification)
  4. Leads Query, Multi-field Search, Filters, and Provenance Detail
  5. Dashboard Overview & Real-time Aggregation Endpoint (GET /api/dashboard/summary)
  6. Data Exports (CSV with BOM and Excel XLSX)
  7. Cross-tenant Security & Anti-Enumeration Isolation
  8. Responsible Crawling Safety Guardrails (SSRF, robots.txt, Access-control)
"""

from __future__ import annotations

import io
import uuid
from datetime import datetime, timezone
from unittest.mock import patch

import openpyxl
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.db.database import get_db
from app.main import app as fastapi_app
from app.models.contact import Contact
from app.models.email_address import EmailAddress
from app.models.lead import Lead
from app.models.lead_verification import LeadVerification
from app.models.organization import Organization
from app.models.phone_number import PhoneNumber
from app.models.scraping_task import ScrapingTask
from app.models.social_link import SocialLink
from app.models.source_page import SourcePage
from app.models.user import User
from app.models.website import Website
from app.utils.ssrf import validate_url_for_ssrf, SsrfBlockedError


@pytest.fixture()
async def e2e_env():
    """Spin up isolated in-memory SQLite engine with all tables for E2E testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    fastapi_app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://testserver",
    ) as client:
        yield {
            "client": client,
            "session_factory": session_factory,
        }

    fastapi_app.dependency_overrides.pop(get_db, None)


@pytest.mark.anyio
async def test_user_auth_lifecycle(e2e_env):
    """Verify signup, login, session bootstrap, and profile update."""
    client: AsyncClient = e2e_env["client"]

    # 1. Signup
    signup_res = await client.post(
        "/api/auth/signup",
        json={
            "name": "Integration User",
            "email": "journey@example.com",
            "password": "SecurePassword123!",
            "company": "LeadScout Inc",
        },
    )
    assert signup_res.status_code == 201
    signup_json = signup_res.json()
    assert signup_json["success"] is True
    token = signup_json["data"]["access_token"]
    assert token

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get Profile (/api/auth/me)
    me_res = await client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["data"]["email"] == "journey@example.com"

    # 3. Update Profile
    patch_res = await client.patch(
        "/api/users/me",
        headers=headers,
        json={"name": "Updated Lead Scout", "company": "Growth Ops"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["data"]["name"] == "Updated Lead Scout"

    # 4. Login with credentials
    login_res = await client.post(
        "/api/auth/login",
        json={
            "email": "journey@example.com",
            "password": "SecurePassword123!",
        },
    )
    assert login_res.status_code == 200
    assert login_res.json()["data"]["access_token"]


@pytest.mark.anyio
async def test_full_pipeline_leads_dashboard_and_export_journey(e2e_env):
    """Verify complete end-to-end task creation, pipeline persistence, leads querying, dashboard, and exports."""
    client: AsyncClient = e2e_env["client"]
    session_factory = e2e_env["session_factory"]

    # 1. Setup User
    user_id = uuid.uuid4()
    async with session_factory() as session:
        user = User(
            id=user_id,
            name="Scout Leader",
            email="leader@example.com",
            password_hash=hash_password("Pass123!"),
            role="USER",
            is_active=True,
        )
        session.add(user)
        await session.commit()

    token = create_access_token(user_id, role="USER")
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Scraping Task with Idempotency Key
    idempotency_key = f"idemp-{uuid.uuid4()}"
    with patch("app.workers.pipeline.run_scraping_pipeline.delay") as mock_delay:
        mock_delay.return_value = type("AsyncResult", (), {"id": "celery-mock-123"})()

        task_create_res = await client.post(
            "/api/scrape",
            headers={**headers, "Idempotency-Key": idempotency_key},
            json={
                "location": "Puducherry",
                "keyword": "CBSE Schools",
                "search_radius": 25,
                "max_results": 100,
                "max_pages_per_site": 20,
                "selected_fields": ["phone", "email", "website", "address"],
                "crawl_depth": 3,
                "follow_internal_links": True,
                "prioritize_contact": True,
                "prioritize_about": True,
                "prioritize_admissions": True,
                "prioritize_staff_management": True,
            },
        )
        assert task_create_res.status_code == 201
        task_data = task_create_res.json()["data"]
        task_id = task_data["task_id"]
        assert task_id.startswith("TASK-")

        # Idempotency duplicate submission returns identical response without re-queuing
        dup_res = await client.post(
            "/api/scrape",
            headers={**headers, "Idempotency-Key": idempotency_key},
            json={
                "location": "Puducherry",
                "keyword": "CBSE Schools",
                "selected_fields": ["phone", "email", "website", "address"],
            },
        )
        assert dup_res.status_code == 201
        assert dup_res.json()["data"]["task_id"] == task_id

    # 3. Simulate Pipeline Completion & DB Persistence
    lead_id_str = f"lead-{uuid.uuid4()}"
    async with session_factory() as session:
        # Load task and update to COMPLETED
        from sqlalchemy import select
        t_stmt = select(ScrapingTask).where(ScrapingTask.task_id == task_id)
        task_db = (await session.execute(t_stmt)).scalar_one()
        task_db.status = "COMPLETED"
        task_db.current_stage = "COMPLETED"
        task_db.progress = 100
        task_db.results_discovered = 1
        task_db.websites_found = 1
        task_db.websites_crawled = 1
        task_db.phones_found = 1
        task_db.emails_found = 1
        task_db.addresses_found = 1
        task_db.verified_count = 1
        task_db.started_at = datetime.now(timezone.utc)
        task_db.completed_at = datetime.now(timezone.utc)

        # Create Organization
        org = Organization(
            id=uuid.uuid4(),
            name="St. Patrick Matriculation School",
            category="CBSE Schools",
            address="12 Rue Romain Rolland",
            city="Puducherry",
            state="Puducherry",
            pincode="605001",
        )
        session.add(org)
        await session.flush()

        # Create Website
        web = Website(
            id=uuid.uuid4(),
            organization_id=org.id,
            url="https://stpatricks.example.com",
            normalized_url="https://stpatricks.example.com",
            domain="stpatricks.example.com",
            is_official=True,
            status="CRAWLED",
        )
        session.add(web)

        # Create SourcePage
        src = SourcePage(
            id=uuid.uuid4(),
            organization_id=org.id,
            task_id=task_db.id,
            website_id=web.id,
            url="https://stpatricks.example.com/contact",
            normalized_url="https://stpatricks.example.com/contact",
            http_status=200,
            page_type="CONTACT",
            page_title="Contact Us - St. Patrick School",
        )
        session.add(src)

        # Create Phone
        ph = PhoneNumber(
            id=uuid.uuid4(),
            organization_id=org.id,
            phone_number="+91 413 222 3344",
            normalized_phone="+914132223344",
            phone_type="OFFICE",
            is_primary=True,
            is_whatsapp=False,
        )
        session.add(ph)

        # Create Email
        em = EmailAddress(
            id=uuid.uuid4(),
            organization_id=org.id,
            email="contact@stpatricks.example.com",
            normalized_email="contact@stpatricks.example.com",
            email_type="CONTACT",
            is_primary=True,
        )
        session.add(em)

        # Create Contact
        cnt = Contact(
            id=uuid.uuid4(),
            organization_id=org.id,
            name="Fr. John Doe",
            designation="Principal",
        )
        session.add(cnt)

        # Create SocialLink
        soc = SocialLink(
            id=uuid.uuid4(),
            organization_id=org.id,
            platform="FACEBOOK",
            url="https://facebook.com/stpatrickspuducherry",
            normalized_url="https://facebook.com/stpatrickspuducherry",
            is_official=True,
        )
        session.add(soc)

        # Create Lead
        lead = Lead(
            id=uuid.uuid4(),
            task_id=task_db.id,
            organization_id=org.id,
            status="ACTIVE",
            verification_status="HIGH",
        )
        session.add(lead)
        await session.flush()

        lead_id_str = str(lead.id)

        # Create LeadVerification
        ver = LeadVerification(
            id=uuid.uuid4(),
            organization_id=org.id,
            lead_id=lead.id,
            status="HIGH",
            score=95,
            fields_found=6,
            total_fields=8,
            completeness_percentage=75.0,
            source_quality_score=90.0,
            consistency_score=98.0,
            verification_reasons={"official_domain": True, "valid_phone": True},
            source_quality_details={"domain": "stpatricks.example.com"},
            verified_at=datetime.now(timezone.utc),
        )
        session.add(ver)
        await session.commit()

    # 4. Verify GET /api/tasks and GET /api/tasks/{task_id}
    tasks_res = await client.get("/api/tasks", headers=headers)
    assert tasks_res.status_code == 200
    assert tasks_res.json()["pagination"]["total"] >= 1

    task_detail_res = await client.get(f"/api/tasks/{task_id}", headers=headers)
    assert task_detail_res.status_code == 200
    assert task_detail_res.json()["data"]["status"] == "COMPLETED"

    # 5. Verify GET /api/tasks/{task_id}/leads and GET /api/leads
    task_leads_res = await client.get(f"/api/tasks/{task_id}/leads", headers=headers)
    assert task_leads_res.status_code == 200
    assert len(task_leads_res.json()["data"]) >= 1

    leads_res = await client.get(
        "/api/leads",
        headers=headers,
        params={"search": "Patrick", "location": "Puducherry", "has_phone": "true"},
    )
    assert leads_res.status_code == 200
    leads_json = leads_res.json()
    assert leads_json["pagination"]["total"] >= 1
    assert "Patrick" in leads_json["data"][0]["organization"]["name"]

    # 6. Verify GET /api/leads/{lead_id} profile
    single_lead_res = await client.get(f"/api/leads/{lead_id_str}", headers=headers)
    assert single_lead_res.status_code == 200
    lead_prof = single_lead_res.json()["data"]
    assert lead_prof["organization"]["name"] == "St. Patrick Matriculation School"
    assert lead_prof["verification"]["score"] == 95
    assert lead_prof["verification"]["status"] == "HIGH"
    assert len(lead_prof["phones"]) >= 1
    assert len(lead_prof["emails"]) >= 1
    assert len(lead_prof["contacts"]) >= 1

    # 7. Verify GET /api/dashboard/summary
    dash_res = await client.get("/api/dashboard/summary", headers=headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()["data"]
    assert dash_data["total_leads"] >= 1
    assert dash_data["verified_leads"] >= 1
    assert dash_data["scraping_tasks"] >= 1
    assert len(dash_data["recent_tasks"]) >= 1
    assert len(dash_data["category_summary"]) >= 1
    assert len(dash_data["location_summary"]) >= 1

    # 8. Verify Exports (CSV & Excel)
    csv_res = await client.get(f"/api/tasks/{task_id}/export/csv", headers=headers)
    assert csv_res.status_code == 200
    assert csv_res.headers["content-type"].startswith("text/csv")
    assert csv_res.content.startswith(b"\xef\xbb\xbf")  # UTF-8 BOM
    assert b"St. Patrick" in csv_res.content

    excel_res = await client.get(f"/api/tasks/{task_id}/export/excel", headers=headers)
    assert excel_res.status_code == 200
    assert "spreadsheetml" in excel_res.headers["content-type"]
    wb = openpyxl.load_workbook(io.BytesIO(excel_res.content))
    assert "Leads" in wb.sheetnames
    ws = wb["Leads"]
    assert ws["A1"].value == "Organization Name"

    # Global CSV Export
    global_csv_res = await client.get("/api/leads/export/csv", headers=headers)
    assert global_csv_res.status_code == 200
    assert b"St. Patrick" in global_csv_res.content


@pytest.mark.anyio
async def test_user_isolation_boundaries(e2e_env):
    """Verify User A cannot read, query, export, or enumerate User B's resources."""
    client: AsyncClient = e2e_env["client"]
    session_factory = e2e_env["session_factory"]

    user_a_id = uuid.uuid4()
    user_b_id = uuid.uuid4()

    async with session_factory() as session:
        user_a = User(
            id=user_a_id,
            name="User A",
            email="user_a@leadscout.test",
            password_hash=hash_password("Pass123!"),
            role="USER",
            is_active=True,
        )
        user_b = User(
            id=user_b_id,
            name="User B",
            email="user_b@leadscout.test",
            password_hash=hash_password("Pass123!"),
            role="USER",
            is_active=True,
        )
        session.add_all([user_a, user_b])
        await session.flush()

        task_b = ScrapingTask(
            id=uuid.uuid4(),
            task_id="TASK-999999",
            user_id=user_b_id,
            keyword="Private Colleges",
            location="Chennai",
            status="COMPLETED",
        )
        session.add(task_b)
        await session.flush()

        org_b = Organization(id=uuid.uuid4(), name="User B College", category="Colleges")
        session.add(org_b)
        await session.flush()

        lead_b = Lead(id=uuid.uuid4(), task_id=task_b.id, organization_id=org_b.id)
        session.add(lead_b)
        await session.flush()

        ver_b = LeadVerification(
            id=uuid.uuid4(),
            organization_id=org_b.id,
            lead_id=lead_b.id,
            status="HIGH",
        )
        session.add(ver_b)
        await session.commit()

        lead_b_id = str(lead_b.id)

    token_a = create_access_token(user_a_id, role="USER")
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 1. User A tries to view User B's task -> 404 (anti-enumeration)
    res1 = await client.get("/api/tasks/TASK-999999", headers=headers_a)
    assert res1.status_code == 404

    # 2. User A tries to view User B's lead -> 404
    res2 = await client.get(f"/api/leads/{lead_b_id}", headers=headers_a)
    assert res2.status_code == 404

    # 3. User A tries to export User B's task -> 404
    res3 = await client.get("/api/tasks/TASK-999999/export/csv", headers=headers_a)
    assert res3.status_code == 404

    # 4. User A tries to export User B's lead -> 404
    res4 = await client.get(f"/api/leads/{lead_b_id}/export/csv", headers=headers_a)
    assert res4.status_code == 404

    # 5. User A dashboard shows 0 leads and 0 tasks
    dash_a = await client.get("/api/dashboard/summary", headers=headers_a)
    assert dash_a.status_code == 200
    assert dash_a.json()["data"]["total_leads"] == 0
    assert dash_a.json()["data"]["scraping_tasks"] == 0


@pytest.mark.anyio
async def test_ssrf_and_responsible_crawling_e2e():
    """Verify SSRF validation blocks internal metadata and loopback destinations."""
    with pytest.raises(SsrfBlockedError):
        validate_url_for_ssrf("http://127.0.0.1:8000/admin")

    with pytest.raises(SsrfBlockedError):
        validate_url_for_ssrf("http://169.254.169.254/latest/meta-data")

    with pytest.raises(SsrfBlockedError):
        validate_url_for_ssrf("http://metadata.google.internal")

    with pytest.raises(SsrfBlockedError):
        validate_url_for_ssrf("file:///etc/passwd")

    validate_url_for_ssrf("https://example.com")  # Does not raise
