"""
app/models/extracted_field.py

ExtractedField — provenance and audit trail for public data extracted from web pages.

Table: extracted_fields
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.source_page import SourcePage


class ExtractedField(UUIDMixin, TimestampMixin, Base):
    """Provenance audit log for individual data points scraped from source pages.

    Tracks which exact page yielded each field value (phone, email, address, etc.)
    without storing arbitrary unvetted data.
    """

    __tablename__ = "extracted_fields"
    __table_args__ = (
        sa.Index("ix_extracted_fields_org_field", "organization_id", "field_name"),
        sa.Index("ix_extracted_fields_page_field", "source_page_id", "field_name"),
        sa.Index("ix_extracted_fields_normalized", "normalized_value"),
    )

    # ── Foreign keys ──────────────────────────────────────────────────────────
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    source_page_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("source_pages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Field details ─────────────────────────────────────────────────────────
    field_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    field_value: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_value: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    organization: Mapped[Organization] = relationship("Organization")
    source_page: Mapped[SourcePage] = relationship(
        "SourcePage", back_populates="extracted_fields"
    )

    def __repr__(self) -> str:
        return (
            f"<ExtractedField id={self.id} field={self.field_name} "
            f"org_id={self.organization_id} page_id={self.source_page_id}>"
        )
