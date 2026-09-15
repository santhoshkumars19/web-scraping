"""
app/db/database.py

Async SQLAlchemy engine, session factory, and FastAPI dependency.

Architecture
────────────
• Uses SQLAlchemy 2.x async engine backed by asyncpg.
• A single engine is created at startup and disposed on shutdown (via lifespan).
• `get_db()` yields an AsyncSession per request and rolls back automatically
  on unhandled exceptions, then closes the session.
• `Base` is the declarative base all ORM models will inherit from.
"""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# ─── Module-level engine & session factory ───────────────────────────────────
# These are initialised in `create_engine_and_factory()` which is called from
# the FastAPI lifespan handler — not at import time — so that tests can
# override the DATABASE_URL before the engine is created.

_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


# ─── Declarative base ────────────────────────────────────────────────────────


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models.

    Inheriting from this class registers the model's metadata so that
    Alembic autogenerate can detect schema changes.
    """


# ─── Engine lifecycle ────────────────────────────────────────────────────────


def create_engine_and_factory(database_url: str | None = None) -> AsyncEngine:
    """Create the async engine and session factory.

    Designed to be called once during application startup (via lifespan).
    Passing `database_url` overrides Settings.DATABASE_URL (useful in tests).
    """
    global _engine, _async_session_factory

    raw_url = database_url or settings.DATABASE_URL
    url = raw_url.strip()
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("sqlite://") and "+aiosqlite" not in url:
        url = url.replace("sqlite://", "sqlite+aiosqlite://", 1)

    _engine = create_async_engine(
        url,
        echo=settings.DEBUG,          # logs SQL statements when DEBUG=true
        pool_pre_ping=True,            # validates connections before use
        pool_size=5,
        max_overflow=10,
        pool_recycle=3600,
    )

    _async_session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,        # avoid implicit lazy-loads after commit
        autoflush=False,
    )

    logger.info("Async database engine created. URL schema: %s", url.split("://")[0])
    return _engine


async def dispose_engine() -> None:
    """Dispose the async engine, closing all pooled connections.

    Call this in the FastAPI shutdown lifespan hook.
    """
    global _engine
    if _engine is not None:
        await _engine.dispose()
        logger.info("Database engine disposed.")
        _engine = None


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the module-level session factory.

    Raises RuntimeError if the engine has not been initialised yet.
    """
    if _async_session_factory is None:
        raise RuntimeError(
            "Database engine has not been initialised. "
            "Call `create_engine_and_factory()` during application startup."
        )
    return _async_session_factory


# ─── FastAPI dependency ───────────────────────────────────────────────────────


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields one AsyncSession per request.

    Usage in a route::

        @router.get("/example")
        async def example(db: AsyncSession = Depends(get_db)):
            ...

    The session is rolled back automatically if an unhandled exception
    propagates, then closed regardless.
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
