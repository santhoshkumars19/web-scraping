"""
app/workers/pipeline.py

Celery pipeline orchestrator composing the complete scraping workflow chain.
"""

from __future__ import annotations

from typing import Any

from celery import chain

from app.core.logging import get_logger
from app.workers.celery_app import celery_app
from app.workers.tasks import (
    run_cleaning_task,
    run_crawl_task,
    run_discovery_task,
    run_extraction_task,
    run_finalize_task,
    run_official_website_task,
    run_verification_task,
)

logger = get_logger(__name__)


def build_pipeline_chain(task_id: str) -> chain:
    """Construct the sequential Celery chain of tasks for a scraping pipeline.

    Flow:
        Discovery (discovery)
        ↓
        Official Website Identification (discovery)
        ↓
        Crawl (crawl)
        ↓
        Extraction (extraction)
        ↓
        Cleaning & Deduplication (cleaning)
        ↓
        Verification & Scoring (verification)
        ↓
        Finalization (pipeline)
    """
    return chain(
        run_discovery_task.si(task_id),
        run_official_website_task.si(task_id),
        run_crawl_task.si(task_id),
        run_extraction_task.si(task_id),
        run_cleaning_task.si(task_id),
        run_verification_task.si(task_id),
        run_finalize_task.si(task_id),
    )


@celery_app.task(
    bind=True,
    name="app.workers.pipeline.run_scraping_pipeline",
    queue="pipeline",
    acks_late=True,
)
def run_scraping_pipeline(self, task_id: str) -> dict[str, Any]:
    """Orchestrates and triggers the full background scraping pipeline chain for a task."""
    logger.info(
        "Initiating scraping pipeline chain for task %s (job_id=%s, eager=%s)",
        task_id,
        self.request.id,
        celery_app.conf.task_always_eager,
    )

    workflow = build_pipeline_chain(task_id)

    if celery_app.conf.task_always_eager:
        # In eager mode (e.g. tests), execute the chain synchronously to completion
        res = workflow.apply()
        return {
            "task_id": task_id,
            "status": "COMPLETED",
            "chain_result": str(res.result) if res else "OK",
        }
    else:
        # In distributed mode, dispatch to Redis broker
        chain_async = workflow.apply_async()
        return {
            "task_id": task_id,
            "status": "QUEUED",
            "pipeline_chain_id": chain_async.id,
        }
