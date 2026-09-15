"""
tests/test_ownership.py

Comprehensive test suite for Backend Step 13:
Resource Ownership Scoping, Anti-Enumeration 404s, and Multi-Tenant Isolation.

Verifies that:
1. User A and User B cannot see or manipulate each other's ScrapingTasks.
2. User A and User B cannot query each other's Lead records.
3. User A and User B cannot export each other's Tasks or Leads (including selected ID spoofing).
4. User A and User B cannot stream WebSocket events for each other's tasks.
5. Client-supplied user_id injection in POST /api/scrape is ignored/overridden.
6. Non-existent and unauthorized resources both return 404 to prevent ID enumeration.
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from app.core.config import settings
from app.core.security import create_access_token
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
from app.models.user import User
from app.models.website import Website
from app.realtime import connection_manager


USER_A_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
USER_B_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


@pytest.fixture()
async def multi_user_env():
    """Seed database with User A (and task + lead) and User B (and task + lead)."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    seeded: dict[str, Any] = {}

    async with session_factory() as session:
        # Create User A
        user_a = User(
            id=USER_A_ID,
            name="Alice Owner",
            email="alice.owner@leadscout.app",
            email_normalized="alice.owner@leadscout.app",
            password_hash="$argon2id$mock_hash_a",
            role="USER",
            is_active=True,
        )
        # Create User B
        user_b = User(
            id=USER_B_ID,
            name="Bob Attacker",
            email="bob.attacker@leadscout.app",
            email_normalized="bob.attacker@leadscout.app",
            password_hash="$argon2id$mock_hash_b",
            role="USER",
            is_active=True,
        )
        session.add_all([user_a, user_b])
        await session.flush()

        # Task A owned by User A
        task_a = ScrapingTask(
            id=uuid.uuid4(),
            task_id="TASK-000001",
            user_id=USER_A_ID,
            location="Puducherry",
            keyword="Private Schools",
            status="COMPLETED",
            current_stage="COMPLETED",
            progress=100,
            results_discovered=1,
            selected_fields=["name", "phone", "email"],
        )
        # Task B owned by User B
        task_b = ScrapingTask(
            id=uuid.uuid4(),
            task_id="TASK-000002",
            user_id=USER_B_ID,
            location="Chennai",
            keyword="Hospitals",
            status="COMPLETED",
            current_stage="COMPLETED",
            progress=100,
            results_discovered=1,
            selected_fields=["name", "phone", "email"],
        )
        session.add_all([task_a, task_b])
        await session.flush()

        # Lead A under Task A
        org_a = Organization(
            name="St. Patrick School",
            category="School",
            city="Puducherry",
            state="Puducherry",
        )
        session.add(org_a)
        await session.flush()

        lead_a = Lead(
            id=uuid.uuid4(),
            task_id=task_a.id,
            organization_id=org_a.id,
            verification_status="HIGH",
        )
        session.add(lead_a)
        await session.flush()

        web_a = Website(
            organization_id=org_a.id,
            url="https://stpatricks.edu",
            normalized_url="https://stpatricks.edu",
            domain="stpatricks.edu",
            is_official=True,
        )
        phone_a = PhoneNumber(
            organization_id=org_a.id,
            phone_number="+91 413 2221111",
            normalized_phone="+914132221111",
            is_primary=True,
        )
        session.add_all([web_a, phone_a])

        # Lead B under Task B
        org_b = Organization(
            name="Apollo Hospital",
            category="Healthcare",
            city="Chennai",
            state="Tamil Nadu",
        )
        session.add(org_b)
        await session.flush()

        lead_b = Lead(
            id=uuid.uuid4(),
            task_id=task_b.id,
            organization_id=org_b.id,
            verification_status="HIGH",
        )
        session.add(lead_b)
        await session.flush()

        web_b = Website(
            organization_id=org_b.id,
            url="https://apollo.example",
            normalized_url="https://apollo.example",
            domain="apollo.example",
            is_official=True,
        )
        phone_b = PhoneNumber(
            organization_id=org_b.id,
            phone_number="+91 44 28290000",
            normalized_phone="+914428290000",
            is_primary=True,
        )
        session.add_all([web_b, phone_b])

        await session.commit()

        seeded["task_a_id"] = task_a.task_id
        seeded["task_a_uuid"] = str(task_a.id)
        seeded["lead_a_id"] = str(lead_a.id)
        seeded["task_b_id"] = task_b.task_id
        seeded["task_b_uuid"] = str(task_b.id)
        seeded["lead_b_id"] = str(lead_b.id)

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    fastapi_app.dependency_overrides[get_db] = override_get_db

    # Also override database module engine/factory for websockets
    import app.db.database as db_mod
    orig_engine = db_mod._engine
    orig_factory = db_mod._async_session_factory
    db_mod._engine = engine
    db_mod._async_session_factory = session_factory

    token_a = create_access_token(USER_A_ID)
    token_b = create_access_token(USER_B_ID)

    mock_celery = MagicMock()
    mock_celery.id = "mock-pipeline-uuid"

    with patch("app.workers.pipeline.run_scraping_pipeline.delay", return_value=mock_celery):
        async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://testserver") as client_a:
            client_a.headers["Authorization"] = f"Bearer {token_a}"
            async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://testserver") as client_b:
                client_b.headers["Authorization"] = f"Bearer {token_b}"
                yield {
                    "client_a": client_a,
                    "client_b": client_b,
                    "token_a": token_a,
                    "token_b": token_b,
                    "seeded": seeded,
                }

    fastapi_app.dependency_overrides.clear()
    db_mod._engine = orig_engine
    db_mod._async_session_factory = orig_factory
    await engine.dispose()


