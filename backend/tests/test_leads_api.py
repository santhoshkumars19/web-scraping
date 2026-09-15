"""
tests/test_leads_api.py

Comprehensive test suite for Backend Step 11:
Leads REST API layer (Endpoints, Queries, Filtering, Sorting, Pagination, Provenance).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token
from app.db.base import Base
from app.db.database import get_db
from app.main import app as fastapi_app
from app.models.contact import Contact
from app.models.email_address import EmailAddress
from app.models.extracted_field import ExtractedField
from app.models.lead import Lead
from app.models.lead_verification import LeadVerification
from app.models.organization import Organization, task_organizations
from app.models.phone_number import PhoneNumber
from app.models.scraping_task import ScrapingTask
from app.models.social_link import SocialLink
from app.models.source_page import SourcePage
from app.models.user import User
from app.models.website import Website

DEMO_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture()
async def leads_client():
    """Async HTTPX client wired to an in-memory SQLite DB with pre-seeded lead data."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    seeded_ids = {}

    async with session_factory() as session:
        # Seed demo user
        demo_user = User(
            id=DEMO_USER_ID,
            name="Demo Scout",
            email="demo@leadscout.app",
            password_hash="$2b$12$demo_placeholder_hash",
            role="USER",
            is_active=True,
        )
        session.add(demo_user)
        await session.flush()

        # Task 1: Schools in Puducherry
        t1 = ScrapingTask(
            id=uuid.uuid4(),
            task_id="TASK-000001",
            user_id=DEMO_USER_ID,
            location="Puducherry",
            keyword="CBSE Schools",
            status="COMPLETED",
            progress=100,
            results_discovered=2,
            selected_fields=["name", "phone", "email", "website", "address"],
        )
        # Task 2: Hospitals in Chennai
        t2 = ScrapingTask(
            id=uuid.uuid4(),
            task_id="TASK-000002",
            user_id=DEMO_USER_ID,
            location="Chennai",
            keyword="Hospitals",
            status="COMPLETED",
            progress=100,
            results_discovered=1,
            selected_fields=["name", "phone", "email"],
        )
        # Task 3: Empty task
        t3 = ScrapingTask(
            id=uuid.uuid4(),
            task_id="TASK-000003",
            user_id=DEMO_USER_ID,
            location="Madurai",
            keyword="Hotels",
            status="COMPLETED",
            progress=100,
            results_discovered=0,
            selected_fields=["name"],
        )
        session.add_all([t1, t2, t3])
        await session.flush()

        # Org 1: St. Patrick
        org1 = Organization(
            id=uuid.uuid4(),
            name="St. Patrick Matriculation Higher Secondary School",
            category="Matriculation School",
            address="100 Saram Road",
            city="Puducherry",
            state="Puducherry",
            pincode="605001",
        )
        # Org 2: Petit Seminaire
        org2 = Organization(
            id=uuid.uuid4(),
            name="Petit Seminaire Higher Secondary School",
            category="Higher Secondary School",
            address="Rue Dumas",
            city="Puducherry",
            state="Puducherry",
            pincode="605002",
        )
        # Org 3: Apollo Hospital
        org3 = Organization(
            id=uuid.uuid4(),
            name="Apollo Specialty Hospital",
            category="Multi-Specialty Hospital",
            address="21 Greams Lane",
            city="Chennai",
            state="Tamil Nadu",
            pincode="600006",
        )
        session.add_all([org1, org2, org3])
        await session.flush()

        # Link to tasks
        await session.execute(
            task_organizations.insert().values(
                [
                    {"task_id": t1.id, "organization_id": org1.id},
                    {"task_id": t1.id, "organization_id": org2.id},
                    {"task_id": t2.id, "organization_id": org3.id},
                ]
            )
        )

        # Leads
        lead1 = Lead(
            id=uuid.uuid4(),
            task_id=t1.id,
            organization_id=org1.id,
            status="ACTIVE",
            verification_status="HIGH",
            created_at=datetime(2026, 3, 12, 10, 0, 0, tzinfo=timezone.utc),
        )
        lead2 = Lead(
            id=uuid.uuid4(),
            task_id=t1.id,
            organization_id=org2.id,
            status="ACTIVE",
            verification_status="MEDIUM",
            created_at=datetime(2026, 3, 12, 11, 0, 0, tzinfo=timezone.utc),
        )
        lead3 = Lead(
            id=uuid.uuid4(),
            task_id=t2.id,
            organization_id=org3.id,
            status="ACTIVE",
            verification_status="LOW",
            created_at=datetime(2026, 3, 12, 12, 0, 0, tzinfo=timezone.utc),
        )
        session.add_all([lead1, lead2, lead3])
        await session.flush()

        # Org 1 children
        w1 = Website(
            organization_id=org1.id,
            url="https://stpatricks.edu",
            normalized_url="https://stpatricks.edu",
            domain="stpatricks.edu",
            is_official=True,
        )
        p1 = PhoneNumber(
            organization_id=org1.id,
            phone_number="+91 413 2244668",
            normalized_phone="+914132244668",
            phone_type="MAIN",
            is_primary=True,
        )
        p1_alt = PhoneNumber(
            organization_id=org1.id,
            phone_number="+91 98765 43210",
            normalized_phone="+919876543210",
            phone_type="WHATSAPP",
            is_whatsapp=True,
            is_primary=False,
        )
        e1 = EmailAddress(
            organization_id=org1.id,
            email="office@stpatricks.edu",
            normalized_email="office@stpatricks.edu",
            email_type="GENERAL",
            is_primary=True,
        )
        c1 = Contact(
            organization_id=org1.id,
            name="Fr. John Britto",
            designation="Principal",
        )
        soc1 = SocialLink(
            organization_id=org1.id,
            platform="FACEBOOK",
            url="https://facebook.com/stpatricks",
            normalized_url="https://facebook.com/stpatricks",
            is_official=True,
        )
        sp1 = SourcePage(
            organization_id=org1.id,
            website_id=w1.id,
            task_id=t1.id,
            url="https://stpatricks.edu/contact",
            normalized_url="https://stpatricks.edu/contact",
            page_type="CONTACT",
            page_title="Contact St. Patrick School",
            http_status=200,
        )
        ver1 = LeadVerification(
            organization_id=org1.id,
            lead_id=lead1.id,
            status="HIGH",
            score=88,
            fields_found=7,
            total_fields=8,
            completeness_percentage=87.5,
            source_quality_score=90.0,
            consistency_score=95.0,
            verification_reasons={"phone": "Valid format"},
            source_quality_details={"domain": "official"},
            verified_at=datetime(2026, 3, 12, 10, 5, 0, tzinfo=timezone.utc),
        )
        session.add_all([w1, p1, p1_alt, e1, c1, soc1, sp1, ver1])
        await session.flush()

        ef1 = ExtractedField(
            organization_id=org1.id,
            source_page_id=sp1.id,
            field_name="phone",
            field_value="+91 413 2244668",
            normalized_value="+914132244668",
        )
        session.add(ef1)

        # Org 2 children: phone only, NO email, NO whatsapp
        w2 = Website(
            organization_id=org2.id,
            url="https://petitseminaire.edu",
            normalized_url="https://petitseminaire.edu",
            domain="petitseminaire.edu",
            is_official=True,
        )
        p2 = PhoneNumber(
            organization_id=org2.id,
            phone_number="+91 413 2334455",
            normalized_phone="+914132334455",
            phone_type="MAIN",
            is_primary=True,
        )
        c2 = Contact(
            organization_id=org2.id,
            name="Rev. Fr. Pascal",
            designation="Headmaster",
        )
        ver2 = LeadVerification(
            organization_id=org2.id,
            lead_id=lead2.id,
            status="MEDIUM",
            score=65,
            fields_found=4,
            total_fields=8,
            completeness_percentage=50.0,
            source_quality_score=80.0,
            consistency_score=85.0,
            verified_at=datetime(2026, 3, 12, 11, 5, 0, tzinfo=timezone.utc),
        )
        session.add_all([w2, p2, c2, ver2])

        # Org 3 children: phone + email
        w3 = Website(
            organization_id=org3.id,
            url="https://apollohospitals.example",
            normalized_url="https://apollohospitals.example",
            domain="apollohospitals.example",
            is_official=True,
        )
        p3 = PhoneNumber(
            organization_id=org3.id,
            phone_number="+91 44 28290200",
            normalized_phone="+914428290200",
            phone_type="OFFICE",
            is_primary=True,
        )
        e3 = EmailAddress(
            organization_id=org3.id,
            email="contact@apollohospitals.example",
            normalized_email="contact@apollohospitals.example",
            email_type="GENERAL",
            is_primary=True,
        )
        ver3 = LeadVerification(
            organization_id=org3.id,
            lead_id=lead3.id,
            status="LOW",
            score=45,
            fields_found=3,
            total_fields=8,
            completeness_percentage=37.5,
            source_quality_score=50.0,
            consistency_score=60.0,
            verified_at=datetime(2026, 3, 12, 12, 5, 0, tzinfo=timezone.utc),
        )
        session.add_all([w3, p3, e3, ver3])

        await session.commit()

        seeded_ids["t1_id"] = t1.task_id
        seeded_ids["t2_id"] = t2.task_id
        seeded_ids["t3_id"] = t3.task_id
        seeded_ids["lead1_id"] = str(lead1.id)
        seeded_ids["lead2_id"] = str(lead2.id)
        seeded_ids["lead3_id"] = str(lead3.id)

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    fastapi_app.dependency_overrides[get_db] = override_get_db

    token = create_access_token(DEMO_USER_ID)
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://testserver",
        headers={"Authorization": f"Bearer {token}"},
    ) as ac:
        ac.seeded = seeded_ids  # type: ignore[attr-defined]
        yield ac

    fastapi_app.dependency_overrides.clear()
    await engine.dispose()


