"""
app/services/task_service.py

Business logic and workflow orchestration for Scraping Tasks.
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException, ValidationError
from app.core.logging import get_logger
from app.models.scraping_task import ScrapingTask
from app.models.user import User
from app.repositories.task_repository import SORT_COLUMNS, TaskRepository
from app.schemas.task import ScrapingTaskCreate
from app.utils.task_id import generate_task_id

import asyncio

logger = get_logger(__name__)

DEMO_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
DEMO_USER_EMAIL = "demo@leadscout.app"
_demo_user_lock = asyncio.Lock()


class TaskService:
    """Service handling scraping task creation, retrieval, and status tracking."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = TaskRepository(session)

    async def _get_or_create_demo_user(self) -> uuid.UUID:
        """Ensure a valid user exists for associating tasks in development."""
        async with _demo_user_lock:
            stmt = select(User).where(User.id == DEMO_USER_ID)
            result = await self.session.execute(stmt)
            user = result.scalar_one_or_none()

            if user is None:
                stmt_email = select(User).where(User.email == DEMO_USER_EMAIL)
                result_email = await self.session.execute(stmt_email)
                user = result_email.scalar_one_or_none()

            if user is None:
                try:
                    user = User(
                        id=DEMO_USER_ID,
                        name="Demo Scout",
                        email=DEMO_USER_EMAIL,
                        password_hash="$2b$12$demo_placeholder_hash",
                        role="USER",
                        is_active=True,
                    )
                    self.session.add(user)
                    await self.session.flush()
                except Exception:
                    await self.session.rollback()
                    stmt_retry = select(User).where(
                        (User.id == DEMO_USER_ID) | (User.email == DEMO_USER_EMAIL)
                    )
                    result_retry = await self.session.execute(stmt_retry)
                    user = result_retry.scalar_one()

            return user.id

    async def create_task(
        self,
        data: ScrapingTaskCreate,
        user_id: uuid.UUID | None = None,
    ) -> ScrapingTask:
        """Create and persist a new scraping task in PENDING state.

        Steps:
          1. Ensure user identity (assigned from authenticated user, or demo user fallback).
          2. Concurrency-safe task ID generation (TASK-XXXXXX).
          3. Instantiate ScrapingTask in initial state.
          4. Persist and commit transaction.
          5. Log creation event.
        """
        if user_id is None:
            user_id = await self._get_or_create_demo_user()
        task_id = await generate_task_id(self.session)

        task = ScrapingTask(
            task_id=task_id,
            user_id=user_id,
            location=data.location,
            keyword=data.keyword,
            search_radius=data.search_radius,
            max_results=data.max_results,
            max_pages_per_site=data.max_pages_per_site,
            crawl_depth=data.crawl_depth,
            selected_fields=data.selected_fields,
            follow_internal_links=data.follow_internal_links,
            prioritize_contact=data.prioritize_contact,
            prioritize_about=data.prioritize_about,
            prioritize_admissions=data.prioritize_admissions,
            prioritize_staff_management=data.prioritize_staff_management,
            status="PENDING",
            current_stage="CREATING_TASK",
            progress=0,
            results_discovered=0,
            websites_found=0,
            websites_crawled=0,
            phones_found=0,
            emails_found=0,
            addresses_found=0,
            duplicates_removed=0,
            failed_websites=0,
            started_at=None,
            completed_at=None,
            failure_reason=None,
        )

        await self.repository.create(task)
        await self.session.commit()

        logger.info("Scraping task created: %s (user=%s)", task.task_id, user_id)
        return task

    async def get_task(
        self,
        task_id: str,
        user_id: uuid.UUID | None = None,
    ) -> ScrapingTask:
        """Retrieve a task by its task_id (optionally scoped to user) or raise a 404 AppException."""
        task = await self.repository.get_by_task_id(task_id, user_id=user_id)
        if task is None:
            raise AppException(
                message="Scraping task not found.",
                status_code=404,
                code="TASK_NOT_FOUND",
            )
        return task

    async def list_tasks(
        self,
        *,
        user_id: uuid.UUID | None = None,
        page: int = 1,
        limit: int = 20,
        status: str | None = None,
        location: str | None = None,
        keyword: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[ScrapingTask], int, int]:
        """List tasks with filtering, sorting, and pagination.

        Returns:
            Tuple of (tasks_list, total_count, total_pages).
        """
        if sort_by not in SORT_COLUMNS:
            raise ValidationError(
                f"Invalid sort_by field '{sort_by}'. Allowed: {sorted(list(SORT_COLUMNS.keys()))}"
            )
        if sort_order.lower() not in {"asc", "desc"}:
            raise ValidationError("Invalid sort_order. Allowed: 'asc', 'desc'")

        tasks, total = await self.repository.list_tasks(
            user_id=user_id,
            page=page,
            limit=limit,
            status=status,
            location=location,
            keyword=keyword,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        total_pages = math.ceil(total / limit) if total > 0 else 0
        return list(tasks), total, total_pages

    # ── Internal status / progress updates (for future worker use) ───────────

    async def start_task(self, task_id: str) -> ScrapingTask:
        """Mark a task as actively running."""
        task = await self.get_task(task_id)
        task.status = "RUNNING"
        task.current_stage = "DISCOVERING"
        task.started_at = datetime.now(timezone.utc)
        await self.repository.update(task)
        await self.session.commit()
        logger.info("Task %s started", task_id)
        return task

    async def complete_task(self, task_id: str) -> ScrapingTask:
        """Mark a task as successfully completed."""
        task = await self.get_task(task_id)
        task.status = "COMPLETED"
        task.current_stage = "COMPLETED"
        task.progress = 100
        task.completed_at = datetime.now(timezone.utc)
        await self.repository.update(task)
        await self.session.commit()
        logger.info("Task %s completed", task_id)
        return task

    async def fail_task(self, task_id: str, reason: str) -> ScrapingTask:
        """Mark a task as failed with an explanation."""
        task = await self.get_task(task_id)
        task.status = "FAILED"
        task.completed_at = datetime.now(timezone.utc)
        task.failure_reason = reason
        await self.repository.update(task)
        await self.session.commit()
        logger.warning("Task %s failed: %s", task_id, reason)
        return task

    async def cancel_task(self, task_id: str) -> ScrapingTask:
        """Cancel an in-progress or pending task."""
        task = await self.get_task(task_id)
        task.status = "CANCELLED"
        task.completed_at = datetime.now(timezone.utc)
        await self.repository.update(task)
        await self.session.commit()
        logger.info("Task %s cancelled", task_id)
        return task

    async def update_progress(self, task_id: str, progress: int) -> ScrapingTask:
        """Update progress percent (0–100)."""
        if not (0 <= progress <= 100):
            raise ValidationError("Progress must be between 0 and 100.")
        task = await self.get_task(task_id)
        task.progress = progress
        await self.repository.update(task)
        await self.session.commit()
        return task

    async def update_stage(self, task_id: str, stage: str) -> ScrapingTask:
        """Update current processing stage."""
        task = await self.get_task(task_id)
        task.current_stage = stage
        await self.repository.update(task)
        await self.session.commit()
        return task
