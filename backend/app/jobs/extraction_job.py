"""
app/jobs/extraction_job.py

Extraction task execution job function.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import create_engine_and_factory, get_session_factory
from app.schemas.extraction import TaskExtractionSummary
from app.services.extraction_service import ExtractionService


async def run_extraction(
    task_id: str,
    session: AsyncSession | None = None,
) -> TaskExtractionSummary:
    """Execute the data extraction pipeline for a given task ID.

    Can be invoked directly by background workers or the development CLI.
    """
    if session is not None:
        service = ExtractionService(session)
        return await service.extract_for_task(task_id)

    # Ensure engine and session factory are initialized
    try:
        factory = get_session_factory()
    except RuntimeError:
        create_engine_and_factory()
        factory = get_session_factory()

    async with factory() as new_session:
        service = ExtractionService(new_session)
        return await service.extract_for_task(task_id)