# ── 1. Global Leads Query & Pagination Tests ─────────────────────────────────

@pytest.mark.asyncio
async def test_list_leads_returns_all(leads_client: AsyncClient) -> None:
    """GET /api/leads returns all user leads with proper pagination metadata."""
    res = await leads_client.get("/api/leads")
    assert res.status_code == 200

    data = res.json()
    assert data["success"] is True
    assert len(data["data"]) == 3
    assert data["pagination"]["total"] == 3
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["limit"] == 20
    assert data["pagination"]["total_pages"] == 1
    assert data["pagination"]["has_next"] is False
    assert data["pagination"]["has_prev"] is False


@pytest.mark.asyncio
async def test_list_leads_pagination_chunks(leads_client: AsyncClient) -> None:
    """Page and limit parameters properly paginate records at the database level."""
    # Page 1, limit 2 -> returns 2 items
    res1 = await leads_client.get("/api/leads?page=1&limit=2")
    assert res1.status_code == 200
    p1 = res1.json()["pagination"]
    assert len(res1.json()["data"]) == 2
    assert p1["total"] == 3
    assert p1["total_pages"] == 2
    assert p1["has_next"] is True
    assert p1["has_prev"] is False

    # Page 2, limit 2 -> returns remaining 1 item
    res2 = await leads_client.get("/api/leads?page=2&limit=2")
    assert res2.status_code == 200
    p2 = res2.json()["pagination"]
    assert len(res2.json()["data"]) == 1
    assert p2["total"] == 3
    assert p2["total_pages"] == 2
    assert p2["has_next"] is False
    assert p2["has_prev"] is True


