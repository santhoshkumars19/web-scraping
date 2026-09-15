"""
app/services/task_progress_service.py

Centralized task progress and state management service.
Validates stages and monotonic progress, updates PostgreSQL, commits transactions,
and publishes real-time WebSocket events via Redis Pub/Sub with failure isolation.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppException, ValidationError
from app.core.logging import get_logger
from app.models.scraping_task import ScrapingTask
from app.realtime.events import (
    EventType,
    build_activity_event,
    build_cancelled_event,
    build_completed_event,
    build_failed_event,
    build_progress_event,
    build_stage_changed_event,
    build_started_event,
    extract_task_metrics,
)
from app.realtime.publisher import get_event_publisher
from app.repositories.task_repository import TaskRepository

logger = get_logger(__name__)

VALID_STAGES: set[str] = {
    "CREATING_TASK",
    "DISCOVERING",
    "FINDING_WEBSITES",
    "CRAWLING",
    "EXTRACTING",
    "CLEANING",
    "DEDUPLICATING",
    "VERIFYING",
    "SAVING",
    "COMPLETED",
}

VALID_STATUSES: set[str] = {
    "PENDING",
    "RUNNING",
    "COMPLETED",
    "FAILED",
    "CANCELLED",
}

METRIC_FIELDS: set[str] = {
    "results_discovered",
    "websites_found",
    "websites_crawled",
    "phones_found",
    "emails_found",
    "addresses_found",
    "duplicates_removed",
    "failed_websites",
    "verified_count",
    "high_confidence_count",
    "medium_confidence_count",
    "low_confidence_count",
}

# In-memory throttle tracker: task_id -> (last_published_time, last_published_progress)
_last_published: dict[str, tuple[float, int]] = {}


class TaskProgressService:
    """Authoritative service for task status, stage, progress, and real-time event updates."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = TaskRepository(session)

    @classmethod
    def reset_throttle_cache(cls) -> None:
        """Reset the throttle cache (useful for tests)."""
        _last_published.clear()

    async def update(
        self,
        task_id: str,
        *,
        status: str | None = None,
        stage: str | None = None,
        progress: int | None = None,
        metrics: dict[str, int] | None = None,
        event_type: str | None = None,
        activity_message: str | None = None,
        failure_reason: str | None = None,
        allow_regression: bool = False,
        force_publish: bool = False,
    ) -> ScrapingTask:
        """Update task state in PostgreSQL and publish real-time notifications.

        Guarantees:
          1. Validation of stage and progress range [0, 100].
          2. Enforces progress monotonicity (no regressions during normal flow).
          3. Terminal state protection (no updates after COMPLETED/FAILED/CANCELLED).
          4. Database transaction committed before publishing.
          5. Failure isolation: Redis publish error does not roll back committed data.
        """
        task = await self.repository.get_by_task_id(task_id)
        if not task:
            raise AppException(
                message=f"Scraping task '{task_id}' not found.",
                status_code=404,
                code="TASK_NOT_FOUND",
            )

        # ── 1. Terminal State Protection ─────────────────────────────────────
        if task.status in {"COMPLETED", "FAILED", "CANCELLED"}:
            if status is None or status == task.status:
                logger.warning(
                    "Task %s is in terminal state '%s'; ignoring update (stage=%s, progress=%s).",
                    task_id,
                    task.status,
                    stage,
                    progress,
                )
                return task

        # ── 2. Stage Validation ──────────────────────────────────────────────
        previous_stage = task.current_stage
        if stage is not None:
            if stage not in VALID_STAGES:
                raise ValidationError(
                    f"Invalid stage '{stage}'. Allowed stages: {sorted(list(VALID_STAGES))}"
                )
            task.current_stage = stage

        # ── 3. Status Validation ─────────────────────────────────────────────
        previous_status = task.status
        if status is not None:
            if status not in VALID_STATUSES:
                raise ValidationError(
                    f"Invalid status '{status}'. Allowed statuses: {sorted(list(VALID_STATUSES))}"
                )
            task.status = status

            now = datetime.now(timezone.utc)
            if status == "RUNNING" and not task.started_at:
                task.started_at = now
            elif status in {"COMPLETED", "FAILED", "CANCELLED"} and not task.completed_at:
                task.completed_at = now

        if failure_reason is not None:
            task.failure_reason = failure_reason

        # ── 4. Progress Validation & Monotonicity ─────────────────────────────
        previous_progress = task.progress
        if progress is not None:
            if not (0 <= progress <= 100):
                raise ValidationError(f"Progress must be between 0 and 100, got {progress}.")

            if progress < task.progress and not allow_regression:
                logger.info(
                    "Progress regression ignored for task %s (current: %d, proposed: %d)",
                    task_id,
                    task.progress,
                    progress,
                )
                # Keep current progress
            else:
                task.progress = progress

        # ── 5. Metrics Update ────────────────────────────────────────────────
        if metrics:
            for field, val in metrics.items():
                if field in METRIC_FIELDS and hasattr(task, field):
                    setattr(task, field, val)

        # ── 6. Database Commit ───────────────────────────────────────────────
        await self.repository.update(task)
        await self.session.commit()

        # ── 7. Build and Publish Event ───────────────────────────────────────
        current_metrics = extract_task_metrics(task)
        now_ts = time.time()
        last_time, last_prog = _last_published.get(task_id, (0.0, -1))
        throttle_interval = settings.REALTIME_EVENT_THROTTLE_MS / 1000.0

        is_critical_event = (
            force_publish
            or (status is not None and status != previous_status)
            or (stage is not None and stage != previous_stage)
            or (task.status in {"COMPLETED", "FAILED", "CANCELLED"})
            or (activity_message is not None)
            or (event_type is not None)
        )

        should_publish = is_critical_event or (
            (now_ts - last_time >= throttle_interval)
            and (abs(task.progress - last_prog) >= 1)
        )

        if should_publish:
            event: dict[str, Any]
            if event_type == EventType.STARTED.value or (task.status == "RUNNING" and previous_status == "PENDING"):
                event = build_started_event(
                    task_id,
                    stage=task.current_stage,
                    progress=task.progress,
                    metrics=current_metrics,
                )
            elif event_type == EventType.COMPLETED.value or task.status == "COMPLETED":
                event = build_completed_event(task_id, metrics=current_metrics)
            elif event_type == EventType.FAILED.value or task.status == "FAILED":
                event = build_failed_event(
                    task_id,
                    stage=task.current_stage,
                    reason=task.failure_reason or "Unknown error",
                )
            elif event_type == EventType.CANCELLED.value or task.status == "CANCELLED":
                event = build_cancelled_event(
                    task_id,
                    stage=task.current_stage,
                    progress=task.progress,
                )
            elif activity_message:
                event = build_activity_event(
                    task_id,
                    message=activity_message,
                    stage=task.current_stage,
                )
            elif stage is not None and stage != previous_stage:
                event = build_stage_changed_event(
                    task_id,
                    stage=task.current_stage,
                    progress=task.progress,
                    status=task.status,
                    metrics=current_metrics,
                )
            else:
                event = build_progress_event(
                    task_id,
                    progress=task.progress,
                    stage=task.current_stage,
                    status=task.status,
                    metrics=current_metrics,
                )

            publisher = get_event_publisher()
            try:
                await publisher.publish_event(task_id, event)
                _last_published[task_id] = (now_ts, task.progress)
            except Exception as exc:
                # Failure isolation: Do NOT let realtime publish error affect database state
                logger.warning(
                    "REALTIME_PUBLISH_FAILED: Error publishing event for task %s: %s",
                    task_id,
                    exc,
                )

        return task
