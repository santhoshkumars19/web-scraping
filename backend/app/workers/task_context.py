"""
app/workers/task_context.py

Execution bridge between synchronous Celery workers and async domain services.
Manages database sessions, task lifecycle transitions, cancellation checks,
and pipeline stage logging.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
from collections.abc import Callable, Coroutine
from datetime import datetime, timezone
from typing import Any, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.db.database import create_engine_and_factory, get_session_factory
from app.models.scraping_log import ScrapingLog
from app.models.scraping_task import ScrapingTask
from app.repositories.task_repository import TaskRepository

logger = get_logger(__name__)

T = TypeVar("T")


class TaskCancelledException(Exception):
    """Raised when a task has been cancelled and downstream stages must halt."""
    pass


class TaskAlreadyFailedException(Exception):
    """Raised when a task has already failed and downstream stages must halt."""
    pass


def run_async(coro_fn: Callable[..., Coroutine[Any, Any, T]], *args: Any, **kwargs: Any) -> T:
    """Execute an async coroutine safely from a synchronous context.

    Handles existing running event loops (e.g. eager tests) via a background thread.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro_fn(*args, **kwargs)).result()
    else:
        return asyncio.run(coro_fn(*args, **kwargs))


async def _execute_stage_in_session(
    async_stage_fn: Callable[[str, AsyncSession], Coroutine[Any, Any, Any]],
    task_id: str,
    stage_name: str,
) -> dict[str, Any]:
    """Internal async runner executing a pipeline stage within an isolated DB session."""
    try:
        factory = get_session_factory()
    except RuntimeError:
        create_engine_and_factory()
        factory = get_session_factory()

    async with factory() as session:
        repo = TaskRepository(session)
        task = await repo.get_by_task_id(task_id)
        if not task:
            raise AppException(
                message=f"Scraping task '{task_id}' not found.",
                status_code=404,
                code="TASK_NOT_FOUND",
            )

        # ── 1. Check Cancellation or Prior Failure ────────────────────────────
        if task.status == "CANCELLED":
            session.add(
                ScrapingLog(
                    task_id=task.id,
                    level="WARNING",
                    event_type="PIPELINE_CANCELLED",
                    message=f"Pipeline cancelled. Halting before stage '{stage_name}'.",
                )
            )
            await session.commit()
            try:
                from app.realtime.publisher import get_event_publisher
                await get_event_publisher().publish_cancelled(task_id, stage=stage_name, progress=task.progress)
            except Exception as pe:
                logger.debug("Realtime publish failed for task %s cancelled event: %s", task_id, pe)
            raise TaskCancelledException(f"Task '{task_id}' was cancelled.")

        if task.status == "FAILED":
            logger.warning("Task %s already failed; skipping stage '%s'.", task_id, stage_name)
            raise TaskAlreadyFailedException(f"Task '{task_id}' has already failed.")

        # ── 2. Mark Started Timestamp & Status (First Stage) ──────────────────
        if task.status == "PENDING":
            task.status = "RUNNING"
            task.started_at = datetime.now(timezone.utc)
            session.add(
                ScrapingLog(
                    task_id=task.id,
                    level="INFO",
                    event_type="PIPELINE_STARTED",
                    message=f"Pipeline worker started execution for task {task_id}.",
                )
            )
            try:
                from app.realtime.publisher import get_event_publisher
                await get_event_publisher().publish_started(task_id, stage=stage_name, progress=task.progress)
            except Exception as pe:
                logger.debug("Realtime publish failed for task %s started event: %s", task_id, pe)

        # ── 3. Stage Started Log & Realtime Event ─────────────────────────────
        session.add(
            ScrapingLog(
                task_id=task.id,
                level="INFO",
                event_type="PIPELINE_STAGE_STARTED",
                message=f"Pipeline stage '{stage_name}' started for task {task_id}.",
            )
        )
        await session.commit()

        try:
            from app.realtime.publisher import get_event_publisher
            await get_event_publisher().publish_stage_changed(
                task_id,
                stage=stage_name,
                progress=task.progress,
                status=task.status,
            )
        except Exception as pe:
            logger.debug("Realtime publish failed for task %s stage_changed event: %s", task_id, pe)

        # ── 4. Execute the Service/Job Stage ──────────────────────────────────
        try:
            result = await async_stage_fn(task_id, session=session)
        except Exception as exc:
            logger.error(
                "Stage '%s' failed for task %s: %s",
                stage_name,
                task_id,
                exc,
                exc_info=True,
            )
            task.status = "FAILED"
            task.failure_reason = f"Stage '{stage_name}' failed: {exc}"
            session.add(
                ScrapingLog(
                    task_id=task.id,
                    level="ERROR",
                    event_type="PIPELINE_STAGE_FAILED",
                    message=f"Pipeline stage '{stage_name}' failed for task {task_id}: {exc}",
                )
            )
            await session.commit()
            try:
                from app.realtime.publisher import get_event_publisher
                await get_event_publisher().publish_failed(
                    task_id,
                    stage=stage_name,
                    reason=f"Stage '{stage_name}' failed: {exc}",
                )
            except Exception as pe:
                logger.debug("Realtime publish failed for task %s failed event: %s", task_id, pe)
            raise

        # ── 5. Stage Completed Log ────────────────────────────────────────────
        session.add(
            ScrapingLog(
                task_id=task.id,
                level="INFO",
                event_type="PIPELINE_STAGE_COMPLETED",
                message=f"Pipeline stage '{stage_name}' completed for task {task_id}.",
            )
        )
        await session.commit()

        # Convert result object or pydantic model to dictionary
        result_dict: dict[str, Any]
        if hasattr(result, "model_dump"):
            result_dict = result.model_dump()
        elif hasattr(result, "__dict__"):
            result_dict = {
                k: v for k, v in result.__dict__.items() if not k.startswith("_")
            }
        else:
            result_dict = {"raw": str(result)}

        return {
            "task_id": task_id,
            "stage": stage_name,
            "status": "COMPLETED",
            "data": result_dict,
        }


def run_worker_stage(
    async_stage_fn: Callable[[str, AsyncSession], Coroutine[Any, Any, Any]],
    task_id: str,
    stage_name: str,
) -> dict[str, Any]:
    """Synchronous entrypoint called by Celery tasks to execute an async stage."""
    return run_async(_execute_stage_in_session, async_stage_fn, task_id, stage_name)