# ── 2. Multi-Field Search Tests ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_search_by_organization_name(leads_client: AsyncClient) -> None:
    """Search matches organization name case-insensitively."""
    res = await leads_client.get("/api/leads?search=apollo")
    assert res.status_code == 200
    items = res.json()["data"]
    assert len(items) == 1
    assert items[0]["organization"]["name"] == "Apollo Specialty Hospital"


@pytest.mark.asyncio
async def test_search_by_phone_number(leads_client: AsyncClient) -> None:
    """Search matches phone number or normalized phone."""
    res = await leads_client.get("/api/leads?search=98765")
    assert res.status_code == 200
    items = res.json()["data"]
    assert len(items) == 1
    assert items[0]["organization"]["name"] == "St. Patrick Matriculation Higher Secondary School"


@pytest.mark.asyncio
async def test_search_by_email(leads_client: AsyncClient) -> None:
    """Search matches email address."""
    res = await leads_client.get("/api/leads?search=office@stpatricks")
    assert res.status_code == 200
    items = res.json()["data"]
    assert len(items) == 1
    assert items[0]["organization"]["name"] == "St. Patrick Matriculation Higher Secondary School"


@pytest.mark.asyncio
async def test_search_by_contact_person(leads_client: AsyncClient) -> None:
    """Search matches contact person name."""
    res = await leads_client.get("/api/leads?search=Pascal")
    assert res.status_code == 200
    items = res.json()["data"]
    assert len(items) == 1
    assert items[0]["organization"]["name"] == "Petit Seminaire Higher Secondary School"


