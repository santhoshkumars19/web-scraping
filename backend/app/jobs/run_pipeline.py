"""
app/jobs/run_pipeline.py

Development CLI command to manually trigger the full background scraping pipeline for a task.

Usage:
    python -m app.jobs.run_pipeline TASK-000001
    python -m app.jobs.run_pipeline TASK-000001 --eager
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from app.db.database import create_engine_and_factory, dispose_engine, get_session_factory
from app.repositories.task_repository import TaskRepository


async def main(task_id: str, eager: bool = False) -> None:
    create_engine_and_factory()
    factory = get_session_factory()

    async with factory() as session:
        repo = TaskRepository(session)
        task = await repo.get_by_task_id(task_id)
        if not task:
            print(f"Error: Task '{task_id}' not found.")
            sys.exit(1)

    await dispose_engine()

    from app.workers.celery_app import celery_app
    from app.workers.pipeline import run_scraping_pipeline

    print(f"Submitting scraping pipeline for task: {task_id} (eager={eager})")

    if eager:
        # Run synchronously in eager mode
        celery_app.conf.task_always_eager = True
        res = run_scraping_pipeline.apply(args=[task_id])
        print(f"Pipeline executed synchronously.")
        print(f"Result: {res.result}")
    else:
        # Submit to Celery broker
        async_res = run_scraping_pipeline.delay(task_id)
        print(f"Pipeline enqueued.")
        print(f"Task ID: {task_id}")
        print(f"Celery Job ID: {async_res.id}")
        print(f"Queue: pipeline")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run background scraping pipeline for a ScrapingTask."
    )
    parser.add_argument("task_id", help="Human-readable Task ID (e.g. TASK-000001)")
    parser.add_argument(
        "--eager",
        action="store_true",
        help="Run synchronously in eager mode instead of queueing to Redis",
    )
    args = parser.parse_args()

    asyncio.run(main(args.task_id, eager=args.eager))
