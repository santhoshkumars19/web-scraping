"""
app/models/organization.py

Organization — the core business entity discovered by a scraping task.

Table: organizations
Association table: task_organizations (M2M with scraping_tasks)
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import Column, DateTime, ForeignKey, String, Table, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin, TimestampWithUpdateMixin

if TYPE_CHECKING:
    from app.models.scraping_task import ScrapingTask
    from app.models.website import Website
    from app.models.contact import Contact
    from app.models.phone_number import PhoneNumber
    from app.models.email_address import EmailAddress
    from app.models.social_link import SocialLink
    from app.models.source_page import SourcePage
    from app.models.lead import Lead
    from app.models.lead_verification import LeadVerification


# ── Many-to-many association table ────────────────────────────────────────────

task_organizations = Table(
    "task_organizations",
    Base.metadata,
    Column(
        "task_id",
        ForeignKey("scraping_tasks.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "organization_id",
        ForeignKey("organizations.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
)


# ── Organization model ────────────────────────────────────────────────────────


class Organization(UUIDMixin, TimestampWithUpdateMixin, Base):
    """A real-world business entity discovered during scraping.

    Kept normalized so the same organization can be linked to multiple tasks
    without duplicating its core identity data.
    """

    __tablename__ = "organizations"
    __table_args__ = (
        sa.Index("ix_organizations_name", "name"),
        sa.Index("ix_organizations_city_state", "city", "state"),
        sa.Index("ix_organizations_pincode", "pincode"),
    )

    # ── Identity ──────────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    # ── Address ───────────────────────────────────────────────────────────────
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    state: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pincode: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # ── Soft delete ───────────────────────────────────────────────────────────
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    tasks: Mapped[list[ScrapingTask]] = relationship(
        "ScrapingTask",
        secondary="task_organizations",
        back_populates="organizations",
        passive_deletes=True,
        lazy="selectin",
    )

    websites: Mapped[list[Website]] = relationship(
        "Website",
        back_populates="organization",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    contacts: Mapped[list[Contact]] = relationship(
        "Contact",
        back_populates="organization",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    phone_numbers: Mapped[list[PhoneNumber]] = relationship(
        "PhoneNumber",
        back_populates="organization",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    email_addresses: Mapped[list[EmailAddress]] = relationship(
        "EmailAddress",
        back_populates="organization",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    social_links: Mapped[list[SocialLink]] = relationship(
        "SocialLink",
        back_populates="organization",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    source_pages: Mapped[list[SourcePage]] = relationship(
        "SourcePage",
        back_populates="organization",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    leads: Mapped[list[Lead]] = relationship(
        "Lead",
        back_populates="organization",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    verifications: Mapped[list[LeadVerification]] = relationship(
        "LeadVerification",
        back_populates="organization",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Organization id={self.id} name={self.name!r}>"