@pytest.mark.asyncio
async def test_search_no_match(leads_client: AsyncClient) -> None:
    """Search with non-existent term returns empty list with total=0."""
    res = await leads_client.get("/api/leads?search=NonExistentQueryXYZ123")
    assert res.status_code == 200
    assert len(res.json()["data"]) == 0
    assert res.json()["pagination"]["total"] == 0


# ── 3. Filters & Facet Tests ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_filter_by_verification_tier(leads_client: AsyncClient) -> None:
    """Filter by HIGH, MEDIUM, LOW verification tiers."""
    res_high = await leads_client.get("/api/leads?verification=HIGH")
    assert res_high.status_code == 200
    assert len(res_high.json()["data"]) == 1
    assert res_high.json()["data"][0]["verification"]["status"] == "HIGH"

    res_med = await leads_client.get("/api/leads?verification=MEDIUM")
    assert res_med.status_code == 200
    assert len(res_med.json()["data"]) == 1
    assert res_med.json()["data"][0]["verification"]["status"] == "MEDIUM"


@pytest.mark.asyncio
async def test_filter_by_category_and_location(leads_client: AsyncClient) -> None:
    """Filter by category substring and location."""
    res_cat = await leads_client.get("/api/leads?category=Hospital")
    assert res_cat.status_code == 200
    assert len(res_cat.json()["data"]) == 1
    assert res_cat.json()["data"][0]["organization"]["name"] == "Apollo Specialty Hospital"

    res_loc = await leads_client.get("/api/leads?location=Chennai")
    assert res_loc.status_code == 200
    assert len(res_loc.json()["data"]) == 1
    assert res_loc.json()["data"][0]["organization"]["city"] == "Chennai"


@pytest.mark.asyncio
async def test_filter_by_data_availability(leads_client: AsyncClient) -> None:
    """Availability flags: has_email, has_whatsapp, has_social."""
    # has_whatsapp=true -> only St. Patrick
    res_wa = await leads_client.get("/api/leads?has_whatsapp=true")
    assert res_wa.status_code == 200
    assert len(res_wa.json()["data"]) == 1
    assert res_wa.json()["data"][0]["whatsapp"] is not None

    # has_email=false -> only Petit Seminaire
    res_no_email = await leads_client.get("/api/leads?has_email=false")
    assert res_no_email.status_code == 200
    assert len(res_no_email.json()["data"]) == 1
    assert res_no_email.json()["data"][0]["organization"]["name"] == "Petit Seminaire Higher Secondary School"

    # has_social=true -> only St. Patrick
    res_soc = await leads_client.get("/api/leads?has_social=true")
    assert res_soc.status_code == 200
    assert len(res_soc.json()["data"]) == 1


