"""
app/services/finalization_service.py

Finalization service for Scraping Tasks (Backend Step 9).

Executes final persistence, metric reconciliation, task completion,
and marks status/current_stage = COMPLETED with progress = 100%.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.models.email_address import EmailAddress
from app.models.lead import Lead
from app.models.organization import Organization, task_organizations
from app.models.phone_number import PhoneNumber
from app.models.scraping_log import ScrapingLog
from app.models.scraping_task import ScrapingTask
from app.models.website import Website
from app.repositories.task_repository import TaskRepository

logger = get_logger(__name__)


class TaskFinalizationSummary(BaseModel):
    """Execution summary returned upon task finalization."""

    task_id: str
    status: str
    current_stage: str
    progress: int
    results_discovered: int
    verified_count: int
    high_confidence_count: int
    medium_confidence_count: int
    low_confidence_count: int
    completed_at: datetime | None = None
    duration_seconds: float = 0.0


class FinalizationService:
    """Service to reconcile final counts and complete scraping tasks."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = TaskRepository(session)

    async def finalize_task(self, task_id: str | uuid.UUID) -> TaskFinalizationSummary:
        """Perform final metric reconciliation and transition task to COMPLETED.

        Args:
            task_id: Human-readable task ID (e.g. "TASK-000124") or UUID.

        Returns:
            TaskFinalizationSummary with reconciled metrics.
        """
        start_time = time.monotonic()

        # ── 1. Resolve Task ───────────────────────────────────────────────────
        task: ScrapingTask | None = None
        if isinstance(task_id, uuid.UUID):
            task = await self.repository.get_by_id(task_id)
        elif isinstance(task_id, str):
            if task_id.startswith("TASK-"):
                task = await self.repository.get_by_task_id(task_id)
            else:
                try:
                    uid = uuid.UUID(task_id)
                    task = await self.repository.get_by_id(uid)
                except ValueError:
                    task = await self.repository.get_by_task_id(task_id)

        if task is None:
            raise AppException(
                message="Scraping task not found.",
                status_code=404,
                code="TASK_NOT_FOUND",
            )

        # ── 2. Guard Terminal States ──────────────────────────────────────────
        if task.status in ("CANCELLED", "FAILED"):
            logger.info(
                "Task %s is already in terminal status %s; skipping finalization.",
                task.task_id,
                task.status,
            )
            return TaskFinalizationSummary(
                task_id=task.task_id,
                status=task.status,
                current_stage=task.current_stage,
                progress=task.progress,
                results_discovered=task.results_discovered,
                verified_count=task.verified_count,
                high_confidence_count=task.high_confidence_count,
                medium_confidence_count=task.medium_confidence_count,
                low_confidence_count=task.low_confidence_count,
                completed_at=task.completed_at,
            )

        # ── 3. Reconcile Final Metrics ────────────────────────────────────────
        # Query task organization IDs
        stmt_org_ids = (
            select(task_organizations.c.organization_id)
            .where(task_organizations.c.task_id == task.id)
        )
        task_org_ids = list((await self.session.execute(stmt_org_ids)).scalars().all())

        if task_org_ids:
            # Count websites
            stmt_web = (
                select(func.count(Website.id))
                .where(Website.organization_id.in_(task_org_ids))
            )
            web_count = (await self.session.execute(stmt_web)).scalar() or 0
            if web_count > task.websites_found:
                task.websites_found = web_count

            # Count phone numbers
            stmt_phone = (
                select(func.count(PhoneNumber.id))
                .where(PhoneNumber.organization_id.in_(task_org_ids))
            )
            phone_count = (await self.session.execute(stmt_phone)).scalar() or 0
            task.phones_found = phone_count

            # Count email addresses
            stmt_email = (
                select(func.count(EmailAddress.id))
                .where(EmailAddress.organization_id.in_(task_org_ids))
            )
            email_count = (await self.session.execute(stmt_email)).scalar() or 0
            task.emails_found = email_count

            # Count organizations with address/pincode
            stmt_addr = (
                select(func.count(Organization.id))
                .where(
                    Organization.id.in_(task_org_ids),
                    (Organization.address.isnot(None)) | (Organization.pincode.isnot(None)),
                )
            )
            addr_count = (await self.session.execute(stmt_addr)).scalar() or 0
            task.addresses_found = addr_count

            task.results_discovered = len(task_org_ids)

        # Reconcile lead verification counts
        stmt_leads = select(Lead).where(Lead.task_id == task.id)
        leads = list((await self.session.execute(stmt_leads)).scalars().all())

        verified = 0
        high = 0
        med = 0
        low = 0
        for l in leads:
            if l.verification_status in ("HIGH", "MEDIUM", "LOW"):
                verified += 1
                if l.verification_status == "HIGH":
                    high += 1
                elif l.verification_status == "MEDIUM":
                    med += 1
                else:
                    low += 1

        task.verified_count = verified
        task.high_confidence_count = high
        task.medium_confidence_count = med
        task.low_confidence_count = low

        # ── 4. Set Completion State ───────────────────────────────────────────
        now = datetime.now(timezone.utc)
        task.current_stage = "COMPLETED"
        task.status = "COMPLETED"
        task.progress = 100
        task.completed_at = now
        task.failure_reason = None

        duration = time.monotonic() - start_time
        total_runtime = 0.0
        if task.started_at:
            started = task.started_at
            if started.tzinfo is None:
                started = started.replace(tzinfo=timezone.utc)
            total_runtime = max(0.0, (now - started).total_seconds())

        self.session.add(
            ScrapingLog(
                task_id=task.id,
                level="INFO",
                event_type="PIPELINE_COMPLETED",
                message=(
                    f"Scraping pipeline for {task.task_id} completed successfully. "
                    f"Organizations discovered: {task.results_discovered}, "
                    f"verified leads: {task.verified_count} "
                    f"({task.high_confidence_count} HIGH, {task.medium_confidence_count} MEDIUM, "
                    f"{task.low_confidence_count} LOW). Total run time: {total_runtime:.2f}s."
                ),
            )
        )
        await self.session.commit()

        try:
            from app.realtime.events import extract_task_metrics
            from app.realtime.publisher import get_event_publisher
            await get_event_publisher().publish_completed(
                task.task_id,
                metrics=extract_task_metrics(task),
            )
        except Exception as pe:
            logger.debug("Realtime publish failed for task %s completed event: %s", task.task_id, pe)

        logger.info(
            "Task %s finalized: status=COMPLETED, progress=100%%, verified=%d",
            task.task_id,
            task.verified_count,
        )

        return TaskFinalizationSummary(
            task_id=task.task_id,
            status=task.status,
            current_stage=task.current_stage,
            progress=task.progress,
            results_discovered=task.results_discovered,
            verified_count=task.verified_count,
            high_confidence_count=task.high_confidence_count,
            medium_confidence_count=task.medium_confidence_count,
            low_confidence_count=task.low_confidence_count,
            completed_at=task.completed_at,
            duration_seconds=round(duration, 3),
        )
