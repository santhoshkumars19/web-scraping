"""
app/jobs/run_cleaning.py

Development CLI command to manually trigger data cleaning and deduplication for a task.

Usage:
    python -m app.jobs.run_cleaning TASK-000001
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from app.db.database import create_engine_and_factory, dispose_engine, get_session_factory
from app.jobs.cleaning_job import run_cleaning
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

        result = await run_cleaning(task_id, session=session)

    await dispose_engine()

    print(f"Task: {task_id}")
    print(f"Organizations Processed: {result.organizations_processed}")
    print(f"Organizations Merged: {result.organizations_merged}")
    print(f"Exact Duplicates Removed: {result.exact_duplicates_removed}")
    print(f"Phones Cleaned: {result.phones_cleaned}")
    print(f"Emails Cleaned: {result.emails_cleaned}")
    print(f"Addresses Cleaned: {result.addresses_cleaned}")
    print(f"Invalid Phones Removed: {result.invalid_phones_removed}")
    print(f"Invalid Emails Removed: {result.invalid_emails_removed}")
    print(f"Potential Duplicates Flagged: {result.potential_duplicates_flagged}")
    print(f"Total Duplicates Removed: {result.total_duplicates_removed}")
    print(f"Status: {result.status}")
    print(f"Next Stage: {result.next_stage}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run data cleaning & deduplication engine for a ScrapingTask."
    )
    parser.add_argument("task_id", help="Human-readable Task ID (e.g. TASK-000001)")
    args = parser.parse_args()

    asyncio.run(main(args.task_id))
