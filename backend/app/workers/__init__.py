"""
app/workers package.

Celery application, background tasks, worker execution bridge,
and scraping pipeline orchestrator.
"""

from app.workers.celery_app import celery_app
from app.workers.pipeline import build_pipeline_chain, run_scraping_pipeline
from app.workers.task_context import (
    TaskAlreadyFailedException,
    TaskCancelledException,
    run_async,
    run_worker_stage,
)
from app.workers.tasks import (
    run_cleaning_task,
    run_crawl_task,
    run_discovery_task,
    run_extraction_task,
    run_finalize_task,
    run_verification_task,
)

__all__ = [
    "celery_app",
    "run_scraping_pipeline",
    "build_pipeline_chain",
    "run_discovery_task",
    "run_crawl_task",
    "run_extraction_task",
    "run_cleaning_task",
    "run_verification_task",
    "run_finalize_task",
    "run_worker_stage",
    "run_async",
    "TaskCancelledException",
    "TaskAlreadyFailedException",
]
