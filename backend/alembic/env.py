"""
alembic/env.py

Alembic migration environment — async edition.

Key design decisions:
• Reads DATABASE_URL from app settings (not from alembic.ini's sqlalchemy.url)
  so there is a single source of truth and no credentials in alembic.ini.
• Uses SQLAlchemy async engine with asyncpg driver.
• `target_metadata` points at Base.metadata so autogenerate works for all
  registered ORM models.
• All ORM models are imported (via app.models) before autogenerate runs so
  Alembic can diff them against the live schema.
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

# ── Import application components ────────────────────────────────────────────
# Settings must be imported before anything that reads env vars.
from app.core.config import settings

# Import Base so Alembic has access to metadata.
from app.db.database import Base  # noqa: F401

# Import all models so they register themselves on Base.metadata.
import app.models  # noqa: F401 — registers model classes via side-effects

# ── Alembic Config object ─────────────────────────────────────────────────────
config = context.config

# Interpret the config file for Python logging if present.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate support.
target_metadata = Base.metadata


# ─── Offline migrations ───────────────────────────────────────────────────────


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    In offline mode Alembic does not need a live DB connection — it simply
    emits the SQL DDL statements to stdout or a file.
    """
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ─── Online migrations ────────────────────────────────────────────────────────


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations using an async engine."""
    connectable = create_async_engine(
        settings.DATABASE_URL,
        poolclass=pool.NullPool,   # use NullPool so connections close after migration
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online (connected) migrations."""
    asyncio.run(run_async_migrations())


# ─── Entry point ──────────────────────────────────────────────────────────────

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
