"""
tests/test_discovery.py

Unit and integration tests for the Discovery Engine:
  • Query generation
  • URL and domain normalization
  • Duplicate candidate detection
  • Fixture discovery provider
  • Multi-provider execution & failure resilience
  • Ranking and official website candidate identification
  • Database persistence and task metrics
  • Idempotency (repeated runs do not create duplicate entities)
  • Max results capping
  • Task status & stage transitions
"""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.organization import Organization, task_organizations
from app.models.scraping_task import ScrapingTask
from app.models.website import Website
from app.schemas.discovery import DiscoveryCandidate
from app.schemas.task import ScrapingTaskCreate
from app.services.discovery import (
    DiscoveryManager,
    DiscoveryProvider,
    FixtureDiscoveryProvider,
    build_discovery_queries,
    normalize_organization_name,
    score_candidate,
)
from app.core.config import settings
from app.services.discovery_service import DiscoveryService
from app.services.task_service import TaskService
from app.utils.url import extract_domain, normalize_url


@pytest.fixture(autouse=True)
def enable_fixtures_for_unit_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "DISCOVERY_ENABLE_FIXTURES", True)


# ── 1. Query Generation Tests ─────────────────────────────────────────────────

def test_query_generation_deterministic() -> None:
    queries = build_discovery_queries("CBSE Schools", "Puducherry")
    assert len(queries) == 4
    assert queries[0] == "CBSE Schools in Puducherry"
    assert queries[1] == "CBSE Schools Puducherry official website"
    assert queries[2] == "CBSE Schools Puducherry contact"
    assert queries[3] == "CBSE Schools Puducherry"


# ── 2. URL & Domain Normalization Tests ────────────────────────────────────────

def test_url_normalization() -> None:
    # Casing and default port
    assert normalize_url("https://EXAMPLE.COM:443/about/") == "https://example.com/about"
    assert normalize_url("http://example.com:80/") == "http://example.com/"

    # Fragment removal
    assert normalize_url("https://example.com/page#home") == "https://example.com/page"

    # Tracking query param stripping & param sorting
    dirty_url = "https://example.com/list?utm_source=newsletter&beta=2&utm_medium=email&alpha=1"
    clean_url = normalize_url(dirty_url)
    assert "utm_source" not in clean_url
    assert "utm_medium" not in clean_url
    assert "alpha=1&beta=2" in clean_url

    # Domain extraction
    assert extract_domain("https://www.abcschool.example/about") == "abcschool.example"
    assert extract_domain("http://sub.school.edu.in:8080/") == "sub.school.edu.in"


# ── 3. Name Normalization & Ranking Tests ─────────────────────────────────────

def test_name_normalization() -> None:
    raw = "  ABC International School - Official Website  "
    assert normalize_organization_name(raw) == "ABC International School"

    html_raw = "Saint Mary&#39;s &amp; Joseph High School | Home"
    assert normalize_organization_name(html_raw) == "Saint Mary's & Joseph High School"


def test_candidate_scoring() -> None:
    cand = DiscoveryCandidate(
        name="ABC CBSE Senior School",
        url="https://abcschool.example",
        domain="abcschool.example",
        source="FIXTURE",
        location="Puducherry",
        category="CBSE Schools",
    )
    score = score_candidate(cand, target_keyword="CBSE Schools", target_location="Puducherry")
    assert score >= 70.0  # Strong relevance


# ── 4. Fixture Provider Tests ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_fixture_provider_deterministic() -> None:
    provider = FixtureDiscoveryProvider()
    candidates = await provider.search(keyword="CBSE Schools", location="Puducherry", limit=10)
    assert len(candidates) >= 5
    domains = [c.domain for c in candidates]
    assert "abcschool.example" in domains
    assert "xyzschool.example" in domains


# ── 5. Provider Resilience & Failure Handling ─────────────────────────────────

class FailingProvider(DiscoveryProvider):
    name = "failing_provider"

    async def search(self, *, keyword: str, location: str, limit: int = 50) -> list[DiscoveryCandidate]:
        raise ConnectionError("Mock network timeout / DNS failure")


@pytest.mark.asyncio
async def test_discovery_manager_resilience_to_failed_provider() -> None:
    manager = DiscoveryManager(
        providers=[
            FailingProvider(),
            FixtureDiscoveryProvider(),
        ]
    )
    candidates, duplicates, stats, errors = await manager.discover(
        keyword="CBSE Schools",
        location="Puducherry",
        max_results=10,
    )
    # The failing provider is logged and recorded in errors, but candidates from Fixture are preserved!
    assert len(errors) == 1
    assert "failing_provider" in errors[0]
    assert len(candidates) > 0
    assert duplicates >= 1  # From intentional fixture duplicate


