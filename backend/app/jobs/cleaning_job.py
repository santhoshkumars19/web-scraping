"""
app/jobs/cleaning_job.py

Cleaning task execution job function.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import create_engine_and_factory, get_session_factory
from app.schemas.cleaning import CleaningResult
from app.services.cleaning.cleaning_service import CleaningService


async def run_cleaning(
    task_id: str | uuid.UUID,
    session: AsyncSession | None = None,
) -> CleaningResult:
    """Execute the data cleaning and deduplication pipeline for a given task ID.

    Can be invoked directly by background workers or the development CLI.
    """
    if session is not None:
        service = CleaningService(session)
        return await service.clean_task(task_id)

    # Ensure engine and session factory are initialized
    try:
        factory = get_session_factory()
    except RuntimeError:
        create_engine_and_factory()
        factory = get_session_factory()

    async with factory() as new_session:
        service = CleaningService(new_session)
        return await service.clean_task(task_id)
