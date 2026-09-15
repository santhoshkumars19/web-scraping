"""
app/services/discovery/__init__.py

Discovery Engine package exports.
"""

from app.services.discovery.base import DiscoveryProvider
from app.services.discovery.fixture_provider import FixtureDiscoveryProvider
from app.services.discovery.manager import DiscoveryManager
from app.services.discovery.normalizer import (
    create_dedup_name_key,
    normalize_location_text,
    normalize_organization_name,
)
from app.services.discovery.public_search import PublicSearchProvider
from app.services.discovery.query_builder import build_discovery_queries
from app.services.discovery.ranking import is_candidate_official_website, score_candidate
from app.services.discovery.user_url_provider import UserURLProvider

__all__ = [
    "DiscoveryProvider",
    "DiscoveryManager",
    "FixtureDiscoveryProvider",
    "PublicSearchProvider",
    "UserURLProvider",
    "build_discovery_queries",
    "normalize_organization_name",
    "create_dedup_name_key",
    "normalize_location_text",
    "score_candidate",
    "is_candidate_official_website",
]
