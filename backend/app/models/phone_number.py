"""
app/models/phone_number.py

PhoneNumber — a phone number for an Organization or Contact.

Stored as text (never integer). Original display value and
normalized E.164-style value kept separately.

Table: phone_numbers
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


phone_type_enum = SAEnum(
    "MAIN", "ALTERNATE", "OFFICE", "ADMISSIONS",
    "LANDLINE", "WHATSAPP", "OTHER",
    name="phone_type_enum",
)


class PhoneNumber(UUIDMixin, TimestampWithUpdateMixin, Base):
    """A phone number linked to an organization (and optionally a contact)."""

    __tablename__ = "phone_numbers"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "normalized_phone",
            name="uq_phone_org_normalized",
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

    # ── Number data ───────────────────────────────────────────────────────────
    # Stored as strings — never as integers.
    phone_number: Mapped[str] = mapped_column(String(50), nullable=False)
    normalized_phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    phone_type: Mapped[str] = mapped_column(
        phone_type_enum,
        nullable=False,
        default="MAIN",
        server_default="MAIN",
    )

    is_whatsapp: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=sa.false()
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=sa.false()
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    organization: Mapped[Organization] = relationship(
        "Organization", back_populates="phone_numbers"
    )
    contact: Mapped[Contact | None] = relationship(
        "Contact", back_populates="phone_numbers"
    )

    def __repr__(self) -> str:
        return (
            f"<PhoneNumber id={self.id} phone={self.phone_number!r} "
            f"type={self.phone_type} whatsapp={self.is_whatsapp}>"
        )
