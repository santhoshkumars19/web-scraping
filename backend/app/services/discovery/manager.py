"""
app/services/discovery/manager.py

DiscoveryManager orchestrating multiple discovery providers, deduplication, ranking, and limit enforcement.
"""

from __future__ import annotations

from typing import Sequence

import re

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.discovery import DiscoveryCandidate
from app.services.discovery.base import DiscoveryProvider
from app.services.discovery.fixture_provider import FixtureDiscoveryProvider
from app.services.discovery.normalizer import (
    create_dedup_name_key,
    normalize_location_text,
    normalize_organization_name,
)
from app.services.discovery.public_search import PublicSearchProvider
from app.services.discovery.ranking import (
    DIRECTORY_DOMAINS,
    is_candidate_official_website,
    score_candidate,
)
from app.services.discovery.user_url_provider import UserURLProvider
from app.utils.url import extract_domain, normalize_url

logger = get_logger(__name__)


class DiscoveryManager:
    """Coordinates discovery across registered providers, deduplicating and ranking results."""

    def __init__(
        self,
        providers: Sequence[DiscoveryProvider] | None = None,
        *,
        min_relevance_score: float = 50.0,
    ) -> None:
        if providers is not None:
            self.providers = list(providers)
        else:
            # Production default provider registry: live public web search + user urls
            # Fixtures are strictly excluded from normal production flow.
            self.providers = [
                PublicSearchProvider(enabled=True),
                UserURLProvider(),
            ]
            if getattr(settings, "DISCOVERY_ENABLE_FIXTURES", False):
                self.providers.insert(0, FixtureDiscoveryProvider())
        self.min_relevance_score = min_relevance_score

    def register_provider(self, provider: DiscoveryProvider) -> None:
        """Add an additional discovery provider to the manager."""
        self.providers.append(provider)

    async def discover(
        self,
        *,
        keyword: str,
        location: str,
        max_results: int = 100,
    ) -> tuple[list[DiscoveryCandidate], int, dict[str, int], list[str]]:
        """Execute discovery across all providers, deduplicating and ranking results.

        Returns:
            Tuple of:
              - accepted_candidates (ranked, capped at max_results)
              - duplicates_removed count
              - provider_stats dictionary
              - errors list (recorded from failing providers)
        """
        raw_candidates: list[DiscoveryCandidate] = []
        provider_stats: dict[str, int] = {}
        errors: list[str] = []

        for provider in self.providers:
            p_name = getattr(provider, "name", type(provider).__name__)
            try:
                available = await provider.is_available()
                if not available:
                    logger.debug("Provider %s is not available; skipping.", p_name)
                    continue

                logger.info("Discovery provider %s started", p_name)
                candidates = await provider.search(
                    keyword=keyword,
                    location=location,
                    limit=max_results,
                )
                raw_candidates.extend(candidates)
                provider_stats[p_name] = len(candidates)
                logger.info("%d candidates returned from provider %s", len(candidates), p_name)

            except Exception as exc:
                err_msg = f"Provider {p_name} failed: {exc}"
                logger.warning(err_msg)
                errors.append(err_msg)
                provider_stats[p_name] = 0
                # Continue with other providers; do not fail whole pipeline

        # ── 1. Normalization ──────────────────────────────────────────────────
        normalized_candidates: list[DiscoveryCandidate] = []
        for c in raw_candidates:
            clean_name = normalize_organization_name(c.name)
            clean_url = normalize_url(c.url)
            domain = extract_domain(clean_url) or c.domain

            if not clean_name or not clean_url:
                continue

            # Production guardrails: strictly reject mock / fake / example domains
            fixtures_enabled = getattr(settings, "DISCOVERY_ENABLE_FIXTURES", False)
            if not fixtures_enabled:
                domain_lower = (domain or "").lower()
                if any(domain_lower.endswith(sfx) or domain_lower == sfx.lstrip(".") for sfx in (".example", ".invalid", ".test", ".localhost", ".local")):
                    logger.debug("Rejected fake domain '%s' in production mode", domain_lower)
                    continue
                if (c.source or "").upper() == "FIXTURE" or "fixture://" in (c.source_url or "").lower():
                    logger.debug("Rejected fixture candidate '%s' in production mode", clean_name)
                    continue
                # Reject generated sequential fake addresses like "10 Main Street, Ooty"
                if c.address and re.search(r"^\d+\s+Main\s+Street\b", c.address.strip(), re.IGNORECASE):
                    logger.debug("Rejected fake address '%s' for '%s'", c.address, clean_name)
                    continue

            normalized_candidates.append(
                DiscoveryCandidate(
                    name=clean_name,
                    category=c.category or keyword,
                    location=normalize_location_text(c.location) or location,
                    url=clean_url,
                    domain=domain,
                    source=c.source,
                    source_url=c.source_url,
                    title=c.title,
                    description=c.description,
                    address=c.address,
                    phone=c.phone,
                    email=c.email,
                    confidence=c.confidence,
                )
            )

        # ── 2. Deduplication ──────────────────────────────────────────────────
        seen_domains: set[str] = set()
        seen_name_keys: set[str] = set()
        unique_candidates: list[DiscoveryCandidate] = []
        duplicates_removed = 0

        for candidate in normalized_candidates:
            domain_key = ""
            if candidate.domain:
                d_lower = candidate.domain.lower()
                is_dir_or_portal = (
                    any(d in d_lower for d in DIRECTORY_DOMAINS)
                    or d_lower in ("openstreetmap.org", "www.openstreetmap.org", "duckduckgo.com", "html.duckduckgo.com")
                )
                if not is_dir_or_portal:
                    domain_key = d_lower

            name_key = create_dedup_name_key(candidate.name)

            is_duplicate = False
            if domain_key and domain_key in seen_domains:
                is_duplicate = True
            elif name_key and name_key in seen_name_keys:
                is_duplicate = True

            if is_duplicate:
                duplicates_removed += 1
                logger.debug("Duplicate candidate removed: %s (%s)", candidate.name, candidate.url)
            else:
                if domain_key:
                    seen_domains.add(domain_key)
                if name_key:
                    seen_name_keys.add(name_key)
                unique_candidates.append(candidate)

        logger.info("%d duplicate candidates removed", duplicates_removed)

        # ── 3. Ranking & Scoring ──────────────────────────────────────────────
        ranked_candidates: list[DiscoveryCandidate] = []
        for cand in unique_candidates:
            score = score_candidate(
                cand,
                target_keyword=keyword,
                target_location=location,
            )
            cand.confidence = score
            cand.is_official_candidate = is_candidate_official_website(cand)

            if score >= self.min_relevance_score:
                ranked_candidates.append(cand)

        # Sort descending by confidence score
        ranked_candidates.sort(key=lambda x: x.confidence, reverse=True)

        # ── 4. Limit to max_results ───────────────────────────────────────────
        accepted = ranked_candidates[:max_results]
        logger.info("%d organizations accepted (capped at max_results=%d)", len(accepted), max_results)

        return accepted, duplicates_removed, provider_stats, errors
