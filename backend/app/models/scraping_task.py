"""
app/models/scraping_task.py

ScrapingTask — a user-initiated web scraping job.

Table: scraping_tasks
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin, TimestampWithUpdateMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.lead import Lead
    from app.models.scraping_log import ScrapingLog
    from app.models.source_page import SourcePage
    from app.models.organization import Organization


# ── Enums ─────────────────────────────────────────────────────────────────────

task_status_enum = SAEnum(
    "PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED",
    name="task_status_enum",
)

task_stage_enum = SAEnum(
    "CREATING_TASK", "DISCOVERING", "FINDING_WEBSITES",
    "CRAWLING", "EXTRACTING", "CLEANING", "DEDUPLICATING",
    "VERIFYING", "SAVING", "COMPLETED",
    name="task_stage_enum",
)


class ScrapingTask(UUIDMixin, TimestampWithUpdateMixin, Base):
    """A single scraping job submitted by a user."""

    __tablename__ = "scraping_tasks"
    __table_args__ = (
        CheckConstraint("progress >= 0 AND progress <= 100", name="ck_task_progress_range"),
    )

    # ── Human-readable identifier ─────────────────────────────────────────────
    task_id: Mapped[str] = mapped_column(
        String(32), nullable=False, unique=True, index=True
    )

    # ── Ownership ────────────────────────────────────────────────────────────
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Search parameters ─────────────────────────────────────────────────────
    location: Mapped[str] = mapped_column(String(500), nullable=False)
    keyword: Mapped[str] = mapped_column(String(500), nullable=False)
    search_radius: Mapped[int] = mapped_column(Integer, nullable=False, default=25)
    max_results: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    max_pages_per_site: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    crawl_depth: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    selected_fields: Mapped[list[str] | None] = mapped_column(sa.JSON, nullable=True, default=list)

    # ── Crawl strategy flags ──────────────────────────────────────────────────
    follow_internal_links: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=sa.true()
    )
    prioritize_contact: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=sa.true()
    )
    prioritize_about: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=sa.true()
    )
    prioritize_admissions: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=sa.false()
    )
    prioritize_staff_management: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=sa.false()
    )

    # ── Status & progress ─────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        task_status_enum,
        nullable=False,
        default="PENDING",
        server_default="PENDING",
        index=True,
    )

    current_stage: Mapped[str] = mapped_column(
        task_stage_enum,
        nullable=False,
        default="CREATING_TASK",
        server_default="CREATING_TASK",
    )

    progress: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    # ── Metrics ───────────────────────────────────────────────────────────────
    results_discovered: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    websites_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    websites_crawled: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    phones_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    emails_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    addresses_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    duplicates_removed: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    failed_websites: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    verified_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    high_confidence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    medium_confidence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    low_confidence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    # ── Lifecycle timestamps ──────────────────────────────────────────────────
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Failure tracking ──────────────────────────────────────────────────────
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Background Worker Tracking (Step 9) ──────────────────────────────────
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    user: Mapped[User] = relationship("User", back_populates="tasks")

    leads: Mapped[list[Lead]] = relationship(
        "Lead",
        back_populates="task",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    logs: Mapped[list[ScrapingLog]] = relationship(
        "ScrapingLog",
        back_populates="task",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    source_pages: Mapped[list[SourcePage]] = relationship(
        "SourcePage",
        back_populates="task",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    # many-to-many via task_organizations
    organizations: Mapped[list[Organization]] = relationship(
        "Organization",
        secondary="task_organizations",
        back_populates="tasks",
        passive_deletes=True,
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<ScrapingTask task_id={self.task_id!r} status={self.status}>"
