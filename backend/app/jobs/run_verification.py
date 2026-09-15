"""
app/jobs/run_verification.py

Development CLI command to manually trigger data confidence verification for a task.

Usage:
    python -m app.jobs.run_verification TASK-000001
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from app.db.database import create_engine_and_factory, dispose_engine, get_session_factory
from app.jobs.verification_job import run_verification
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

        result = await run_verification(task_id, session=session)

    await dispose_engine()

    print(f"Task: {task_id}")
    print(f"Leads Processed: {result.leads_processed}")
    print(f"High Confidence Leads: {result.high_confidence_count}")
    print(f"Medium Confidence Leads: {result.medium_confidence_count}")
    print(f"Low Confidence Leads: {result.low_confidence_count}")
    print(f"Pending Leads: {result.pending_count}")
    print(f"Average Completeness: {result.average_completeness:.1f}%")
    print(f"Average Source Quality: {result.average_source_quality:.1f}")
    print(f"Average Consistency: {result.average_consistency:.1f}")
    print(f"Duration: {result.duration_seconds:.2f}s")
    print(f"Status: {result.status}")
    print(f"Next Stage: {result.next_stage}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run lead data-quality verification & confidence scoring engine for a ScrapingTask."
    )
    parser.add_argument("task_id", help="Human-readable Task ID (e.g. TASK-000001)")
    args = parser.parse_args()

    asyncio.run(main(args.task_id))
