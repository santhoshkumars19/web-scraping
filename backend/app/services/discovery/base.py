"""
app/services/discovery/base.py

Abstract base interface for discovery providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.discovery import DiscoveryCandidate


class DiscoveryProvider(ABC):
    """Base interface for all discovery source providers (fixtures, search engines, directories)."""

    name: str = "base"

    @abstractmethod
    async def search(
        self,
        *,
        keyword: str,
        location: str,
        limit: int = 50,
    ) -> list[DiscoveryCandidate]:
        """Query the provider for candidate organizations and websites.

        Args:
            keyword: Industry/category search query (e.g. "CBSE Schools").
            location: Geographical region (e.g. "Puducherry").
            limit: Maximum candidate limit requested from this provider.

        Returns:
            List of normalized DiscoveryCandidate objects.
        """
        ...

    async def is_available(self) -> bool:
        """Check if provider dependencies or network configurations are ready."""
        return True
