"""
app/jobs/stale_task_job.py

Background detection job for stale or abandoned scraping tasks.
Finds tasks stuck in RUNNING or PENDING longer than TASK_STALE_AFTER_MINUTES
and safely marks them FAILED so they do not hang indefinitely.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.models.scraping_log import ScrapingLog
from app.models.scraping_task import ScrapingTask

logger = get_logger(__name__)


async def detect_and_fail_stale_tasks(
    session: AsyncSession,
    stale_after_minutes: int | None = None,
) -> List[str]:
    """Scan for tasks in RUNNING or PENDING state with no recent activity and mark them FAILED.

    Args:
        session: AsyncSession for database operations.
        stale_after_minutes: Threshold in minutes. Defaults to settings.TASK_STALE_AFTER_MINUTES.

    Returns:
        List of task_id strings that were marked FAILED.
    """
    minutes = (
        stale_after_minutes
        if stale_after_minutes is not None
        else settings.TASK_STALE_AFTER_MINUTES
    )
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    stmt = select(ScrapingTask).where(
        ScrapingTask.status.in_(["RUNNING", "PENDING"]),
        ScrapingTask.updated_at < cutoff,
    )
    res = await session.execute(stmt)
    stale_tasks = list(res.scalars().all())

    if not stale_tasks:
        return []

    failed_task_ids: List[str] = []
    now = datetime.now(timezone.utc)

    for task in stale_tasks:
        logger.warning(
            "Task %s identified as stale (last updated: %s, cutoff: %s). Marking FAILED.",
            task.task_id,
            task.updated_at,
            cutoff,
        )
        task.status = "FAILED"
        task.failure_reason = (
            f"Task exceeded execution timeout: no worker heartbeat or progress for {minutes} minutes."
        )
        task.completed_at = now

        session.add(
            ScrapingLog(
                task_id=task.id,
                level="ERROR",
                event_type="TASK_STALE_TIMEOUT",
                message=f"Task automatically terminated after {minutes}m inactivity threshold.",
            )
        )
        failed_task_ids.append(task.task_id)

    await session.commit()
    logger.info("Marked %d stale tasks as FAILED: %s", len(failed_task_ids), failed_task_ids)
    return failed_task_ids
