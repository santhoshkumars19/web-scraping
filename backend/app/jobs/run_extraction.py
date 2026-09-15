"""
app/jobs/run_extraction.py

Development CLI command to manually trigger data extraction for a task.

Usage:
    python -m app.jobs.run_extraction TASK-000001
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from app.db.database import create_engine_and_factory, dispose_engine, get_session_factory
from app.jobs.extraction_job import run_extraction
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

        result = await run_extraction(task_id, session=session)

    await dispose_engine()

    print(f"Task: {task_id}")
    print(f"Pages Processed: {result.pages_processed}")
    print(f"Phones Extracted: {result.phones_extracted}")
    print(f"Emails Extracted: {result.emails_extracted}")
    print(f"Addresses Extracted: {result.addresses_extracted}")
    print(f"Contacts Extracted: {result.contacts_extracted}")
    print(f"Social Links Extracted: {result.social_links_extracted}")
    print(f"Status: {result.status}")
    print(f"Next Stage: {result.next_stage}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run data extraction engine for a ScrapingTask.")
    parser.add_argument("task_id", help="Human-readable Task ID (e.g. TASK-000001)")
    args = parser.parse_args()

    asyncio.run(main(args.task_id))
