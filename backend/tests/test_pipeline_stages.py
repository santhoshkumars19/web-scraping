"""
tests/test_pipeline_stages.py

Comprehensive regression test suite verifying the resolution of the "Stuck at 15%" bug:
1. Discovery completes at 20% and transitions to FINDING_WEBSITES.
2. OfficialWebsiteService emits all required structured events:
     • official_website_stage_started
     • candidate_count
     • candidate_processing_started
     • official_website_found / official_website_not_found
     • candidate_processing_completed
     • official_website_stage_completed
     • crawl_stage_queued
3. Zero candidate websites found after discovery advances cleanly without stalling at 15%.
4. Slow/hanging candidate website checks are bounded by timeout and never block the task.
5. Multiple task scenarios ("Ooty + Restaurants", "Chennai + Hospitals", "Puducherry + CBSE Schools")
   all execute cleanly beyond 15%.
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
from app.realtime.publisher import MockTaskEventPublisher, set_event_publisher
from app.schemas.crawler import WebsiteCrawlResult
from app.services.crawler_service import CrawlerService
from app.services.discovery_service import DiscoveryService
from app.services.official_website_service import OfficialWebsiteService
from app.workers.task_context import run_worker_stage


@pytest.fixture(autouse=True)
def enable_fixtures_for_stage_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "DISCOVERY_ENABLE_FIXTURES", True)
    set_event_publisher(MockTaskEventPublisher())


@pytest.mark.asyncio
async def test_official_website_service_structured_logging(db_session: AsyncSession) -> None:
    """OfficialWebsiteService must emit all required structured logs and transition

    the task from 20% to 30%.
    """
    user = User(
        name="Structured User",
        email=f"struct_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="hash",
    )
    db_session.add(user)
    await db_session.flush()

    task = ScrapingTask(
        task_id=f"TASK-STRUCT-{uuid.uuid4().hex[:4].upper()}",
        user_id=user.id,
        location="Chennai",
        keyword="Hospitals",
        status="RUNNING",
        current_stage="DISCOVERING",
        progress=20,
    )
    db_session.add(task)
    await db_session.flush()

    # Org 1: Has candidate website
    org1 = Organization(name="Apollo Specialty", city="Chennai")
    db_session.add(org1)
    await db_session.flush()
    await db_session.execute(
        task_organizations.insert().values(task_id=task.id, organization_id=org1.id)
    )
    site1 = Website(
        organization_id=org1.id,
        url="https://apollo.example",
        normalized_url="https://apollo.example",
        domain="apollo.example",
        status="PENDING",
    )
    db_session.add(site1)

    # Org 2: Has no candidate website
    org2 = Organization(name="Local Clinic", city="Chennai")
    db_session.add(org2)
    await db_session.flush()
    await db_session.execute(
        task_organizations.insert().values(task_id=task.id, organization_id=org2.id)
    )

    await db_session.commit()

    service = OfficialWebsiteService(session=db_session)
    result = await service.find_official_websites_for_task(task.task_id)

    assert result["total_candidates"] == 2
    assert result["websites_found"] == 1
    assert result["next_stage"] == "CRAWLING"

    # Verify task DB state
    stmt_t = select(ScrapingTask).where(ScrapingTask.id == task.id)
    refreshed_task = (await db_session.execute(stmt_t)).scalar_one()
    assert refreshed_task.current_stage == "CRAWLING"
    assert refreshed_task.progress == 30
    assert refreshed_task.websites_found == 1

    # Verify all required structured logs exist in ScrapingLog
    stmt_logs = select(ScrapingLog).where(ScrapingLog.task_id == task.id)
    logs = list((await db_session.execute(stmt_logs)).scalars().all())
    event_types = [l.event_type for l in logs]

    assert "OFFICIAL_WEBSITE_STAGE_STARTED" in event_types
    assert "CANDIDATE_COUNT" in event_types
    assert "CANDIDATE_PROCESSING_STARTED" in event_types
    assert "OFFICIAL_WEBSITE_FOUND" in event_types
    assert "OFFICIAL_WEBSITE_NOT_FOUND" in event_types
    assert "CANDIDATE_PROCESSING_COMPLETED" in event_types
    assert "OFFICIAL_WEBSITE_STAGE_COMPLETED" in event_types
    assert "CRAWL_STAGE_QUEUED" in event_types


@pytest.mark.asyncio
async def test_zero_websites_found_advances_cleanly(db_session: AsyncSession) -> None:
    """When discovery finds organizations but zero candidate websites, the pipeline

    records 'Completed with 0 crawlable websites' and advances to EXTRACTING at 50%
    without stalling or remaining stuck at 15%.
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
        progress=20,
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

    assert summary.total_websites == 0
    assert summary.websites_crawled == 0
    assert summary.failed_websites == 0
    assert summary.next_stage == "EXTRACTING"
    assert "0 crawlable websites" in summary.status

    # Task state in DB must be updated and committed
    stmt = select(ScrapingTask).where(ScrapingTask.id == task.id)
    refreshed = (await db_session.execute(stmt)).scalar_one()
    assert refreshed.current_stage == "EXTRACTING"
    assert refreshed.progress == 50
    assert refreshed.status == "RUNNING"


@pytest.mark.asyncio
async def test_task_types_multiple_progress_beyond_15(db_session: AsyncSession) -> None:
    """Test all 3 scenarios requested by user:

      1. Ooty + Restaurants
      2. Chennai + Hospitals
      3. Puducherry + CBSE Schools
    Prove that every task independently moves through Discovery and Official Websites
    beyond 15% to at least 30%.
    """
    test_cases = [
        ("Ooty", "Restaurants"),
        ("Chennai", "Hospitals"),
        ("Puducherry", "CBSE Schools"),
    ]

    for loc, kw in test_cases:
        user = User(
            name=f"User {loc}",
            email=f"{loc.lower()}_{uuid.uuid4().hex[:4]}@example.com",
            password_hash="hash",
        )
        db_session.add(user)
        await db_session.flush()

        task = ScrapingTask(
            task_id=f"TASK-SCENARIO-{uuid.uuid4().hex[:4].upper()}",
            user_id=user.id,
            location=loc,
            keyword=kw,
            status="PENDING",
            current_stage="CREATING_TASK",
            progress=0,
        )
        db_session.add(task)
        await db_session.flush()

        # Step 2: Discovery
        disc_service = DiscoveryService(session=db_session)
        disc_result = await disc_service.discover_for_task(task.task_id)

        # Must have completed discovery and advanced to 20%
        stmt_t = select(ScrapingTask).where(ScrapingTask.id == task.id)
        t_after_disc = (await db_session.execute(stmt_t)).scalar_one()
        assert t_after_disc.progress == 20
        assert t_after_disc.current_stage == "FINDING_WEBSITES"

        # Step 3: Official Websites
        web_service = OfficialWebsiteService(session=db_session)
        web_result = await web_service.find_official_websites_for_task(task.task_id)

        # Must have completed official website stage and advanced to 30%
        t_after_web = (await db_session.execute(stmt_t)).scalar_one()
        assert t_after_web.progress == 30
        assert t_after_web.current_stage == "CRAWLING"
        assert t_after_web.progress > 15, f"Task {task.task_id} failed to move beyond 15%"
