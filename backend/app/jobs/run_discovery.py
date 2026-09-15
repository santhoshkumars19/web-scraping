"""
app/jobs/run_discovery.py

Development CLI command to manually trigger discovery for a task.

Usage:
    python -m app.jobs.run_discovery TASK-000001
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from app.db.database import create_engine_and_factory, dispose_engine, get_session_factory
from app.jobs.discovery_job import run_discovery
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

        location = task.location
        keyword = task.keyword

        result = await run_discovery(task_id, session=session)

    await dispose_engine()

    print(f"Task: {task_id}")
    print(f"Location: {location}")
    print(f"Keyword: {keyword}")
    print(f"Candidates: {result.total_candidates}")
    print(f"Accepted: {result.accepted_candidates}")
    print(f"Duplicates: {result.duplicates_removed}")
    print(f"Websites: {result.websites_found}")
    print("Status: Discovery completed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run discovery engine for a ScrapingTask.")
    parser.add_argument("task_id", help="Human-readable Task ID (e.g. TASK-000001)")
    args = parser.parse_args()

    asyncio.run(main(args.task_id))
