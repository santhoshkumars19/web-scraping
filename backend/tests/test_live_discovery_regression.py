"""
tests/test_live_discovery_regression.py

Regression test suite for Step 16A:
Validates that mock data, .example domains, and fabricated records NEVER appear
in production discovery, and verifies real public discovery normalization, reachability,
source provenance, and deduplication.
"""

from __future__ import annotations

import re
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.lead import Lead
from app.models.organization import Organization
from app.models.website import Website
from app.schemas.discovery import DiscoveryCandidate
from app.schemas.task import ScrapingTaskCreate
from app.services.discovery import (
    DiscoveryManager,
    FixtureDiscoveryProvider,
    normalize_organization_name,
)
from app.services.discovery.public_search import PublicSearchProvider
from app.services.discovery.website_validator import validate_website_reachability
from app.services.discovery_service import DiscoveryService
from app.services.lead_service import LeadService
from app.services.task_service import TaskService
from app.utils.url import normalize_url


# ── 1. Production Provider Defaults ──────────────────────────────────────────

def test_production_discovery_manager_excludes_fixture_provider():
    """DiscoveryManager default providers must NOT include FixtureDiscoveryProvider in production."""
    settings.DISCOVERY_ENABLE_FIXTURES = False
    manager = DiscoveryManager()
    provider_types = [type(p) for p in manager.providers]

    assert FixtureDiscoveryProvider not in provider_types
    assert any(isinstance(p, PublicSearchProvider) for p in manager.providers)


# ── 2. Rejection of .example and Mock Domains in Production ───────────────────

@pytest.mark.asyncio
async def test_production_discovery_rejects_example_and_fixture_candidates():
    """Production discovery manager must drop any candidate with .example domain or fixture source."""
    settings.DISCOVERY_ENABLE_FIXTURES = False

    class MockLeakingProvider:
        name = "leaking_provider"

        async def is_available(self) -> bool:
            return True

        async def search(self, *, keyword: str, location: str, limit: int = 50) -> list[DiscoveryCandidate]:
            return [
                DiscoveryCandidate(
                    name="Fake Hotel 1",
                    url="https://fake-hotel-1.example",
                    domain="fake-hotel-1.example",
                    source="FIXTURE",
                    source_url="fixture://local-dataset",
                    address="10 Main Street, Ooty",
                    location=location,
                    category=keyword,
                ),
                DiscoveryCandidate(
                    name="Fake Hotel 2",
                    url="https://fake-hotel-2.invalid",
                    domain="fake-hotel-2.invalid",
                    source="LEAKED",
                    source_url="http://leaked.com",
                    address="20 Main Street, Ooty",
                    location=location,
                    category=keyword,
                ),
                DiscoveryCandidate(
                    name="The Grange Hotel",
                    url="https://thegrangehotel.in/",
                    domain="thegrangehotel.in",
                    source="PUBLIC_SEARCH",
                    source_url="https://nominatim.openstreetmap.org",
                    address="Coonoor Road, Beside Indian Oil Petrol Bunk, Ooty, Tamil Nadu - 643001",
                    location=location,
                    category=keyword,
                    is_official_candidate=True,
                ),
            ]

    manager = DiscoveryManager(providers=[MockLeakingProvider()])
    candidates, duplicates, stats, errors = await manager.discover(
        keyword="Restaurants",
        location="Ooty",
        max_results=10,
    )

    candidate_names = [c.name for c in candidates]
    candidate_urls = [c.url for c in candidates]
    candidate_addresses = [c.address for c in candidates if c.address]

    # The 2 mock candidates must be strictly excluded!
    assert "Fake Hotel 1" not in candidate_names
    assert "Fake Hotel 2" not in candidate_names
    assert not any(".example" in u for u in candidate_urls)
    assert not any(".invalid" in u for u in candidate_urls)
    assert not any("Main Street" in a for a in candidate_addresses)

    # The real candidate must be preserved!
    assert "The Grange Hotel" in candidate_names
    assert "https://thegrangehotel.in/" in candidate_urls


