"""
app/services/extraction/social_extractor.py

Extracts and normalizes official social media profile links.
"""

from __future__ import annotations

from urllib.parse import urlparse

from app.services.extraction.base import ExtractedItem, PageContext, ParsedPage
from app.services.extraction.patterns import SOCIAL_PLATFORM_DOMAINS
from app.utils.url import normalize_url

IGNORED_SOCIAL_PATHS = {
    "", "/", "/share", "/sharer", "/sharer.php", "/intent", "/share-offsite",
    "/home", "/feed", "/watch", "/login", "/signup",
}


class SocialExtractor:
    """Specialized extractor for official organization social media profiles."""

    @classmethod
    def extract(cls, page: ParsedPage, context: PageContext) -> list[ExtractedItem]:
        """Extract valid social profile URLs from the parsed page."""
        items: list[ExtractedItem] = []
        seen_urls: set[str] = set()

        for a in page.anchors:
            href = a.get("href", "").strip()
            if not href or href.startswith("#"):
                continue

            parsed = urlparse(href)
            if parsed.scheme.lower() not in ("http", "https"):
                continue

            # Identify platform
            platform = cls._identify_platform(parsed.netloc)
            if not platform:
                continue

            # Exclude generic share links and homepages
            clean_path = parsed.path.rstrip("/")
            if clean_path in IGNORED_SOCIAL_PATHS or "share" in clean_path.lower():
                continue

            try:
                norm_url = normalize_url(href)
            except Exception:
                norm_url = href

            if norm_url in seen_urls:
                continue
            seen_urls.add(norm_url)

            items.append(
                ExtractedItem(
                    field_name="SOCIAL_LINK",
                    raw_value=href,
                    normalized_value=norm_url,
                    method="anchor_link",
                    metadata={
                        "platform": platform,
                        "is_official": True,
                    },
                )
            )

        return items

    @classmethod
    def _identify_platform(cls, netloc: str) -> str | None:
        """Match domain to supported social platform enum."""
        for regex, platform_name in SOCIAL_PLATFORM_DOMAINS:
            if regex.search(netloc):
                return platform_name
        return None
