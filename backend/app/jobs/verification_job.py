"""
app/jobs/verification_job.py

Verification and data confidence scoring task execution job function.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import create_engine_and_factory, get_session_factory
from app.schemas.verification import TaskVerificationSummary
from app.services.verification.verification_service import VerificationService


async def run_verification(
    task_id: str | uuid.UUID,
    session: AsyncSession | None = None,
) -> TaskVerificationSummary:
    """Execute the data confidence verification and scoring engine for a task ID.

    Can be invoked directly by background workers or the development CLI.
    """
    if session is not None:
        service = VerificationService(session)
        return await service.verify_task(task_id)

    # Ensure engine and session factory are initialized
    try:
        factory = get_session_factory()
    except RuntimeError:
        create_engine_and_factory()
        factory = get_session_factory()

    async with factory() as new_session:
        service = VerificationService(new_session)
        return await service.verify_task(task_id)