# ── 4. Sorting Tests ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_sort_by_organization_name(leads_client: AsyncClient) -> None:
    """Sorting by organization name in asc and desc directions."""
    res_asc = await leads_client.get("/api/leads?sort_by=organization&sort_order=asc")
    assert res_asc.status_code == 200
    names_asc = [item["organization"]["name"] for item in res_asc.json()["data"]]
    assert names_asc == [
        "Apollo Specialty Hospital",
        "Petit Seminaire Higher Secondary School",
        "St. Patrick Matriculation Higher Secondary School",
    ]

    res_desc = await leads_client.get("/api/leads?sort_by=organization&sort_order=desc")
    assert res_desc.status_code == 200
    names_desc = [item["organization"]["name"] for item in res_desc.json()["data"]]
    assert names_desc == [
        "St. Patrick Matriculation Higher Secondary School",
        "Petit Seminaire Higher Secondary School",
        "Apollo Specialty Hospital",
    ]


# ── 5. Task Scoped Leads Endpoint Tests ──────────────────────────────────────

@pytest.mark.asyncio
async def test_get_task_leads_success(leads_client: AsyncClient) -> None:
    """GET /api/tasks/{task_id}/leads returns only leads for that task."""
    t1_id = leads_client.seeded["t1_id"]  # type: ignore[attr-defined]
    res = await leads_client.get(f"/api/tasks/{t1_id}/leads")
    assert res.status_code == 200
    items = res.json()["data"]
    assert len(items) == 2
    assert all(item["task_id"] == t1_id for item in items)


@pytest.mark.asyncio
async def test_get_task_leads_empty(leads_client: AsyncClient) -> None:
    """Existing task with zero leads returns HTTP 200 with empty list."""
    t3_id = leads_client.seeded["t3_id"]  # type: ignore[attr-defined]
    res = await leads_client.get(f"/api/tasks/{t3_id}/leads")
    assert res.status_code == 200
    assert res.json()["data"] == []
    assert res.json()["pagination"]["total"] == 0


@pytest.mark.asyncio
async def test_get_task_leads_not_found(leads_client: AsyncClient) -> None:
    """Non-existent task returns HTTP 404 with TASK_NOT_FOUND error code."""
    res = await leads_client.get("/api/tasks/TASK-NONEXISTENT/leads")
    assert res.status_code == 404
    body = res.json()
    assert body["success"] is False
    assert body["error"]["code"] == "TASK_NOT_FOUND"


# ── 6. Single Lead Profile & Provenance Tests ────────────────────────────────

@pytest.mark.asyncio
async def test_get_lead_detail_full_provenance(leads_client: AsyncClient) -> None:
    """GET /api/leads/{lead_id} returns complete lead profile and provenance records."""
    lead1_id = leads_client.seeded["lead1_id"]  # type: ignore[attr-defined]
    res = await leads_client.get(f"/api/leads/{lead1_id}")
    assert res.status_code == 200

    body = res.json()
    assert body["success"] is True
    lead = body["data"]

    # Basic info
    assert lead["id"] == lead1_id
    assert lead["organization"]["name"] == "St. Patrick Matriculation Higher Secondary School"

    # Task summary
    assert lead["task"] is not None
    assert lead["task"]["task_id"] == "TASK-000001"
    assert lead["task"]["keyword"] == "CBSE Schools"

    # Related collections
    assert len(lead["websites"]) == 1
    assert lead["websites"][0]["url"] == "https://stpatricks.edu"
    assert len(lead["phones"]) == 2
    assert len(lead["emails"]) == 1
    assert lead["emails"][0]["email"] == "office@stpatricks.edu"
    assert len(lead["contacts"]) == 1
    assert lead["contacts"][0]["name"] == "Fr. John Britto"
    assert lead["contacts"][0]["designation"] == "Principal"
    assert len(lead["social_links"]) == 1
    assert lead["social_links"][0]["platform"] == "FACEBOOK"

    # Field-level source provenance
    assert len(lead["sources"]) >= 1
    assert lead["sources"][0]["source_url"] == "https://stpatricks.edu/contact"
    assert lead["sources"][0]["page_title"] == "Contact St. Patrick School"

    # Verification breakdown
    assert lead["verification"]["status"] == "HIGH"
    assert lead["verification"]["score"] == 88
    assert lead["verification"]["completeness_percentage"] == 87.5
    assert lead["verification"]["source_quality_score"] == 90.0


