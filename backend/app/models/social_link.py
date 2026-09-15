"""
app/models/social_link.py

SocialLink — a social media profile link belonging to an Organization.

Table: social_links
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization


social_platform_enum = SAEnum(
    "FACEBOOK", "INSTAGRAM", "LINKEDIN", "TWITTER", "YOUTUBE", "OTHER",
    name="social_platform_enum",
)


class SocialLink(UUIDMixin, TimestampMixin, Base):
    """A public social profile link for an Organization."""

    __tablename__ = "social_links"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "normalized_url",
            name="uq_social_link_org_normalized",
        ),
        sa.Index("ix_social_links_org_platform", "organization_id", "platform"),
    )

    # ── Ownership ────────────────────────────────────────────────────────────
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Platform & URL ────────────────────────────────────────────────────────
    platform: Mapped[str] = mapped_column(
        social_platform_enum,
        nullable=False,
        default="OTHER",
        server_default="OTHER",
    )

    url: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_url: Mapped[str] = mapped_column(Text, nullable=False, index=True)

    is_official: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=sa.false()
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    organization: Mapped[Organization] = relationship(
        "Organization", back_populates="social_links"
    )

    def __repr__(self) -> str:
        return f"<SocialLink id={self.id} platform={self.platform} url={self.url[:50]!r}>"
