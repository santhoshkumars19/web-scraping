"""
app/db/base.py

Shared mixin classes and the re-exported Base.

All ORM models import `Base` from here (not from database.py directly)
to keep a clean separation: database.py owns the engine / session,
base.py owns the ORM scaffolding that models depend on.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base  # re-export for convenience

__all__ = ["Base", "UUIDMixin", "TimestampMixin", "TimestampWithUpdateMixin"]


# ── Helpers ───────────────────────────────────────────────────────────────────


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Mixins ────────────────────────────────────────────────────────────────────


class UUIDMixin:
    """Primary key mixin: UUID stored as a native PostgreSQL UUID column."""

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        sort_order=-100,
    )


class TimestampMixin:
    """Adds only `created_at` (immutable records like logs)."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        sort_order=100,
    )


class TimestampWithUpdateMixin(TimestampMixin):
    """Adds `created_at` + `updated_at` (mutable entities)."""

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        sort_order=101,
    )
