"""
app/models/lead.py

Lead — links an Organization discovered by a specific ScrapingTask.

The same organization can become a lead in multiple tasks.
This table holds the task-specific status and verification snapshot.

Table: leads
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin, TimestampWithUpdateMixin

if TYPE_CHECKING:
    from app.models.scraping_task import ScrapingTask
    from app.models.organization import Organization
    from app.models.lead_verification import LeadVerification


lead_status_enum = SAEnum(
    "ACTIVE", "ARCHIVED", "DELETED",
    name="lead_status_enum",
)

lead_verification_status_enum = SAEnum(
    "PENDING", "LOW", "MEDIUM", "HIGH",
    name="lead_verification_status_enum",
)


class Lead(UUIDMixin, TimestampWithUpdateMixin, Base):
    """Task-scoped link between a ScrapingTask and an Organization.

    Allows the same organization to be a distinct lead in multiple tasks,
    each with its own status and verification state.
    """

    __tablename__ = "leads"
    __table_args__ = (
        UniqueConstraint("task_id", "organization_id", name="uq_lead_task_org"),
    )

    # ── Foreign keys ──────────────────────────────────────────────────────────
    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("scraping_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Lead-specific state ───────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        lead_status_enum,
        nullable=False,
        default="ACTIVE",
        server_default="ACTIVE",
    )

    verification_status: Mapped[str] = mapped_column(
        lead_verification_status_enum,
        nullable=False,
        default="PENDING",
        server_default="PENDING",
    )

    # Soft delete
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    task: Mapped[ScrapingTask] = relationship("ScrapingTask", back_populates="leads")
    organization: Mapped[Organization] = relationship("Organization", back_populates="leads")
    verification: Mapped[LeadVerification | None] = relationship(
        "LeadVerification",
        back_populates="lead",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return (
            f"<Lead id={self.id} task_id={self.task_id} "
            f"org_id={self.organization_id} status={self.status}>"
        )
