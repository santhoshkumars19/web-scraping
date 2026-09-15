"""
app/services/extraction/base.py

Base classes, data transfer objects, and reusable parsed page representation.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from typing import Any

from bs4 import BeautifulSoup, Tag

from app.core.logging import get_logger
from app.services.extraction.normalizer import clean_text

logger = get_logger(__name__)


@dataclass
class PageContext:
    """Contextual metadata about the page being extracted."""

    task_id: uuid.UUID
    organization_id: uuid.UUID
    source_page_id: uuid.UUID
    source_url: str
    website_id: uuid.UUID | None = None
    page_type: str = "OTHER"
    page_title: str | None = None


@dataclass
class ExtractedItem:
    """A single extracted data point with provenance and extraction method."""

    field_name: str  # PHONE, EMAIL, ADDRESS, CONTACT_PERSON, SOCIAL_LINK, etc.
    raw_value: str
    normalized_value: str
    method: str  # tel_link, mailto_link, address_element, staff_card, json_ld, regex, etc.
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractionResult:
    """Aggregated extraction results for a single SourcePage."""

    context: PageContext
    items: list[ExtractedItem] = field(default_factory=list)


class ParsedPage:
    """Reusable parsed DOM representation to avoid reparsing HTML multiple times."""

    def __init__(self, html: str, base_url: str = "") -> None:
        self.raw_html = html
        self.base_url = base_url

        try:
            self.soup = BeautifulSoup(html, "lxml")
        except Exception:
            self.soup = BeautifulSoup(html, "html.parser")

        # Decompose non-content elements for visible text extraction
        text_soup = BeautifulSoup(html, "html.parser")
        for tag in text_soup(["script", "style", "meta", "noscript", "svg"]):
            tag.decompose()

        self.visible_text = clean_text(" ".join(text_soup.stripped_strings))
        self.visible_text_lower = self.visible_text.lower()

        # Precompute commonly queried collections
        self.anchors: list[Tag] = self.soup.find_all("a", href=True)
        self.address_tags: list[Tag] = self.soup.find_all("address")
        self.h1_tags: list[Tag] = self.soup.find_all("h1")

        # Extract Schema.org JSON-LD scripts
        self.json_ld: list[dict[str, Any]] = self._parse_json_ld()

    def _parse_json_ld(self) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for script in self.soup.find_all("script", type="application/ld+json"):
            if not script.string:
                continue
            try:
                data = json.loads(script.string.strip())
                if isinstance(data, list):
                    results.extend(data)
                elif isinstance(data, dict):
                    if "@graph" in data and isinstance(data["@graph"], list):
                        results.extend(data["@graph"])
                    else:
                        results.append(data)
            except Exception as e:
                logger.debug("Failed to parse JSON-LD script on %s: %s", self.base_url, e)
        return results
