"""
tests/test_export.py

Comprehensive test suite for Backend Step 12:
Export APIs (CSV & Excel) covering:
- Task-scoped CSV and Excel exports
- Global filtered leads CSV and Excel exports
- Selected leads export (ids parameter)
- Single lead profile export
- Custom field selection (fields parameter) and alias mapping
- Invalid field validation (422 INVALID_EXPORT_FIELD)
- Text-safe phone formatting in Excel (@ and 's')
- UTF-8 BOM in CSV
- Freeze panes and autofilter in Excel
- Semicolon delimited contacts, emails, and source URLs
- Not found (404) and empty leads (404) errors
- Max export rows limit check (413 EXPORT_TOO_LARGE)
- Safe filename generation
"""

from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime, timezone
import pytest
from httpx import ASGITransport, AsyncClient
import openpyxl
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import settings
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
from app.services.export.filename import build_export_filename, sanitize_filename

DEMO_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture()
async def export_client():
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
            task_id="TASK-EXPORT-001",
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
            task_id="TASK-EXPORT-002",
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
            task_id="TASK-EXPORT-003",
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

        # Org 2 children
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
            phone_type="OFFICE",
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

        # Org 3 children
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


# ── 1. Task-Scoped Exports ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_export_task_csv(export_client: AsyncClient):
    """Test exporting all leads for a specific task as CSV."""
    task_id = export_client.seeded["t1_id"]
    res = await export_client.get(f"/api/tasks/{task_id}/export/csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert f'leadscout-task-{task_id}-' in res.headers["content-disposition"]
    assert res.headers["content-disposition"].endswith('.csv"')

    # Verify UTF-8 BOM
    raw_bytes = res.content
    assert raw_bytes.startswith(b"\xef\xbb\xbf")

    # Parse CSV content
    text = raw_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)

    assert len(rows) == 2
    org_names = {r["Organization Name"] for r in rows}
    assert "St. Patrick Matriculation Higher Secondary School" in org_names
    assert "Petit Seminaire Higher Secondary School" in org_names
    assert "Apollo Specialty Hospital" not in org_names

    # Check St. Patrick details
    pat = next(r for r in rows if "St. Patrick" in r["Organization Name"])
    assert pat["City"] == "Puducherry"
    assert pat["State"] == "Puducherry"
    assert pat["Pincode"] == "605001"
    assert pat["Phone"] == "+91 413 2244668"
    assert pat["Email"] == "office@stpatricks.edu"
    assert pat["Contact Person"] == "Fr. John Britto"
    assert pat["Designation"] == "Principal"
    assert pat["Verification"] == "HIGH"
    assert "https://stpatricks.edu/contact" in pat["Source URLs"]


@pytest.mark.asyncio
async def test_export_task_excel(export_client: AsyncClient):
    """Test exporting task leads as Excel (.xlsx)."""
    task_id = export_client.seeded["t1_id"]
    res = await export_client.get(f"/api/tasks/{task_id}/export/excel")
    assert res.status_code == 200
    assert "spreadsheetml.sheet" in res.headers["content-type"]
    assert f'leadscout-task-{task_id}-' in res.headers["content-disposition"]
    assert res.headers["content-disposition"].endswith('.xlsx"')

    wb = openpyxl.load_workbook(io.BytesIO(res.content))
    assert "Leads" in wb.sheetnames
    ws = wb["Leads"]

    # Verify header and row count
    headers = [cell.value for cell in ws[1]]
    assert "Organization Name" in headers
    assert "Phone" in headers
    assert "Email" in headers
    assert "Verification" in headers

    # 2 data rows + 1 header = 3 rows
    assert ws.max_row == 3

    # Freeze panes
    assert ws.freeze_panes == "A2"
    # Auto-filter
    assert ws.auto_filter.ref is not None


# ── 2. Global / Filtered Leads Export ────────────────────────────────────────

