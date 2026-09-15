"""
app/services/discovery/normalizer.py

Normalization helpers for candidate organization names, URLs, domains, and locations.
"""

from __future__ import annotations

import html
import re

from app.utils.url import extract_domain, normalize_url

# Common title/brand suffixes that search engines append to organization names
TITLE_SUFFIXES = [
    r"\|\s*Official\s*(?:Website|Site|Portal)$",
    r"-\s*Official\s*(?:Website|Site|Portal)$",
    r"\|\s*Home$",
    r"-\s*Home$",
    r"\|\s*Welcome$",
    r"-\s*Welcome$",
    r"\|\s*Contact\s*Us$",
    r"-\s*Contact\s*Us$",
]


def normalize_organization_name(raw_name: str) -> str:
    """Normalize organization display name.

    Cleans up HTML entities, collapses whitespace, and removes common page title suffixes,
    while preserving original proper capitalization and legitimate punctuation.
    """
    if not raw_name:
        return ""

    # Unescape HTML entities (&amp; -> &, etc.)
    name = html.unescape(raw_name.strip())

    # Collapse multiple whitespace characters into a single space
    name = re.sub(r"\s+", " ", name)

    # Strip common web page title suffixes
    for suffix_pattern in TITLE_SUFFIXES:
        name = re.sub(suffix_pattern, "", name, flags=re.IGNORECASE).strip()

    # Trim lingering edge punctuation (like trailing hyphens or pipes)
    name = re.sub(r"[\s\|\-]+$", "", name).strip()
    return name


def create_dedup_name_key(name: str) -> str:
    """Create a simplified, lowercased alphanumeric string for deduplication comparisons.

    Example:
        'ABC School, Pvt. Ltd.' -> 'abcschoolpvtltd'
    """
    clean = normalize_organization_name(name).lower()
    return re.sub(r"[^a-z0-9]", "", clean)


def normalize_location_text(location: str | None) -> str | None:
    """Clean and normalize location string."""
    if not location:
        return None
    cleaned = html.unescape(location.strip())
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned if cleaned else None