# ── 1. Task Ownership & Injection Tests ──────────────────────────────────────

@pytest.mark.asyncio
async def test_create_task_overrides_injected_user_id(multi_user_env):
    """User B cannot create a task on behalf of User A by sending user_id in payload."""
    client_b = multi_user_env["client_b"]

    payload = {
        "location": "Bengaluru",
        "keyword": "Tech Startups",
        "selected_fields": ["name", "phone", "email"],
        "user_id": str(USER_A_ID),  # Attempted spoof
    }
    res = await client_b.post("/api/scrape", json=payload)
    assert res.status_code == 201
    task_data = res.json()["data"]

    # The created task must belong to User B, not User A
    assert task_data["task_id"] is not None

    # User B can view it
    get_res = await client_b.get(f"/api/tasks/{task_data['task_id']}")
    assert get_res.status_code == 200

    # User A cannot view it (anti-enumeration 404)
    client_a = multi_user_env["client_a"]
    unauth_get = await client_a.get(f"/api/tasks/{task_data['task_id']}")
    assert unauth_get.status_code == 404
    assert unauth_get.json()["error"]["code"] == "TASK_NOT_FOUND"


@pytest.mark.asyncio
async def test_list_tasks_scoped_to_current_user(multi_user_env):
    """GET /api/tasks only returns tasks owned by the requesting user."""
    client_a = multi_user_env["client_a"]
    client_b = multi_user_env["client_b"]
    seeded = multi_user_env["seeded"]

    # User A list
    res_a = await client_a.get("/api/tasks")
    assert res_a.status_code == 200
    tasks_a = res_a.json()["data"]
    assert any(t["task_id"] == seeded["task_a_id"] for t in tasks_a)
    assert not any(t["task_id"] == seeded["task_b_id"] for t in tasks_a)

    # User B list
    res_b = await client_b.get("/api/tasks")
    assert res_b.status_code == 200
    tasks_b = res_b.json()["data"]
    assert any(t["task_id"] == seeded["task_b_id"] for t in tasks_b)
    assert not any(t["task_id"] == seeded["task_a_id"] for t in tasks_b)


@pytest.mark.asyncio
async def test_get_task_cross_user_returns_404(multi_user_env):
    """GET /api/tasks/{task_id} for another user's task returns 404 to avoid enumeration."""
    client_b = multi_user_env["client_b"]
    seeded = multi_user_env["seeded"]

    # User B attempts to access User A's task
    res = await client_b.get(f"/api/tasks/{seeded['task_a_id']}")
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "TASK_NOT_FOUND"


@pytest.mark.asyncio
async def test_get_task_leads_cross_user_returns_404(multi_user_env):
    """GET /api/tasks/{task_id}/leads for another user's task returns 404."""
    client_b = multi_user_env["client_b"]
    seeded = multi_user_env["seeded"]

    # User B attempts to access User A's task leads
    res = await client_b.get(f"/api/tasks/{seeded['task_a_id']}/leads")
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "TASK_NOT_FOUND"


