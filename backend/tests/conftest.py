"""
tests/conftest.py

Shared pytest fixtures for the LeadScout backend test suite.

Sets up:
• An in-memory SQLite database (via aiosqlite) for tests that don't need
  real PostgreSQL — keeps CI fast without a database server.
• An HTTPX AsyncClient targeting the FastAPI app.

NOTE: Tests that genuinely require PostgreSQL should use a separate marker
and are not yet implemented in this foundation step.
"""

from __future__ import annotations

import os
import pytest
from httpx import ASGITransport, AsyncClient

# ── Force test environment BEFORE importing app modules ───────────────────────
os.environ.setdefault("APP_NAME", "LeadScout-Test")
os.environ.setdefault("APP_VERSION", "1.0.0")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://leadscout:leadscout@localhost:5432/leadscout",
)
os.environ.setdefault("API_PREFIX", "/api")
os.environ.setdefault("CORS_ORIGINS", '["http://localhost:3000"]')
os.environ.setdefault("LOG_LEVEL", "WARNING")

from app.main import app  # noqa: E402 — must come after env setup


@pytest.fixture(autouse=True)
def reset_rate_limiters():
    """Ensure in-memory rate limiters are fresh for each test."""
    from app.core.rate_limiter import api_rate_limiter
    from app.services.auth_rate_limiter import auth_rate_limiter
    api_rate_limiter.reset_fallback()
    auth_rate_limiter.reset_all()
    yield
    api_rate_limiter.reset_fallback()
    auth_rate_limiter.reset_all()


@pytest.fixture()
async def client() -> AsyncClient:  # type: ignore[misc]
    """Async HTTPX client wired to the FastAPI application (without DB override)."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac


@pytest.fixture()
async def test_app_client():
    """Async HTTPX client with an in-memory SQLite DB wired to get_db dependency."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from sqlalchemy.pool import StaticPool
    from app.db.base import Base
    from app.db.database import get_db
    from app.main import app as fastapi_app
    import app.models as _models  # noqa: F401

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Pre-seed demo user so concurrent tests don't collide on initial user insertion
    import uuid
    from app.models.user import User
    async with session_factory() as init_session:
        demo_user = User(
            id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            name="Demo Scout",
            email="demo@leadscout.app",
            password_hash="$2b$12$demo_placeholder_hash",
            role="USER",
            is_active=True,
        )
        init_session.add(demo_user)
        await init_session.commit()

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    fastapi_app.dependency_overrides[get_db] = override_get_db

    from unittest.mock import MagicMock, patch
    mock_celery_res = MagicMock()
    mock_celery_res.id = "mock-celery-pipeline-id-12345"

    from app.core.security import create_access_token
    token = create_access_token(uuid.UUID("11111111-1111-1111-1111-111111111111"))

    with patch("app.workers.pipeline.run_scraping_pipeline.delay", return_value=mock_celery_res):
        async with AsyncClient(
            transport=ASGITransport(app=fastapi_app),
            base_url="http://testserver",
            headers={"Authorization": f"Bearer {token}"},
        ) as ac:
            yield ac

    fastapi_app.dependency_overrides.clear()
    await engine.dispose()


@pytest.fixture()
async def db_session():
    """Isolated in-memory async database session for model tests."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from app.db.base import Base
    import app.models  # noqa: F401

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()

