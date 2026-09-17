"""
tests/test_workers.py

Comprehensive test suite for Backend Step 9:
Redis, Celery, Background Task Execution & Pipeline Orchestration.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.jobs.finalization_job import run_finalize
from app.main import app as fastapi_app
from app.models.lead import Lead
from app.models.organization import Organization, task_organizations
from app.models.scraping_log import ScrapingLog
from app.models.scraping_task import ScrapingTask
from app.models.user import User
from app.models.website import Website
from app.services.finalization_service import FinalizationService
from app.workers.celery_app import celery_app
from app.workers.pipeline import build_pipeline_chain, run_scraping_pipeline
from app.workers.task_context import (
    TaskAlreadyFailedException,
    TaskCancelledException,
    run_async,
)
from app.workers.tasks import (
    run_cleaning_task,
    run_crawl_task,
    run_discovery_task,
    run_extraction_task,
    run_finalize_task,
    run_verification_task,
)


# ── 1. Celery Configuration & Task Registration Tests ─────────────────────────


def test_celery_configuration():
    """Verify Celery app configuration, serializer, and safe defaults."""
    conf = celery_app.conf
    assert conf.task_serializer == "json"
    assert conf.result_serializer == "json"
    assert conf.accept_content == ["json"]
    assert conf.timezone == "UTC"
    assert conf.enable_utc is True
    assert conf.worker_prefetch_multiplier == 1
    assert conf.task_acks_late is True
    assert conf.task_time_limit == 1800
    assert conf.task_soft_time_limit == 1500


def test_celery_queue_definitions_and_routing():
    """Verify logical queues (discovery, crawl, extraction, cleaning, verification, pipeline)."""
    queues = {q.name for q in celery_app.conf.task_queues}
    expected_queues = {"discovery", "crawl", "extraction", "cleaning", "verification", "pipeline"}
    assert expected_queues.issubset(queues)

    routes = celery_app.conf.task_routes
    assert routes["app.workers.tasks.run_discovery_task"]["queue"] == "pipeline"
    assert routes["app.workers.tasks.run_official_website_task"]["queue"] == "pipeline"
    assert routes["app.workers.tasks.run_crawl_task"]["queue"] == "pipeline"
    assert routes["app.workers.tasks.run_extraction_task"]["queue"] == "pipeline"
    assert routes["app.workers.tasks.run_cleaning_task"]["queue"] == "pipeline"
    assert routes["app.workers.tasks.run_verification_task"]["queue"] == "pipeline"
    assert routes["app.workers.tasks.run_finalize_task"]["queue"] == "pipeline"
    assert routes["app.workers.pipeline.run_scraping_pipeline"]["queue"] == "pipeline"



def test_registered_tasks():
    """Verify all worker and pipeline tasks are registered with Celery."""
    tasks = celery_app.tasks
    assert "app.workers.tasks.run_discovery_task" in tasks
    assert "app.workers.tasks.run_crawl_task" in tasks
    assert "app.workers.tasks.run_extraction_task" in tasks
    assert "app.workers.tasks.run_cleaning_task" in tasks
    assert "app.workers.tasks.run_verification_task" in tasks
    assert "app.workers.tasks.run_finalize_task" in tasks
    assert "app.workers.pipeline.run_scraping_pipeline" in tasks


# ── 2. Sync/Async Execution Bridge Tests ──────────────────────────────────────


def test_run_async_utility():
    """Verify run_async safely executes a coroutine from synchronous code."""
    async def sample_coro(a: int, b: int) -> int:
        return a + b

    result = run_async(sample_coro, 10, 25)
    assert result == 35


# ── 3. FinalizationService Tests ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_finalization_service_completes_task(db_session: AsyncSession):
    """Verify FinalizationService reconciles metrics and completes task."""
    user = User(name="Fin User", email="fin@example.com", password_hash="hash")
    db_session.add(user)
    await db_session.commit()

    task = ScrapingTask(
        task_id="TASK-FIN-01",
        user_id=user.id,
        location="Puducherry",
        keyword="Schools",
        status="RUNNING",
        current_stage="SAVING",
        progress=95,
    )
    db_session.add(task)
    await db_session.commit()

    org = Organization(name="Fin High School")
    web = Website(url="https://fin.edu", normalized_url="https://fin.edu")
    org.websites = [web]
    db_session.add(org)
    await db_session.commit()

    await db_session.execute(
        task_organizations.insert().values(task_id=task.id, organization_id=org.id)
    )
    lead = Lead(task_id=task.id, organization_id=org.id, verification_status="HIGH")
    db_session.add(lead)
    await db_session.commit()

    service = FinalizationService(db_session)
    summary = await service.finalize_task(task.task_id)

    assert summary.status == "COMPLETED"
    assert summary.current_stage == "COMPLETED"
    assert summary.progress == 100
    assert summary.verified_count == 1
    assert summary.high_confidence_count == 1
    assert summary.completed_at is not None

    # Check DB state
    stmt_t = select(ScrapingTask).where(ScrapingTask.id == task.id)
    refreshed_task = (await db_session.execute(stmt_t)).scalar_one()
    assert refreshed_task.status == "COMPLETED"
    assert refreshed_task.progress == 100
    assert refreshed_task.completed_at is not None

    # Check audit log
    stmt_log = select(ScrapingLog).where(
        ScrapingLog.task_id == task.id,
        ScrapingLog.event_type == "PIPELINE_COMPLETED",
    )
    log = (await db_session.execute(stmt_log)).scalar_one_or_none()
    assert log is not None
    assert "completed successfully" in log.message


@pytest.mark.asyncio
async def test_finalization_service_guards_cancelled_status(db_session: AsyncSession):
    """Verify FinalizationService does NOT overwrite CANCELLED status."""
    user = User(name="Cancel User", email="can@example.com", password_hash="hash")
    db_session.add(user)
    await db_session.commit()

    task = ScrapingTask(
        task_id="TASK-FIN-CANCEL",
        user_id=user.id,
        location="Puducherry",
        keyword="Schools",
        status="CANCELLED",
        current_stage="CRAWLING",
        progress=35,
    )
    db_session.add(task)
    await db_session.commit()

    service = FinalizationService(db_session)
    summary = await service.finalize_task(task.task_id)

    assert summary.status == "CANCELLED"
    assert summary.current_stage == "CRAWLING"
    assert summary.progress == 35


# ── 4. Full Pipeline Execution Tests (Eager Mode) ─────────────────────────────


@pytest.mark.asyncio
async def test_full_pipeline_execution_eager(db_session: AsyncSession, monkeypatch):
    """Verify sequential execution of the complete pipeline chain across all 6 stages."""
    user = User(name="Pipe User", email="pipe@example.com", password_hash="hash")
    db_session.add(user)
    await db_session.commit()

    task = ScrapingTask(
        task_id="TASK-PIPE-01",
        user_id=user.id,
        location="Puducherry",
        keyword="CBSE Schools",
        selected_fields=["name", "website", "phone", "email"],
        status="PENDING",
        current_stage="CREATING_TASK",
        progress=0,
    )
    db_session.add(task)
    await db_session.commit()

    # Route DB sessions to this in-memory session
    class MockContext:
        async def __aenter__(self):
            return db_session

        async def __aexit__(self, *args):
            pass

    monkeypatch.setattr("app.workers.task_context.get_session_factory", lambda: lambda: MockContext())
    monkeypatch.setattr(settings, "DISCOVERY_ENABLE_FIXTURES", True)

    # Build chain and execute in eager mode
    chain_obj = build_pipeline_chain(task.task_id)
    celery_app.conf.task_always_eager = True

    result = chain_obj.apply()
    assert result.successful()

    # Check task completion state
    stmt_t = select(ScrapingTask).where(ScrapingTask.id == task.id)
    updated_task = (await db_session.execute(stmt_t)).scalar_one()

    assert updated_task.status == "COMPLETED"
    assert updated_task.current_stage == "COMPLETED"
    assert updated_task.progress == 100
    assert updated_task.started_at is not None
    assert updated_task.completed_at is not None
    assert updated_task.results_discovered > 0

    # Verify lifecycle logs recorded
    stmt_logs = select(ScrapingLog).where(ScrapingLog.task_id == task.id)
    logs = list((await db_session.execute(stmt_logs)).scalars().all())
    event_types = [l.event_type for l in logs]

    assert "PIPELINE_STARTED" in event_types
    assert "PIPELINE_STAGE_STARTED" in event_types
    assert "PIPELINE_STAGE_COMPLETED" in event_types
    assert "PIPELINE_COMPLETED" in event_types


# ── 5. Stage Failure Halting Tests ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_stage_failure_halts_downstream_stages(db_session: AsyncSession, monkeypatch):
    """Verify failure in one stage halts downstream pipeline stages and marks task FAILED."""
    user = User(name="Fail User", email="fail@example.com", password_hash="hash")
    db_session.add(user)
    await db_session.commit()

    task = ScrapingTask(
        task_id="TASK-FAIL-PIPE",
        user_id=user.id,
        location="Puducherry",
        keyword="Colleges",
        status="PENDING",
        current_stage="CREATING_TASK",
        progress=0,
    )
    db_session.add(task)
    await db_session.commit()

    class MockContext:
        async def __aenter__(self):
            return db_session

        async def __aexit__(self, *args):
            pass

    monkeypatch.setattr("app.workers.task_context.get_session_factory", lambda: lambda: MockContext())

    # Simulate catastrophic failure during extraction
    async def mock_fail_extraction(task_id, session=None):
        raise RuntimeError("Simulated unrecoverable HTML parser crash")

    monkeypatch.setattr("app.workers.tasks.run_extraction", mock_fail_extraction)

    celery_app.conf.task_always_eager = True
    chain_obj = build_pipeline_chain(task.task_id)

    # Executing the chain should raise the failure
    with pytest.raises(Exception):
        chain_obj.apply()

    # Check task DB state
    stmt_t = select(ScrapingTask).where(ScrapingTask.id == task.id)
    failed_task = (await db_session.execute(stmt_t)).scalar_one()

    assert failed_task.status == "FAILED"
    assert "Simulated unrecoverable HTML parser crash" in failed_task.failure_reason
    assert failed_task.current_stage != "COMPLETED"

    # Verify PIPELINE_STAGE_FAILED log exists
    stmt_log = select(ScrapingLog).where(
        ScrapingLog.task_id == task.id,
        ScrapingLog.event_type == "PIPELINE_STAGE_FAILED",
    )
    fail_log = (await db_session.execute(stmt_log)).scalar_one_or_none()
    assert fail_log is not None
    assert "EXTRACTING" in fail_log.message


# ── 6. Cancellation Safety Tests ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cancellation_halts_pipeline_stage(db_session: AsyncSession, monkeypatch):
    """Verify that a cancelled task stops execution cleanly without continuing stages."""
    user = User(name="Cancel User", email="cpipe@example.com", password_hash="hash")
    db_session.add(user)
    await db_session.commit()

    task = ScrapingTask(
        task_id="TASK-CANCEL-PIPE",
        user_id=user.id,
        location="Puducherry",
        keyword="Dentists",
        status="CANCELLED",
        current_stage="DISCOVERING",
        progress=10,
    )
    db_session.add(task)
    await db_session.commit()

    class MockContext:
        async def __aenter__(self):
            return db_session

        async def __aexit__(self, *args):
            pass

    monkeypatch.setattr("app.workers.task_context.get_session_factory", lambda: lambda: MockContext())

    celery_app.conf.task_always_eager = True
    # Attempting to run crawl on a cancelled task
    result = run_crawl_task.apply(args=[task.task_id])
    assert result.result["status"] == "HALTED"
    assert "cancelled" in result.result["reason"].lower()

    # Task status remains CANCELLED
    stmt_t = select(ScrapingTask).where(ScrapingTask.id == task.id)
    refreshed_task = (await db_session.execute(stmt_t)).scalar_one()
    assert refreshed_task.status == "CANCELLED"


# ── 7. Transient Retry Tests ──────────────────────────────────────────────────


def test_transient_error_triggers_retry(monkeypatch):
    """Verify that transient infrastructure exceptions trigger self.retry."""
    from celery.exceptions import Retry

    def mock_stage_fn(*args, **kwargs):
        raise RedisConnectionError("Temporary Redis connection reset")

    monkeypatch.setattr("app.workers.tasks.run_worker_stage", mock_stage_fn)

    with pytest.raises(Retry):
        run_discovery_task.apply(args=["TASK-RETRY-01"], throw=True)



# ── 8. API Queueing Failure Recovery Tests ────────────────────────────────────


@pytest.mark.asyncio
async def test_create_task_queuing_failure_recovery(test_app_client: AsyncClient, monkeypatch):
    """Verify POST /api/scrape marks task FAILED and returns 503 if broker fails."""
    def mock_failing_delay(task_id):
        raise RedisConnectionError("Redis broker is unavailable")

    monkeypatch.setattr("app.workers.pipeline.run_scraping_pipeline.delay", mock_failing_delay)

    response = await test_app_client.post(
        "/api/scrape",
        json={
            "location": "Chennai",
            "keyword": "Clinics",
            "selected_fields": ["name", "phone"],
        },
    )

    assert response.status_code == 503
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "QUEUE_ERROR"
    assert "Unable to queue background scraping job" in body["error"]["message"]


# ── 9. Development CLI Runner Tests ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_run_pipeline_cli_runner(db_session: AsyncSession, monkeypatch, capsys):
    """Verify run_pipeline CLI runner outputs task and job details."""
    from app.jobs.run_pipeline import main as run_pipeline_main

    async def mock_dispose():
        pass

    monkeypatch.setattr("app.jobs.run_pipeline.create_engine_and_factory", lambda: None)
    monkeypatch.setattr("app.jobs.run_pipeline.dispose_engine", mock_dispose)

    class MockContext:
        async def __aenter__(self):
            return db_session

        async def __aexit__(self, *args):
            pass

    monkeypatch.setattr("app.jobs.run_pipeline.get_session_factory", lambda: lambda: MockContext())

    user = User(
        id=uuid.uuid4(),
        name="CLI Pipeline User",
        email=f"cli_pipe_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="hash",
    )
    db_session.add(user)
    await db_session.commit()

    task = ScrapingTask(
        task_id="TASK-CLI-PIPE",
        user_id=user.id,
        keyword="Hospitals",
        location="Puducherry",
        status="PENDING",
    )
    db_session.add(task)
    await db_session.commit()

    mock_async_res = MagicMock()
    mock_async_res.id = "mock-celery-chain-uuid-999"

    monkeypatch.setattr(
        "app.workers.pipeline.run_scraping_pipeline.delay",
        lambda tid: mock_async_res,
    )

    await run_pipeline_main(task.task_id, eager=False)

    captured = capsys.readouterr().out
    assert "Submitting scraping pipeline for task: TASK-CLI-PIPE" in captured
    assert "Pipeline enqueued." in captured
    assert "Task ID: TASK-CLI-PIPE" in captured
    assert "Celery Job ID: mock-celery-chain-uuid-999" in captured
    assert "Queue: pipeline" in captured
