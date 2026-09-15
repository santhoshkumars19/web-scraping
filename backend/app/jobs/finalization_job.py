"""
app/jobs/finalization_job.py

Finalization task execution job function.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import create_engine_and_factory, get_session_factory
from app.services.finalization_service import (
    FinalizationService,
    TaskFinalizationSummary,
)


async def run_finalize(
    task_id: str | uuid.UUID,
    session: AsyncSession | None = None,
) -> TaskFinalizationSummary:
    """Execute the finalization and task completion stage for a given task ID.

    Can be invoked directly by background workers or the development CLI.
    """
    if session is not None:
        service = FinalizationService(session)
        return await service.finalize_task(task_id)

    # Ensure engine and session factory are initialized
    try:
        factory = get_session_factory()
    except RuntimeError:
        create_engine_and_factory()
        factory = get_session_factory()

    async with factory() as new_session:
        service = FinalizationService(new_session)
        return await service.finalize_task(task_id)
