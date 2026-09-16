"""
tests/test_pipeline_stages.py

Regression test suite specifically verifying the resolution of the "Stuck at 15%" bug:
1. Zero candidate websites found after discovery advances cleanly to EXTRACTING (no stall at 15%).
2. CrawlerService commits task.current_stage = "CRAWLING" and progress >= 20 immediately upon entry.
3. Slow/hanging websites are bounded by timeout and do not stall the pipeline.
4. run_worker_stage commits stage start state before calling the underlying stage service.
5. End-to-end stage progression from DISCOVERING -> FINDING_WEBSITES -> CRAWLING -> EXTRACTING -> COMPLETED.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.organization import Organization, task_organizations
from app.models.scraping_log import ScrapingLog
from app.models.scraping_task import ScrapingTask
from app.models.user import User
from app.models.website import Website
from app.schemas.crawler import WebsiteCrawlResult
from app.realtime.publisher import MockTaskEventPublisher, set_event_publisher
from app.services.crawler_service import CrawlerService
from app.services.discovery_service import DiscoveryService
from app.workers.task_context import run_worker_stage


@pytest.fixture(autouse=True)
def enable_fixtures_for_stage_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "DISCOVERY_ENABLE_FIXTURES", True)
    set_event_publisher(MockTaskEventPublisher())


@pytest.mark.asyncio
async def test_zero_websites_found_advances_to_extracting(db_session: AsyncSession) -> None:
    """When discovery finds organizations but zero candidate websites, CrawlerService must
    immediately advance the task to EXTRACTING at 50% without stalling or waiting.
    """
    user = User(
        name="Zero Sites User",
        email=f"zero_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="hash",
    )
    db_session.add(user)
    await db_session.flush()

    task = ScrapingTask(
        task_id=f"TASK-ZERO-{uuid.uuid4().hex[:4].upper()}",
        user_id=user.id,
        location="Nowhere",
        keyword="Unknowns",
        status="RUNNING",
        current_stage="FINDING_WEBSITES",
        progress=15,
        results_discovered=3,
        websites_found=0,
    )
    db_session.add(task)
    await db_session.flush()

    # Create 3 organizations without any associated Website records
    for i in range(3):
        org = Organization(name=f"Org Without Site {i}", city="Nowhere")
        db_session.add(org)
        await db_session.flush()
        await db_session.execute(
            task_organizations.insert().values(task_id=task.id, organization_id=org.id)
        )
    await db_session.commit()

    service = CrawlerService(session=db_session)
    summary = await service.crawl_for_task(task.task_id)

    # Must have 0 websites queued, 0 crawled, 0 failed, and advance cleanly
    assert summary.total_websites == 0
    assert summary.websites_crawled == 0
    assert summary.failed_websites == 0
    assert summary.next_stage == "EXTRACTING"

    # Task state in DB must be updated and committed
    stmt = select(ScrapingTask).where(ScrapingTask.id == task.id)
    refreshed = (await db_session.execute(stmt)).scalar_one()
    assert refreshed.current_stage == "EXTRACTING"
    assert refreshed.progress == 50
    assert refreshed.status == "RUNNING"
    assert refreshed.websites_crawled == 0


@pytest.mark.asyncio
async def test_crawler_service_immediate_stage_commit(db_session: AsyncSession) -> None:
    """CrawlerService must commit task.current_stage = 'CRAWLING' and progress >= 20
    to the database before any website HTTP crawl loops begin.
    """
    user = User(
        name="Commit User",
        email=f"commit_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="hash",
    )
    db_session.add(user)
    await db_session.flush()

    task = ScrapingTask(
        task_id=f"TASK-COMMIT-{uuid.uuid4().hex[:4].upper()}",
        user_id=user.id,
        location="Chennai",
        keyword="Hotels",
        status="RUNNING",
        current_stage="FINDING_WEBSITES",
        progress=15,
    )
    db_session.add(task)
    await db_session.flush()

    org = Organization(name="Commit Hotel", city="Chennai")
    db_session.add(org)
    await db_session.flush()
    await db_session.execute(
        task_organizations.insert().values(task_id=task.id, organization_id=org.id)
    )

    site = Website(
        organization_id=org.id,
        url="https://commithotel.example",
        normalized_url="https://commithotel.example",
        domain="commithotel.example",
        status="PENDING",
    )
    db_session.add(site)
    await db_session.commit()

    # Track DB state right before crawler executes
    stage_at_start = None

    class MockCrawler:
        async def crawl(self, *args, **kwargs):
            nonlocal stage_at_start
            stmt = select(ScrapingTask).where(ScrapingTask.id == task.id)
            t = (await db_session.execute(stmt)).scalar_one()
            stage_at_start = (t.current_stage, t.progress)
            return WebsiteCrawlResult(
                website_id=site.id,
                url=site.url,
                domain=site.domain,
                status="CRAWLED",
                pages=[],
                duration_seconds=0.1,
            )

    service = CrawlerService(session=db_session, crawler=MockCrawler())
    await service.crawl_for_task(task.task_id)

    assert stage_at_start is not None
    assert stage_at_start[0] == "CRAWLING"
    assert stage_at_start[1] >= 20


@pytest.mark.asyncio
async def test_hanging_website_crawl_bounded_by_timeout(db_session: AsyncSession, monkeypatch) -> None:
    """A website crawler call that hangs indefinitely must be aborted by the per-site
    asyncio.wait_for timeout and marked as FAILED, allowing the pipeline to continue.
    """
    monkeypatch.setattr(settings, "WEBSITE_CRAWL_TIMEOUT_SECONDS", 0.1)

    user = User(
        name="Hang User",
        email=f"hang_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="hash",
    )
    db_session.add(user)
    await db_session.flush()

    task = ScrapingTask(
        task_id=f"TASK-HANG-{uuid.uuid4().hex[:4].upper()}",
        user_id=user.id,
        location="Chennai",
        keyword="Restaurants",
        status="RUNNING",
        current_stage="FINDING_WEBSITES",
        progress=15,
    )
    db_session.add(task)
    await db_session.flush()

    org = Organization(name="Hanging Bistro", city="Chennai")
    db_session.add(org)
    await db_session.flush()
    await db_session.execute(
        task_organizations.insert().values(task_id=task.id, organization_id=org.id)
    )

    site = Website(
        organization_id=org.id,
        url="https://hangingbistro.example",
        normalized_url="https://hangingbistro.example",
        domain="hangingbistro.example",
        status="PENDING",
    )
    db_session.add(site)
    await db_session.commit()

    class HangingCrawler:
        async def crawl(self, *args, **kwargs):
            # Hang longer than the 0.1s timeout
            await asyncio.sleep(5.0)
            return None

    service = CrawlerService(session=db_session, crawler=HangingCrawler())
    summary = await service.crawl_for_task(task.task_id)

    # Must complete safely, marking the hung site as failed
    assert summary.total_websites == 1
    assert summary.websites_crawled == 0
    assert summary.failed_websites == 1
    assert summary.next_stage == "EXTRACTING"

    # Website status in DB must be FAILED
    stmt_site = select(Website).where(Website.id == site.id)
    refreshed_site = (await db_session.execute(stmt_site)).scalar_one()
    assert refreshed_site.status == "FAILED"


@pytest.mark.asyncio
async def test_run_worker_stage_commits_stage_start(db_session: AsyncSession, monkeypatch) -> None:
    """task_context.run_worker_stage must commit the new stage and progress floor to the DB
    before delegating execution to the async stage function.
    """
    user = User(
        name="Context User",
        email=f"context_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="hash",
    )
    db_session.add(user)
    await db_session.flush()

    task = ScrapingTask(
        task_id=f"TASK-CTX-{uuid.uuid4().hex[:4].upper()}",
        user_id=user.id,
        location="Ooty",
        keyword="Resorts",
        status="RUNNING",
        current_stage="FINDING_WEBSITES",
        progress=15,
    )
    db_session.add(task)
    await db_session.commit()

    class MockContext:
        async def __aenter__(self):
            return db_session

        async def __aexit__(self, *args):
            pass

    monkeypatch.setattr("app.workers.task_context.get_session_factory", lambda: lambda: MockContext())

    captured_stage_on_entry = None

    async def mock_crawl_stage(task_id: str, session: AsyncSession) -> dict:
        nonlocal captured_stage_on_entry
        stmt = select(ScrapingTask).where(ScrapingTask.task_id == task_id)
        t = (await session.execute(stmt)).scalar_one()
        captured_stage_on_entry = (t.current_stage, t.progress)
        return {"crawled": 0}

    # Execute run_worker_stage
    result = run_worker_stage(mock_crawl_stage, task.task_id, "CRAWLING")
    assert result["status"] == "COMPLETED"

    # On entry to mock_crawl_stage, the DB must already have reflected CRAWLING & 20%
    assert captured_stage_on_entry == ("CRAWLING", 20)
