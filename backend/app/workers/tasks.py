"""
app/workers/tasks.py

Individual Celery stage tasks for the LeadScout scraping pipeline.
Each stage calls the corresponding existing service/job function via the worker bridge.
"""

from __future__ import annotations

from typing import Any

from redis.exceptions import RedisError
from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.core.logging import get_logger
from app.jobs.cleaning_job import run_cleaning
from app.jobs.crawl_job import run_crawl
from app.jobs.discovery_job import run_discovery
from app.jobs.extraction_job import run_extraction
from app.jobs.finalization_job import run_finalize
from app.jobs.verification_job import run_verification
from app.workers.celery_app import celery_app
from app.workers.task_context import (
    TaskAlreadyFailedException,
    TaskCancelledException,
    run_worker_stage,
)

logger = get_logger(__name__)

TRANSIENT_ERRORS = (OperationalError, ConnectionError, TimeoutError, RedisError)


@celery_app.task(
    bind=True,
    name="app.workers.tasks.run_discovery_task",
    queue="discovery",
    max_retries=settings.CELERY_MAX_RETRIES,
    acks_late=True,
)
def run_discovery_task(self, task_id: str, *args: Any, **kwargs: Any) -> dict[str, Any]:
    """Execute Discovery Engine stage for a task."""
    logger.info("Celery task started: run_discovery_task for %s", task_id)
    try:
        return run_worker_stage(run_discovery, task_id, "DISCOVERING")
    except (TaskCancelledException, TaskAlreadyFailedException) as e:
        logger.info("Discovery task halted for %s: %s", task_id, e)
        return {"task_id": task_id, "status": "HALTED", "reason": str(e)}
    except TRANSIENT_ERRORS as exc:
        logger.warning(
            "Transient error in discovery for task %s (attempt %d/%d): %s",
            task_id,
            self.request.retries + 1,
            self.max_retries,
            exc,
        )
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
    except Exception as exc:
        logger.error("Permanent error in discovery for task %s: %s", task_id, exc)
        raise


@celery_app.task(
    bind=True,
    name="app.workers.tasks.run_crawl_task",
    queue="crawl",
    max_retries=settings.CELERY_MAX_RETRIES,
    acks_late=True,
)
def run_crawl_task(self, task_id: str, *args: Any, **kwargs: Any) -> dict[str, Any]:
    """Execute Website Crawler stage for a task."""
    logger.info("Celery task started: run_crawl_task for %s", task_id)
    try:
        return run_worker_stage(run_crawl, task_id, "CRAWLING")
    except (TaskCancelledException, TaskAlreadyFailedException) as e:
        logger.info("Crawl task halted for %s: %s", task_id, e)
        return {"task_id": task_id, "status": "HALTED", "reason": str(e)}
    except TRANSIENT_ERRORS as exc:
        logger.warning(
            "Transient error in crawler for task %s (attempt %d/%d): %s",
            task_id,
            self.request.retries + 1,
            self.max_retries,
            exc,
        )
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
    except Exception as exc:
        logger.error("Permanent error in crawler for task %s: %s", task_id, exc)
        raise


@celery_app.task(
    bind=True,
    name="app.workers.tasks.run_extraction_task",
    queue="extraction",
    max_retries=settings.CELERY_MAX_RETRIES,
    acks_late=True,
)
def run_extraction_task(self, task_id: str, *args: Any, **kwargs: Any) -> dict[str, Any]:
    """Execute Data Extraction stage for a task."""
    logger.info("Celery task started: run_extraction_task for %s", task_id)
    try:
        return run_worker_stage(run_extraction, task_id, "EXTRACTING")
    except (TaskCancelledException, TaskAlreadyFailedException) as e:
        logger.info("Extraction task halted for %s: %s", task_id, e)
        return {"task_id": task_id, "status": "HALTED", "reason": str(e)}
    except TRANSIENT_ERRORS as exc:
        logger.warning(
            "Transient error in extraction for task %s (attempt %d/%d): %s",
            task_id,
            self.request.retries + 1,
            self.max_retries,
            exc,
        )
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
    except Exception as exc:
        logger.error("Permanent error in extraction for task %s: %s", task_id, exc)
        raise


@celery_app.task(
    bind=True,
    name="app.workers.tasks.run_cleaning_task",
    queue="cleaning",
    max_retries=settings.CELERY_MAX_RETRIES,
    acks_late=True,
)
def run_cleaning_task(self, task_id: str, *args: Any, **kwargs: Any) -> dict[str, Any]:
    """Execute Data Cleaning and Deduplication stage for a task."""
    logger.info("Celery task started: run_cleaning_task for %s", task_id)
    try:
        return run_worker_stage(run_cleaning, task_id, "CLEANING")
    except (TaskCancelledException, TaskAlreadyFailedException) as e:
        logger.info("Cleaning task halted for %s: %s", task_id, e)
        return {"task_id": task_id, "status": "HALTED", "reason": str(e)}
    except TRANSIENT_ERRORS as exc:
        logger.warning(
            "Transient error in cleaning for task %s (attempt %d/%d): %s",
            task_id,
            self.request.retries + 1,
            self.max_retries,
            exc,
        )
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
    except Exception as exc:
        logger.error("Permanent error in cleaning for task %s: %s", task_id, exc)
        raise


@celery_app.task(
    bind=True,
    name="app.workers.tasks.run_verification_task",
    queue="verification",
    max_retries=settings.CELERY_MAX_RETRIES,
    acks_late=True,
)
def run_verification_task(self, task_id: str, *args: Any, **kwargs: Any) -> dict[str, Any]:
    """Execute Lead Data-Quality Verification & Confidence Scoring stage for a task."""
    logger.info("Celery task started: run_verification_task for %s", task_id)
    try:
        return run_worker_stage(run_verification, task_id, "VERIFYING")
    except (TaskCancelledException, TaskAlreadyFailedException) as e:
        logger.info("Verification task halted for %s: %s", task_id, e)
        return {"task_id": task_id, "status": "HALTED", "reason": str(e)}
    except TRANSIENT_ERRORS as exc:
        logger.warning(
            "Transient error in verification for task %s (attempt %d/%d): %s",
            task_id,
            self.request.retries + 1,
            self.max_retries,
            exc,
        )
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
    except Exception as exc:
        logger.error("Permanent error in verification for task %s: %s", task_id, exc)
        raise


@celery_app.task(
    bind=True,
    name="app.workers.tasks.run_finalize_task",
    queue="pipeline",
    max_retries=settings.CELERY_MAX_RETRIES,
    acks_late=True,
)
def run_finalize_task(self, task_id: str, *args: Any, **kwargs: Any) -> dict[str, Any]:
    """Execute Finalization and Completion stage for a task."""
    logger.info("Celery task started: run_finalize_task for %s", task_id)
    try:
        return run_worker_stage(run_finalize, task_id, "COMPLETED")
    except (TaskCancelledException, TaskAlreadyFailedException) as e:
        logger.info("Finalize task halted for %s: %s", task_id, e)
        return {"task_id": task_id, "status": "HALTED", "reason": str(e)}
    except TRANSIENT_ERRORS as exc:
        logger.warning(
            "Transient error in finalize for task %s (attempt %d/%d): %s",
            task_id,
            self.request.retries + 1,
            self.max_retries,
            exc,
        )
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
    except Exception as exc:
        logger.error("Permanent error in finalize for task %s: %s", task_id, exc)
        raise
