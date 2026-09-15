"""
app/models/organization_merge_event.py

OrganizationMergeEvent — audit log for organization merge operations.

Table: organization_merge_events
"""

from __future__ import annotations

import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class OrganizationMergeEvent(UUIDMixin, TimestampMixin, Base):
    """Audit record capturing an organization deduplication merge operation.

    Tracks which source organization was merged into which canonical target organization,
    along with the numerical match score and evidence list.
    """

    __tablename__ = "organization_merge_events"
    __table_args__ = (
        sa.Index("ix_org_merge_source", "source_organization_id"),
        sa.Index("ix_org_merge_target", "target_organization_id"),
    )

    source_organization_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid,
        nullable=False,
        index=True,
    )

    target_organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    match_score: Mapped[int] = mapped_column(Integer, nullable=False)

    match_reasons: Mapped[list[str]] = mapped_column(
        sa.JSON,
        nullable=False,
        default=list,
    )

    def __repr__(self) -> str:
        return (
            f"<OrganizationMergeEvent id={self.id} "
            f"source={self.source_organization_id} target={self.target_organization_id} "
            f"score={self.match_score}>"
        )