# ── 6. Discovery Service Integration & Database Persistence ───────────────────

@pytest.mark.asyncio
async def test_discover_for_task_lifecycle(db_session: AsyncSession) -> None:
    # 1. Create task
    task_service = TaskService(db_session)
    task_in = ScrapingTaskCreate(
        location="Puducherry",
        keyword="CBSE Schools",
        max_results=10,
        selected_fields=["name", "website", "phone", "email"],
    )
    task = await task_service.create_task(task_in)
    assert task.status == "PENDING"
    assert task.current_stage == "CREATING_TASK"
    assert task.progress == 0

    # 2. Run discovery service
    discovery_service = DiscoveryService(
        db_session,
        manager=DiscoveryManager([FixtureDiscoveryProvider()]),
    )
    result = await discovery_service.discover_for_task(task.task_id)

    assert result.accepted_candidates > 0
    assert result.websites_found > 0

    # 3. Verify task status & stage progression (Section 41)
    refreshed_task = await task_service.get_task(task.task_id)
    assert refreshed_task.status == "RUNNING"
    assert refreshed_task.current_stage == "FINDING_WEBSITES"
    assert refreshed_task.progress > 0
    assert refreshed_task.results_discovered > 0
    assert refreshed_task.websites_found > 0
    assert refreshed_task.websites_crawled == 0  # No crawling in Step 4!

    # 4. Verify Organizations and Websites persisted with PENDING status (Section 29)
    stmt_sites = select(Website)
    sites = (await db_session.execute(stmt_sites)).scalars().all()
    assert len(sites) >= 5
    for s in sites:
        assert s.status == "PENDING"

    # 5. Verify task_organizations links created
    stmt_links = select(task_organizations).where(task_organizations.c.task_id == task.id)
    links = (await db_session.execute(stmt_links)).all()
    assert len(links) == refreshed_task.results_discovered


# ── 7. Max Results Capping ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_max_results_capping(db_session: AsyncSession) -> None:
    task_service = TaskService(db_session)
    task_in = ScrapingTaskCreate(
        location="Puducherry",
        keyword="CBSE Schools",
        max_results=2,  # Cap strictly at 2
        selected_fields=["name", "website"],
    )
    task = await task_service.create_task(task_in)

    discovery_service = DiscoveryService(
        db_session,
        manager=DiscoveryManager([FixtureDiscoveryProvider()]),
    )
    result = await discovery_service.discover_for_task(task.task_id)

    assert result.accepted_candidates == 2

    refreshed = await task_service.get_task(task.task_id)
    assert refreshed.results_discovered == 2


# ── 8. Idempotency Test (Section 40) ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_discovery_idempotency(db_session: AsyncSession) -> None:
    task_service = TaskService(db_session)
    task_in = ScrapingTaskCreate(
        location="Puducherry",
        keyword="CBSE Schools",
        max_results=10,
        selected_fields=["name", "website"],
    )
    task = await task_service.create_task(task_in)

    discovery_service = DiscoveryService(
        db_session,
        manager=DiscoveryManager([FixtureDiscoveryProvider()]),
    )

    # First run
    res1 = await discovery_service.discover_for_task(task.task_id)

    # Query initial counts
    orgs_count_1 = len((await db_session.execute(select(Organization))).scalars().all())
    sites_count_1 = len((await db_session.execute(select(Website))).scalars().all())
    links_count_1 = len((await db_session.execute(select(task_organizations))).all())

    # Second run (should be completely idempotent)
    res2 = await discovery_service.discover_for_task(task.task_id)

    orgs_count_2 = len((await db_session.execute(select(Organization))).scalars().all())
    sites_count_2 = len((await db_session.execute(select(Website))).scalars().all())
    links_count_2 = len((await db_session.execute(select(task_organizations))).all())

    assert orgs_count_1 == orgs_count_2
    assert sites_count_1 == sites_count_2
    assert links_count_1 == links_count_2


# ── 9. Error Handling ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_discover_task_not_found(db_session: AsyncSession) -> None:
    discovery_service = DiscoveryService(db_session)
    with pytest.raises(AppException) as exc_info:
        await discovery_service.discover_for_task("TASK-999999")
    assert exc_info.value.code == "TASK_NOT_FOUND"
    assert exc_info.value.status_code == 404
