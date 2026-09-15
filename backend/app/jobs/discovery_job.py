"""
app/jobs/discovery_job.py

Discovery task execution job function.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import create_engine_and_factory, get_session_factory
from app.schemas.discovery import DiscoveryResult
from app.services.discovery_service import DiscoveryService


async def run_discovery(
    task_id: str,
    session: AsyncSession | None = None,
) -> DiscoveryResult:
    """Execute the discovery pipeline for a given task ID.

    Can be invoked directly by background workers or the development CLI.
    """
    if session is not None:
        service = DiscoveryService(session)
        return await service.discover_for_task(task_id)

    # Ensure engine and session factory are initialized
    try:
        factory = get_session_factory()
    except RuntimeError:
        create_engine_and_factory()
        factory = get_session_factory()

    async with factory() as new_session:
        service = DiscoveryService(new_session)
        return await service.discover_for_task(task_id)
