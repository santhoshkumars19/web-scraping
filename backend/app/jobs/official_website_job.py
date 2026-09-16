"""
app/jobs/official_website_job.py

Official website candidate identification job entrypoint.
"""

from __future__ import annotations

from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import create_engine_and_factory, get_session_factory
from app.services.official_website_service import OfficialWebsiteService


async def run_official_website(
    task_id: str,
    session: AsyncSession | None = None,
) -> dict[str, Any]:
    """Execute the official website identification phase for a given task ID."""
    if session is not None:
        service = OfficialWebsiteService(session)
        return await service.find_official_websites_for_task(task_id)

    try:
        factory = get_session_factory()
    except RuntimeError:
        create_engine_and_factory()
        factory = get_session_factory()

    async with factory() as new_session:
        service = OfficialWebsiteService(new_session)
        return await service.find_official_websites_for_task(task_id)
