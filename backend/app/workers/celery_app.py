"""
app/workers/celery_app.py

Celery application initialization, configuration, and queue routing for LeadScout.
"""

from __future__ import annotations

from celery import Celery
from kombu import Exchange, Queue

from app.core.config import settings

# ── Instantiate Celery ────────────────────────────────────────────────────────
celery_app = Celery("leadscout")

# ── Define Exchanges and Queues ───────────────────────────────────────────────
default_exchange = Exchange("leadscout", type="direct")

task_queues = (
    Queue("pipeline", default_exchange, routing_key="pipeline"),
    Queue("discovery", default_exchange, routing_key="discovery"),
    Queue("crawl", default_exchange, routing_key="crawl"),
    Queue("extraction", default_exchange, routing_key="extraction"),
    Queue("cleaning", default_exchange, routing_key="cleaning"),
    Queue("verification", default_exchange, routing_key="verification"),
)

# ── Configure Celery Settings ─────────────────────────────────────────────────
celery_app.conf.update(
    broker_url=settings.CELERY_BROKER_URL,
    result_backend=settings.CELERY_RESULT_BACKEND,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_soft_time_limit=settings.CELERY_SOFT_TIME_LIMIT,
    result_expires=settings.CELERY_RESULT_EXPIRES,
    worker_concurrency=settings.CELERY_WORKER_CONCURRENCY,
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
    task_eager_propagates=True,
    task_queues=task_queues,
    task_default_queue="pipeline",
    task_default_exchange="leadscout",
    task_default_routing_key="pipeline",
    task_routes={
        "app.workers.pipeline.run_scraping_pipeline": {"queue": "pipeline"},
        "app.workers.tasks.run_discovery_task": {"queue": "pipeline"},
        "app.workers.tasks.run_official_website_task": {"queue": "pipeline"},
        "app.workers.tasks.run_crawl_task": {"queue": "pipeline"},
        "app.workers.tasks.run_extraction_task": {"queue": "pipeline"},
        "app.workers.tasks.run_cleaning_task": {"queue": "pipeline"},
        "app.workers.tasks.run_verification_task": {"queue": "pipeline"},
        "app.workers.tasks.run_finalize_task": {"queue": "pipeline"},
    },
)

# ── Auto-register worker modules ──────────────────────────────────────────────
celery_app.autodiscover_tasks(["app.workers"])
