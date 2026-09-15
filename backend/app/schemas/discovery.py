"""
app/schemas/discovery.py

Data Transfer Objects (DTOs) for the Discovery Engine.
"""

from __future__ import annotations

from app.schemas.base import AppBaseModel


class DiscoveryCandidate(AppBaseModel):
    """Represents an unverified candidate organization and website discovered from a source."""

    name: str
    url: str
    domain: str
    source: str
    source_url: str | None = None
    title: str | None = None
    description: str | None = None
    location: str | None = None
    category: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    confidence: float = 0.0
    is_official_candidate: bool = False


class DiscoveryResult(AppBaseModel):
    """Summary of the execution of a discovery operation for a task."""

    task_id: str
    total_candidates: int = 0
    accepted_candidates: int = 0
    duplicates_removed: int = 0
    organizations_created: int = 0
    organizations_reused: int = 0
    websites_found: int = 0
    provider_results: dict[str, int] = {}
    errors: list[str] = []