@pytest.mark.asyncio
async def test_export_all_leads_csv(export_client: AsyncClient):
    """Test global export of all leads without filters."""
    res = await export_client.get("/api/leads/export/csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert 'leadscout-leads-' in res.headers["content-disposition"]

    text = res.content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    assert len(rows) == 3


@pytest.mark.asyncio
async def test_export_filtered_leads_search(export_client: AsyncClient):
    """Test exporting leads with search term."""
    res = await export_client.get("/api/leads/export/csv?search=Apollo")
    assert res.status_code == 200
    text = res.content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["Organization Name"] == "Apollo Specialty Hospital"
    assert rows[0]["City"] == "Chennai"


@pytest.mark.asyncio
async def test_export_filtered_leads_verification(export_client: AsyncClient):
    """Test exporting leads filtered by verification status."""
    res = await export_client.get("/api/leads/export/csv?verification=HIGH")
    assert res.status_code == 200
    text = res.content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    assert len(rows) == 1
    assert "St. Patrick" in rows[0]["Organization Name"]


@pytest.mark.asyncio
async def test_export_filtered_leads_location(export_client: AsyncClient):
    """Test exporting leads filtered by location."""
    res = await export_client.get("/api/leads/export/excel?location=Puducherry")
    assert res.status_code == 200
    wb = openpyxl.load_workbook(io.BytesIO(res.content))
    ws = wb["Leads"]
    # Header + 2 Puducherry leads
    assert ws.max_row == 3


# ── 3. Selected Leads Export ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_export_selected_leads_csv(export_client: AsyncClient):
    """Test exporting specific lead IDs via ids parameter."""
    l1 = export_client.seeded["lead1_id"]
    l3 = export_client.seeded["lead3_id"]
    res = await export_client.get(f"/api/leads/export/csv?ids={l1},{l3}")
    assert res.status_code == 200
    text = res.content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    assert len(rows) == 2
    orgs = {r["Organization Name"] for r in rows}
    assert "St. Patrick Matriculation Higher Secondary School" in orgs
    assert "Apollo Specialty Hospital" in orgs
    assert "Petit Seminaire Higher Secondary School" not in orgs


@pytest.mark.asyncio
async def test_export_selected_leads_excel(export_client: AsyncClient):
    """Test exporting specific lead IDs via Excel."""
    l2 = export_client.seeded["lead2_id"]
    res = await export_client.get(f"/api/leads/export/excel?ids={l2}")
    assert res.status_code == 200
    wb = openpyxl.load_workbook(io.BytesIO(res.content))
    ws = wb["Leads"]
    assert ws.max_row == 2  # header + 1 lead


# ── 4. Single Lead Export ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_export_single_lead_csv(export_client: AsyncClient):
    """Test exporting a single lead profile as CSV."""
    l1 = export_client.seeded["lead1_id"]
    res = await export_client.get(f"/api/leads/{l1}/export/csv")
    assert res.status_code == 200
    assert 'leadscout-St-Patrick-' in res.headers["content-disposition"]
    text = res.content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["Organization Name"] == "St. Patrick Matriculation Higher Secondary School"


@pytest.mark.asyncio
async def test_export_single_lead_excel(export_client: AsyncClient):
    """Test exporting a single lead profile as Excel."""
    l3 = export_client.seeded["lead3_id"]
    res = await export_client.get(f"/api/leads/{l3}/export/excel")
    assert res.status_code == 200
    wb = openpyxl.load_workbook(io.BytesIO(res.content))
    ws = wb["Leads"]
    assert ws.max_row == 2
    headers = [cell.value for cell in ws[1]]
    row2 = [cell.value for cell in ws[2]]
    data_dict = dict(zip(headers, row2))
    assert data_dict["Organization Name"] == "Apollo Specialty Hospital"
    assert data_dict["City"] == "Chennai"


# ── 5. Field Selection & Alias Mapping ───────────────────────────────────────

@pytest.mark.asyncio
async def test_export_field_selection(export_client: AsyncClient):
    """Test specifying custom subset of fields with aliases."""
    task_id = export_client.seeded["t1_id"]
    # Request 'name' (alias for organization_name), 'phone', 'email', 'city'
    res = await export_client.get(f"/api/tasks/{task_id}/export/csv?fields=name,phone,email,city")
    assert res.status_code == 200
    text = res.content.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text))
    header = next(reader)
    assert header == ["Organization Name", "Phone", "Email", "City"]


@pytest.mark.asyncio
async def test_export_invalid_field_rejected(export_client: AsyncClient):
    """Test requesting an unsupported field returns HTTP 422 INVALID_EXPORT_FIELD."""
    res = await export_client.get("/api/leads/export/csv?fields=name,unknown_hack_field")
    assert res.status_code == 422
    data = res.json()
    assert data["error"]["code"] == "INVALID_EXPORT_FIELD"
    assert "unknown_hack_field" in data["error"]["message"]


