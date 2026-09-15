"""
app/models/website.py

Website — a public URL belonging to an Organization.

An organization can have multiple websites/subdomains.

Table: websites
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin, TimestampWithUpdateMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.source_page import SourcePage


website_status_enum = SAEnum(
    "PENDING", "CRAWLING", "CRAWLED", "FAILED", "BLOCKED",
    name="website_status_enum",
)


class Website(UUIDMixin, TimestampWithUpdateMixin, Base):
    """A crawlable URL linked to an Organization."""

    __tablename__ = "websites"
    __table_args__ = (
        UniqueConstraint("organization_id", "normalized_url", name="uq_website_org_url"),
    )

    # ── Ownership ────────────────────────────────────────────────────────────
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── URL fields ───────────────────────────────────────────────────────────
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    normalized_url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    # ── Flags ────────────────────────────────────────────────────────────────
    is_official: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    # ── Status ───────────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        website_status_enum,
        nullable=False,
        default="PENDING",
        server_default="PENDING",
    )

    last_crawled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    organization: Mapped[Organization] = relationship(
        "Organization", back_populates="websites"
    )

    source_pages: Mapped[list[SourcePage]] = relationship(
        "SourcePage",
        back_populates="website",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Website id={self.id} domain={self.domain!r} status={self.status}>"
