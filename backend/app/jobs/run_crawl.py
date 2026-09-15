"""
app/jobs/run_crawl.py

Development CLI command to manually trigger website crawling for a task.

Usage:
    python -m app.jobs.run_crawl TASK-000001
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from app.db.database import create_engine_and_factory, dispose_engine, get_session_factory
from app.jobs.crawl_job import run_crawl
from app.repositories.task_repository import TaskRepository


async def main(task_id: str) -> None:
    create_engine_and_factory()
    factory = get_session_factory()

    async with factory() as session:
        repo = TaskRepository(session)
        task = await repo.get_by_task_id(task_id)
        if not task:
            print(f"Error: Task '{task_id}' not found.")
            sys.exit(1)

        result = await run_crawl(task_id, session=session)

    await dispose_engine()

    print(f"Task: {task_id}")
    print(f"Websites: {result.total_websites}")
    print(f"Crawled: {result.websites_crawled}")
    print(f"Failed: {result.failed_websites}")
    print(f"Blocked: {result.blocked_websites}")
    print(f"Pages: {result.total_pages_stored}")
    print(f"Playwright: {result.playwright_total}")
    print(f"Status: {result.status}")
    print(f"Next Stage: {result.next_stage}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run website crawler for a ScrapingTask.")
    parser.add_argument("task_id", help="Human-readable Task ID (e.g. TASK-000001)")
    args = parser.parse_args()

    asyncio.run(main(args.task_id))
