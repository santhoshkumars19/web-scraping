"""
app/models/contact.py

Contact — a named person or office associated with an Organization.

Table: contacts
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin, TimestampWithUpdateMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.phone_number import PhoneNumber
    from app.models.email_address import EmailAddress


class Contact(UUIDMixin, TimestampWithUpdateMixin, Base):
    """A person or functional office within an Organization.

    Examples:
        name="Ramesh Kumar", designation="Principal"
        name="Admissions Office", designation="Admissions Coordinator"
    """

    __tablename__ = "contacts"

    # ── Ownership ────────────────────────────────────────────────────────────
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Identity ──────────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    designation: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    organization: Mapped[Organization] = relationship(
        "Organization", back_populates="contacts"
    )

    phone_numbers: Mapped[list[PhoneNumber]] = relationship(
        "PhoneNumber",
        back_populates="contact",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    email_addresses: Mapped[list[EmailAddress]] = relationship(
        "EmailAddress",
        back_populates="contact",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Contact id={self.id} name={self.name!r} designation={self.designation!r}>"
