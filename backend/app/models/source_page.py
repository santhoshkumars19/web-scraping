"""
app/models/source_page.py

SourcePage — a specific public web page that was crawled.

Provides full provenance: every extracted data point can be traced
back to the exact URL it was scraped from.

Table: source_pages
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.website import Website
    from app.models.scraping_task import ScrapingTask
    from app.models.extracted_field import ExtractedField


page_type_enum = SAEnum(
    "HOME", "ABOUT", "CONTACT", "ADMISSIONS", "MANAGEMENT",
    "PRINCIPAL", "FACULTY", "STAFF", "BRANCH", "LOCATION",
    "INFRASTRUCTURE", "OTHER",
    name="page_type_enum",
)


class SourcePage(UUIDMixin, TimestampMixin, Base):
    """A crawled web page — the provenance record for extracted data.

    Immutable after creation (TimestampMixin, no updated_at).
    """

    __tablename__ = "source_pages"
    __table_args__ = (
        UniqueConstraint(
            "website_id", "normalized_url",
            name="uq_source_page_website_url",
        ),
    )

    # ── Ownership ────────────────────────────────────────────────────────────
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    website_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("websites.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Which task triggered the discovery of this page
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("scraping_tasks.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # ── Page data ─────────────────────────────────────────────────────────────
    url: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_url: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    page_title: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    page_type: Mapped[str] = mapped_column(
        page_type_enum,
        nullable=False,
        default="OTHER",
        server_default="OTHER",
        index=True,
    )

    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    discovered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    crawled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    organization: Mapped[Organization] = relationship(
        "Organization", back_populates="source_pages"
    )
    website: Mapped[Website | None] = relationship(
        "Website", back_populates="source_pages"
    )
    task: Mapped[ScrapingTask | None] = relationship(
        "ScrapingTask", back_populates="source_pages"
    )

    extracted_fields: Mapped[list[ExtractedField]] = relationship(
        "ExtractedField",
        back_populates="source_page",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<SourcePage id={self.id} page_type={self.page_type} url={self.url[:60]!r}>"
