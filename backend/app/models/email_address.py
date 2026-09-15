"""
app/models/email_address.py

EmailAddress — an email for an Organization or Contact.

Table: email_addresses
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin, TimestampWithUpdateMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.contact import Contact


email_type_enum = SAEnum(
    "GENERAL", "CONTACT", "ADMISSIONS", "MANAGEMENT", "OTHER",
    name="email_type_enum",
)


class EmailAddress(UUIDMixin, TimestampWithUpdateMixin, Base):
    """An email address linked to an organization (and optionally a contact)."""

    __tablename__ = "email_addresses"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "normalized_email",
            name="uq_email_org_normalized",
        ),
    )

    # ── Ownership ────────────────────────────────────────────────────────────
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("contacts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Email data ────────────────────────────────────────────────────────────
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    normalized_email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)

    email_type: Mapped[str] = mapped_column(
        email_type_enum,
        nullable=False,
        default="GENERAL",
        server_default="GENERAL",
    )

    is_primary: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=sa.false()
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    organization: Mapped[Organization] = relationship(
        "Organization", back_populates="email_addresses"
    )
    contact: Mapped[Contact | None] = relationship(
        "Contact", back_populates="email_addresses"
    )

    def __repr__(self) -> str:
        return (
            f"<EmailAddress id={self.id} email={self.email!r} "
            f"type={self.email_type} primary={self.is_primary}>"
        )