# ── 3. Website Reachability Validation ────────────────────────────────────────

@pytest.mark.asyncio
async def test_website_reachability_rejects_example_domains():
    """Website validator must reject .example domains without network lookup."""
    res = await validate_website_reachability("https://ooty-restaurants-1.example")
    assert res.is_reachable is False
    assert "Disallowed domain" in (res.error or "")


@pytest.mark.asyncio
async def test_website_reachability_rejects_ssrf_and_private_hosts():
    """Website validator must reject internal / private hosts."""
    res = await validate_website_reachability("http://127.0.0.1:8000/api")
    assert res.is_reachable is False
    assert "SSRF blocked" in (res.error or "")


# ── 4. Missing Fields Remain Null / Empty ──────────────────────────────────────

@pytest.mark.asyncio
async def test_missing_fields_never_fabricated(db_session: AsyncSession):
    """When an organization has no phone, email, or website, LeadService must return None (not placeholders)."""
    task_service = TaskService(db_session)
    task_in = ScrapingTaskCreate(
        location="Ooty",
        keyword="Restaurants",
        max_results=5,
        selected_fields=["name", "phone", "email", "website", "address"],
    )
    task = await task_service.create_task(task_in)

    # Add organization with only name and location, no phone, email, or website
    org = Organization(name="Authentic Tea Room", city="Ooty", category="Restaurants")
    db_session.add(org)
    await db_session.flush()

    lead = Lead(task_id=task.id, organization_id=org.id, verification_status="PENDING")
    db_session.add(lead)
    await db_session.commit()

    service = LeadService(db_session)
    lead_dto = await service.get_lead(lead.id)

    assert lead_dto.organization.website is None
    assert len(lead_dto.phones) == 0
    assert len(lead_dto.emails) == 0

    # Also verify the LeadListItem representation (used by Leads Table)
    leads_list, count, _ = await service.list_leads(task_id=task.task_id)
    assert count == 1
    item = leads_list[0]
    assert item.website is None
    assert item.phone is None
    assert item.email is None
    assert item.whatsapp is None
    assert item.contact_person is None


# ── 5. Source Provenance Preservation ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_source_url_preserved_in_discovery_candidates():
    """Candidate results must retain original discovery source URL."""
    cand = DiscoveryCandidate(
        name="The Grange Hotel",
        url="https://thegrangehotel.in/",
        domain="thegrangehotel.in",
        source="PUBLIC_SEARCH",
        source_url="https://nominatim.openstreetmap.org/search?q=restaurants+in+Ooty",
        location="Ooty",
        category="Restaurants",
    )
    assert cand.source_url == "https://nominatim.openstreetmap.org/search?q=restaurants+in+Ooty"
    assert cand.source == "PUBLIC_SEARCH"
    assert "thegrangehotel.in" in cand.url


# ── 6. Deduplication of Real Organizations ─────────────────────────────────────

@pytest.mark.asyncio
async def test_deduplication_merges_identical_domains():
    """Multiple candidates pointing to the same business domain must be deduplicated."""
    manager = DiscoveryManager(providers=[])
    candidates = [
        DiscoveryCandidate(
            name="The Grange Hotel",
            url="https://thegrangehotel.in/",
            domain="thegrangehotel.in",
            source="PUBLIC_SEARCH",
            location="Ooty",
        ),
        DiscoveryCandidate(
            name="The Grange Hotel Restaurant & Dining",
            url="https://thegrangehotel.in/restaurant/",
            domain="thegrangehotel.in",
            source="PUBLIC_SEARCH",
            location="Ooty",
        ),
    ]

    class MultiCandidateProvider:
        name = "multi"
        async def is_available(self): return True
        async def search(self, **kwargs): return candidates

    manager.providers = [MultiCandidateProvider()]
    results, duplicates, stats, errors = await manager.discover(
        keyword="Restaurants",
        location="Ooty",
    )

    assert len(results) == 1
    assert duplicates == 1
    assert results[0].domain == "thegrangehotel.in"
