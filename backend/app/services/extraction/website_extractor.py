"""
app/services/extraction/website_extractor.py

Extracts canonical website URL and domain signals.
"""

from __future__ import annotations

from app.services.extraction.base import ExtractedItem, PageContext, ParsedPage
from app.utils.url import extract_domain, normalize_url


class WebsiteExtractor:
    """Specialized extractor for canonical website URL and domain verification."""

    @classmethod
    def extract(cls, page: ParsedPage, context: PageContext) -> list[ExtractedItem]:
        """Extract canonical website references."""
        items: list[ExtractedItem] = []

        # 1. Canonical tag
        canonical_tag = page.soup.find("link", rel="canonical")
        if canonical_tag and canonical_tag.get("href"):
            raw_url = canonical_tag["href"].strip()
            domain = extract_domain(raw_url)
            if domain:
                try:
                    norm = normalize_url(raw_url)
                except Exception:
                    norm = raw_url

                items.append(
                    ExtractedItem(
                        field_name="WEBSITE",
                        raw_value=raw_url,
                        normalized_value=norm,
                        method="canonical_tag",
                        metadata={"domain": domain},
                    )
                )

        # 2. JSON-LD URL
        for obj in page.json_ld:
            url_val = obj.get("url")
            if isinstance(url_val, str) and url_val.startswith("http"):
                domain = extract_domain(url_val)
                if domain:
                    try:
                        norm = normalize_url(url_val)
                    except Exception:
                        norm = url_val

                    items.append(
                        ExtractedItem(
                            field_name="WEBSITE",
                            raw_value=url_val,
                            normalized_value=norm,
                            method="json_ld",
                            metadata={"domain": domain},
                        )
                    )

        return items