@pytest.mark.asyncio
async def test_get_lead_detail_not_found(leads_client: AsyncClient) -> None:
    """Non-existent lead returns HTTP 404 with LEAD_NOT_FOUND error code."""
    fake_id = str(uuid.uuid4())
    res = await leads_client.get(f"/api/leads/{fake_id}")
    assert res.status_code == 404
    body = res.json()
    assert body["success"] is False
    assert body["error"]["code"] == "LEAD_NOT_FOUND"


# ── 7. Validation & Error Handling Tests ─────────────────────────────────────

@pytest.mark.asyncio
async def test_invalid_sort_field_rejected(leads_client: AsyncClient) -> None:
    """Invalid sort field triggers HTTP 422 validation error."""
    res = await leads_client.get("/api/leads?sort_by=non_existent_column")
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_invalid_verification_filter_rejected(leads_client: AsyncClient) -> None:
    """Invalid verification status filter triggers HTTP 422 validation error."""
    res = await leads_client.get("/api/leads?verification=SUPER_HIGH")
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_negative_page_rejected(leads_client: AsyncClient) -> None:
    """Negative page number triggers HTTP 422 validation error."""
    res = await leads_client.get("/api/leads?page=0")
    assert res.status_code == 422


# ── 8. Strict N+1 Query Prevention Verification ──────────────────────────────

@pytest.mark.asyncio
async def test_n_plus_one_query_prevention() -> None:
    """Verify that listing leads eagerly loads all relationships in constant batch queries."""
    from sqlalchemy import event
    from app.repositories.lead_repository import LeadRepository

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        t = ScrapingTask(
            id=uuid.uuid4(),
            task_id="TASK-NPLUSONE",
            user_id=DEMO_USER_ID,
            location="City",
            keyword="Test",
            status="COMPLETED",
        )
        session.add(t)
        await session.flush()

        for i in range(5):
            org = Organization(id=uuid.uuid4(), name=f"Org {i}", city="City")
            session.add(org)
            await session.flush()
            lead = Lead(
                id=uuid.uuid4(),
                task_id=t.id,
                organization_id=org.id,
                status="ACTIVE",
                verification_status="HIGH",
            )
            session.add(lead)
            w = Website(
                organization_id=org.id,
                url=f"https://org{i}.com",
                normalized_url=f"https://org{i}.com",
            )
            p = PhoneNumber(
                organization_id=org.id,
                phone_number=f"+91 99999 0000{i}",
                normalized_phone=f"+91999990000{i}",
            )
            e = EmailAddress(
                organization_id=org.id,
                email=f"info@org{i}.com",
                normalized_email=f"info@org{i}.com",
            )
            c = Contact(organization_id=org.id, name=f"Person {i}")
            v = LeadVerification(
                organization_id=org.id,
                lead_id=lead.id,
                status="HIGH",
                score=80,
            )
            session.add_all([w, p, e, c, v])
        await session.commit()

    executed_queries = []

    def count_queries(conn, cursor, statement, parameters, context, executemany):
        executed_queries.append(statement)

    event.listen(engine.sync_engine, "before_cursor_execute", count_queries)

    async with session_factory() as query_session:
        repo = LeadRepository(query_session)
        leads, total = await repo.list_leads(task_id="TASK-NPLUSONE", limit=10)
        assert len(leads) == 5
        # Access all relations to ensure lazy loading doesn't fire individual per-row queries
        for l in leads:
            assert l.organization.name is not None
            assert len(l.organization.websites) == 1
            assert len(l.organization.phone_numbers) == 1
            assert len(l.organization.email_addresses) == 1
            assert len(l.organization.contacts) == 1
            assert l.verification is not None

    event.remove(engine.sync_engine, "before_cursor_execute", count_queries)
    await engine.dispose()

    # Query count must remain constant O(1) with respect to N rows:
    # 1 count query + 1 root Lead query + 1 query per batch relationship with `IN (...)`.
    # If N+1 were present, 5 leads would emit 30+ queries, growing linearly O(N).
    # Here all 19 queries are bulk IN (?, ?, ...) lookups, independent of N.
    query_count = len(executed_queries)
    assert query_count <= 20, f"Executed {query_count} queries:\n" + "\n".join(executed_queries)

