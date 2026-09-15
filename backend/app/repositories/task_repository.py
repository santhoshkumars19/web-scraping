"""
app/repositories/task_repository.py

Data access layer for ScrapingTask entities.
"""

from __future__ import annotations

import math
from typing import Sequence

import sqlalchemy as sa
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scraping_task import ScrapingTask


SORT_COLUMNS = {
    "created_at": ScrapingTask.created_at,
    "keyword": ScrapingTask.keyword,
    "location": ScrapingTask.location,
    "status": ScrapingTask.status,
    "progress": ScrapingTask.progress,
}


class TaskRepository:
    """Encapsulates all database operations for ScrapingTask."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, task: ScrapingTask) -> ScrapingTask:
        """Add a new task to the session and flush to generate default values."""
        self.session.add(task)
        await self.session.flush()
        return task

    async def get_by_task_id(
        self,
        task_id: str,
        user_id: uuid.UUID | None = None,
    ) -> ScrapingTask | None:
        """Retrieve a task by its user-facing human-readable ID, optionally scoped to user."""
        stmt = select(ScrapingTask).where(ScrapingTask.task_id == task_id)
        if user_id is not None:
            stmt = stmt.where(ScrapingTask.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

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
    ) -> tuple[Sequence[ScrapingTask], int]:
        """Query tasks with database-level filtering, sorting, and pagination.

        Returns:
            Tuple of (list_of_tasks, total_matching_records).
        """
        stmt = select(ScrapingTask)
        count_stmt = select(func.count()).select_from(ScrapingTask)

        # ── Filters ───────────────────────────────────────────────────────────
        filters = []
        if user_id is not None:
            filters.append(ScrapingTask.user_id == user_id)
        if status:
            filters.append(ScrapingTask.status == status.upper())
        if location:
            filters.append(ScrapingTask.location.ilike(f"%{location}%"))
        if keyword:
            filters.append(ScrapingTask.keyword.ilike(f"%{keyword}%"))

        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        # ── Total count (prior to limit/offset) ────────────────────────────────
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        # ── Sorting ───────────────────────────────────────────────────────────
        sort_col = SORT_COLUMNS.get(sort_by, ScrapingTask.created_at)
        if sort_order.lower() == "asc":
            stmt = stmt.order_by(sort_col.asc())
        else:
            stmt = stmt.order_by(sort_col.desc())

        # ── Pagination ────────────────────────────────────────────────────────
        offset = (page - 1) * limit
        stmt = stmt.offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        tasks = result.scalars().all()

        return tasks, total

    async def update(self, task: ScrapingTask) -> ScrapingTask:
        """Save updates to an existing task."""
        await self.session.flush()
        return task

    async def count(self) -> int:
        """Return the overall count of scraping tasks."""
        stmt = select(func.count()).select_from(ScrapingTask)
        result = await self.session.execute(stmt)
        return result.scalar_one()
