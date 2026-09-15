"""
app/models/lead_verification.py

LeadVerification — data confidence, completeness, source quality, and consistency scores.

Table: lead_verifications
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

import sqlalchemy as sa
from sqlalchemy import DateTime, Enum as SAEnum, Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampWithUpdateMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.lead import Lead
    from app.models.organization import Organization


verification_status_enum = SAEnum(
    "PENDING", "LOW", "MEDIUM", "HIGH",
    name="verification_status_enum",
)


class LeadVerification(UUIDMixin, TimestampWithUpdateMixin, Base):
    """Quality and completeness evaluation record for a lead.

    Evaluates:
    - Field completeness against task.selected_fields (0–100%)
    - Source quality and provenance (official website vs. directory) (0–100)
    - Cross-field consistency (domain match, valid syntax, conflict checks) (0–100)
    - Weighted data confidence score (0–100)
    - Confidence tier: HIGH (80–100), MEDIUM (60–79), LOW (0–59)
    """

    __tablename__ = "lead_verifications"
    __table_args__ = (
        UniqueConstraint("lead_id", name="uq_verification_lead"),
        sa.Index("ix_lead_verifications_org", "organization_id"),
        sa.Index("ix_lead_verifications_lead", "lead_id"),
    )

    # ── Foreign keys ──────────────────────────────────────────────────────────
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # ── Verification tier & score ─────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        verification_status_enum,
        nullable=False,
        default="PENDING",
        server_default="PENDING",
    )

    score: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    # ── Sub-scores & Metrics ──────────────────────────────────────────────────
    fields_found: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    total_fields: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    completeness_percentage: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, server_default="0.0"
    )
    source_quality_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, server_default="0.0"
    )
    consistency_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, server_default="0.0"
    )

    # ── Structured Evidence & Audit Trail ─────────────────────────────────────
    verification_reasons: Mapped[dict[str, Any]] = mapped_column(
        sa.JSON, nullable=False, default=dict
    )
    source_quality_details: Mapped[dict[str, Any]] = mapped_column(
        sa.JSON, nullable=False, default=dict
    )

    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    organization: Mapped[Organization] = relationship(
        "Organization", back_populates="verifications"
    )
    lead: Mapped[Lead | None] = relationship(
        "Lead", back_populates="verification"
    )

    def __repr__(self) -> str:
        return (
            f"<LeadVerification id={self.id} org_id={self.organization_id} "
            f"status={self.status} score={self.score} "
            f"completeness={self.completeness_percentage:.1f}%>"
        )
