"""
app/services/discovery/user_url_provider.py

Provider for processing direct, user-specified seed URLs.
"""

from __future__ import annotations

from app.schemas.discovery import DiscoveryCandidate
from app.services.discovery.base import DiscoveryProvider
from app.utils.url import extract_domain, normalize_url


class UserURLProvider(DiscoveryProvider):
    """Generates high-confidence discovery candidates from direct user-provided URLs."""

    name = "user_url"

    def __init__(self, seed_urls: list[str] | None = None) -> None:
        self.seed_urls = seed_urls or []

    async def search(
        self,
        *,
        keyword: str,
        location: str,
        limit: int = 50,
    ) -> list[DiscoveryCandidate]:
        candidates: list[DiscoveryCandidate] = []
        for url in self.seed_urls[:limit]:
            clean_url = normalize_url(url)
            domain = extract_domain(clean_url)
            if not domain:
                continue

            # Fallback name based on domain label
            display_name = domain.split(".")[0].replace("-", " ").title()
            candidates.append(
                DiscoveryCandidate(
                    name=display_name,
                    category=keyword,
                    location=location,
                    url=clean_url,
                    domain=domain,
                    source="USER_URL",
                    source_url=clean_url,
                    title=f"{display_name} (User Provided)",
                    confidence=95.0,
                    is_official_candidate=True,
                )
            )
        return candidates