# ── 6. Text Safety and Formatting ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_excel_phone_number_text_safety(export_client: AsyncClient):
    """Test phone numbers and pincodes in Excel are stored as explicit text to avoid formula/float mangling."""
    task_id = export_client.seeded["t1_id"]
    res = await export_client.get(f"/api/tasks/{task_id}/export/excel")
    assert res.status_code == 200

    wb = openpyxl.load_workbook(io.BytesIO(res.content))
    ws = wb["Leads"]
    headers = [cell.value for cell in ws[1]]
    phone_col_idx = headers.index("Phone") + 1
    pincode_col_idx = headers.index("Pincode") + 1

    # Check data cells (row 2 and 3)
    for row_idx in [2, 3]:
        phone_cell = ws.cell(row=row_idx, column=phone_col_idx)
        pincode_cell = ws.cell(row=row_idx, column=pincode_col_idx)
        assert phone_cell.data_type == "s"
        assert phone_cell.number_format == "@"
        assert pincode_cell.data_type == "s"
        assert pincode_cell.number_format == "@"


@pytest.mark.asyncio
async def test_source_urls_and_contacts_semicolons(export_client: AsyncClient):
    """Test multiple contacts or source URLs are formatted with semicolon delimiters."""
    l1 = export_client.seeded["lead1_id"]
    res = await export_client.get(f"/api/leads/{l1}/export/csv")
    assert res.status_code == 200
    text = res.content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    row = next(reader)
    assert row["Contact Person"] == "Fr. John Britto"
    assert row["Designation"] == "Principal"
    assert "https://stpatricks.edu/contact" in row["Source URLs"]


# ── 7. Error Handling & Guardrails ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_export_task_not_found(export_client: AsyncClient):
    """Test exporting a non-existent task returns 404."""
    res = await export_client.get("/api/tasks/TASK-NON-EXISTENT-999/export/csv")
    assert res.status_code == 404
    data = res.json()
    assert data["error"]["code"] == "TASK_NOT_FOUND"


@pytest.mark.asyncio
async def test_export_empty_task_returns_404(export_client: AsyncClient):
    """Test exporting a task with 0 leads returns 404 NO_LEADS_TO_EXPORT."""
    task_id = export_client.seeded["t3_id"]
    res = await export_client.get(f"/api/tasks/{task_id}/export/csv")
    assert res.status_code == 404
    data = res.json()
    assert data["error"]["code"] == "NO_LEADS_TO_EXPORT"


@pytest.mark.asyncio
async def test_export_single_lead_not_found(export_client: AsyncClient):
    """Test exporting a non-existent single lead returns 404."""
    fake_uuid = str(uuid.uuid4())
    res = await export_client.get(f"/api/leads/{fake_uuid}/export/csv")
    assert res.status_code == 404
    data = res.json()
    assert data["error"]["code"] == "LEAD_NOT_FOUND"


@pytest.mark.asyncio
async def test_export_selected_leads_invalid_uuid(export_client: AsyncClient):
    """Test invalid UUID format in ids returns 422 INVALID_LEAD_ID."""
    res = await export_client.get("/api/leads/export/csv?ids=not-a-valid-uuid")
    assert res.status_code == 422
    data = res.json()
    assert data["error"]["code"] == "INVALID_LEAD_ID"


@pytest.mark.asyncio
async def test_export_no_matching_filtered_leads_returns_404(export_client: AsyncClient):
    """Test search with no matches returns 404 NO_LEADS_TO_EXPORT."""
    res = await export_client.get("/api/leads/export/csv?search=CompletelyNonExistentXYZ")
    assert res.status_code == 404
    data = res.json()
    assert data["error"]["code"] == "NO_LEADS_TO_EXPORT"


@pytest.mark.asyncio
async def test_export_max_rows_limit(export_client: AsyncClient, monkeypatch):
    """Test requesting export when count exceeds MAX_EXPORT_ROWS returns 413 EXPORT_TOO_LARGE."""
    # Temporarily set MAX_EXPORT_ROWS to 1
    monkeypatch.setattr(settings, "MAX_EXPORT_ROWS", 1)
    res = await export_client.get("/api/leads/export/csv")
    assert res.status_code == 413
    data = res.json()
    assert data["error"]["code"] == "EXPORT_TOO_LARGE"


# ── 8. Filename Sanitization Unit Tests ──────────────────────────────────────

def test_sanitize_filename():
    assert sanitize_filename("Normal Task Name") == "Normal-Task-Name"
    assert sanitize_filename("../../../etc/passwd") == "etc-passwd"
    assert sanitize_filename('special!@#$%^&*()_+="symbols') == "special-symbols"
    assert sanitize_filename("") == "export"


def test_build_export_filename():
    fn_csv = build_export_filename(source_type="task", task_id="TASK-001", extension="csv")
    assert fn_csv.startswith("leadscout-task-TASK-001-")
    assert fn_csv.endswith(".csv")

    fn_excel = build_export_filename(source_type="all", extension="xlsx")
    assert fn_excel.startswith("leadscout-leads-")
    assert fn_excel.endswith(".xlsx")
