"""
app/models/user.py

User — an authenticated LeadScout platform user who creates scraping tasks.

Table: users
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

import sqlalchemy as sa
from sqlalchemy import Boolean, Enum as SAEnum, String, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampWithUpdateMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.scraping_task import ScrapingTask


class UserRole(str):
    USER = "USER"
    ADMIN = "ADMIN"


class User(UUIDMixin, TimestampWithUpdateMixin, Base):
    """Platform user account.

    Passwords are NEVER stored in plaintext — only bcrypt hashes.
    """

    __tablename__ = "users"

    # ── Identity ──────────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
        unique=True,
        index=True,
    )

    email_normalized: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
        unique=True,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    def __init__(self, **kwargs: Any) -> None:
        if "email" in kwargs and not kwargs.get("email_normalized") and kwargs["email"]:
            kwargs["email_normalized"] = kwargs["email"].strip().lower()
        super().__init__(**kwargs)

    # ── Profile ───────────────────────────────────────────────────────────────
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)

    role: Mapped[str] = mapped_column(
        SAEnum("USER", "ADMIN", name="user_role_enum"),
        nullable=False,
        default="USER",
        server_default="USER",
    )

    avatar_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=sa.true()
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    tasks: Mapped[list[ScrapingTask]] = relationship(
        "ScrapingTask",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role}>"


@event.listens_for(User, "before_insert")
def _auto_normalize_email_before_insert(mapper: Any, connection: Any, target: User) -> None:
    if target.email and not target.email_normalized:
        target.email_normalized = target.email.strip().lower()


@event.listens_for(User, "before_update")
def _auto_normalize_email_before_update(mapper: Any, connection: Any, target: User) -> None:
    if target.email and not target.email_normalized:
        target.email_normalized = target.email.strip().lower()
