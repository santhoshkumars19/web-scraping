"""
app/models/scraping_log.py

ScrapingLog — structured event log for scraping tasks.

Table: scraping_logs
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.scraping_task import ScrapingTask
    from app.models.organization import Organization
    from app.models.website import Website


log_level_enum = SAEnum(
    "INFO", "WARNING", "ERROR",
    name="log_level_enum",
)


class ScrapingLog(UUIDMixin, TimestampMixin, Base):
    """Event log record for monitoring scraping pipeline activity.

    Immutable once written (TimestampMixin). Does not log credentials or secrets.
    """

    __tablename__ = "scraping_logs"
    __table_args__ = (
        sa.Index("ix_scraping_logs_task_created", "task_id", "created_at"),
        sa.Index("ix_scraping_logs_level", "level"),
        sa.Index("ix_scraping_logs_event_type", "event_type"),
    )

    # ── Foreign keys ──────────────────────────────────────────────────────────
    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("scraping_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    website_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("websites.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Log content ───────────────────────────────────────────────────────────
    level: Mapped[str] = mapped_column(
        log_level_enum,
        nullable=False,
        default="INFO",
        server_default="INFO",
    )

    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    message: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    task: Mapped[ScrapingTask] = relationship("ScrapingTask", back_populates="logs")
    organization: Mapped[Organization | None] = relationship("Organization")
    website: Mapped[Website | None] = relationship("Website")

    def __repr__(self) -> str:
        return (
            f"<ScrapingLog id={self.id} task_id={self.task_id} "
            f"level={self.level} event={self.event_type}>"
        )