# ── 2. Lead Query Ownership Tests ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_leads_scoped_to_current_user(multi_user_env):
    """GET /api/leads only returns leads from tasks owned by the requesting user."""
    client_a = multi_user_env["client_a"]
    client_b = multi_user_env["client_b"]
    seeded = multi_user_env["seeded"]

    res_a = await client_a.get("/api/leads")
    assert res_a.status_code == 200
    leads_a = res_a.json()["data"]
    assert any(l["id"] == seeded["lead_a_id"] for l in leads_a)
    assert not any(l["id"] == seeded["lead_b_id"] for l in leads_a)

    res_b = await client_b.get("/api/leads")
    assert res_b.status_code == 200
    leads_b = res_b.json()["data"]
    assert any(l["id"] == seeded["lead_b_id"] for l in leads_b)
    assert not any(l["id"] == seeded["lead_a_id"] for l in leads_b)


@pytest.mark.asyncio
async def test_get_lead_detail_cross_user_returns_404(multi_user_env):
    """GET /api/leads/{lead_id} for another user's lead returns 404."""
    client_b = multi_user_env["client_b"]
    seeded = multi_user_env["seeded"]

    res = await client_b.get(f"/api/leads/{seeded['lead_a_id']}")
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "LEAD_NOT_FOUND"


# ── 3. Export Ownership Tests ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_export_task_csv_cross_user_returns_404(multi_user_env):
    """GET /api/tasks/{task_id}/export/csv for another user's task returns 404."""
    client_b = multi_user_env["client_b"]
    seeded = multi_user_env["seeded"]

    res = await client_b.get(f"/api/tasks/{seeded['task_a_id']}/export/csv")
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "TASK_NOT_FOUND"


@pytest.mark.asyncio
async def test_export_task_excel_cross_user_returns_404(multi_user_env):
    """GET /api/tasks/{task_id}/export/excel for another user's task returns 404."""
    client_b = multi_user_env["client_b"]
    seeded = multi_user_env["seeded"]

    res = await client_b.get(f"/api/tasks/{seeded['task_a_id']}/export/excel")
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "TASK_NOT_FOUND"


@pytest.mark.asyncio
async def test_export_single_lead_cross_user_returns_404(multi_user_env):
    """GET /api/leads/{lead_id}/export/csv and excel for another user's lead returns 404."""
    client_b = multi_user_env["client_b"]
    seeded = multi_user_env["seeded"]

    res_csv = await client_b.get(f"/api/leads/{seeded['lead_a_id']}/export/csv")
    assert res_csv.status_code == 404
    assert res_csv.json()["error"]["code"] == "LEAD_NOT_FOUND"

    res_excel = await client_b.get(f"/api/leads/{seeded['lead_a_id']}/export/excel")
    assert res_excel.status_code == 404
    assert res_excel.json()["error"]["code"] == "LEAD_NOT_FOUND"


@pytest.mark.asyncio
async def test_export_selected_ids_cross_user_rejected(multi_user_env):
    """User B cannot export User A's leads by supplying ids={lead_a_id}."""
    client_b = multi_user_env["client_b"]
    seeded = multi_user_env["seeded"]

    # Spoof User A's lead ID in global export
    res = await client_b.get(f"/api/leads/export/csv?ids={seeded['lead_a_id']}")
    assert res.status_code == 404
    assert res.json()["error"]["code"] in ("LEAD_NOT_FOUND", "NO_LEADS_TO_EXPORT")


# ── 4. WebSocket Ownership Tests ─────────────────────────────────────────────

def test_websocket_cross_user_connection_rejected(multi_user_env):
    """User B cannot stream progress for User A's task via WebSocket."""
    token_b = multi_user_env["token_b"]
    task_a_id = multi_user_env["seeded"]["task_a_id"]

    test_client = TestClient(fastapi_app)
    with test_client.websocket_connect(
        f"/api/ws/tasks/{task_a_id}?token={token_b}"
    ) as ws:
        msg = ws.receive_json()
        assert msg["type"] == "task.error"
        assert msg["data"]["code"] == "TASK_NOT_FOUND"


def test_websocket_invalid_token_rejected():
    """Connecting with an invalid token rejects with UNAUTHENTICATED error and closes."""
    test_client = TestClient(fastapi_app)
    with test_client.websocket_connect(
        "/api/ws/tasks/TASK-000001?token=invalid.jwt.token"
    ) as ws:
        msg = ws.receive_json()
        assert msg["type"] == "task.error"
        assert msg["data"]["code"] == "UNAUTHENTICATED"
