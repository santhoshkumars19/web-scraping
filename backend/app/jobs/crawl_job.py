"""
app/jobs/crawl_job.py

Crawl task execution job function.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import create_engine_and_factory, get_session_factory
from app.schemas.crawler import TaskCrawlSummary
from app.services.crawler_service import CrawlerService


async def run_crawl(
    task_id: str,
    session: AsyncSession | None = None,
) -> TaskCrawlSummary:
    """Execute the website crawling pipeline for a given task ID.

    Can be invoked directly by background workers or the development CLI.
    """
    if session is not None:
        service = CrawlerService(session)
        return await service.crawl_for_task(task_id)

    # Ensure engine and session factory are initialized
    try:
        factory = get_session_factory()
    except RuntimeError:
        create_engine_and_factory()
        factory = get_session_factory()

    async with factory() as new_session:
        service = CrawlerService(new_session)
        return await service.crawl_for_task(task_id)
