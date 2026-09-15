"""
app/services/cleaning/organization_cleaner.py

Organization name cleaning for presentation and canonical comparison keys for matching.
"""

from __future__ import annotations

import re

from app.services.cleaning.text_cleaner import clean_text

LEGAL_SUFFIXES_REGEX = re.compile(
    r"\b(?:pvt\.?\s*ltd\.?|private\s+limited|ltd\.?|limited|inc\.?|incorporated|llc|co\.?|company|corp\.?|corporation)\b",
    re.IGNORECASE,
)


def clean_organization_name(raw_name: str) -> str:
    """Clean organization display name for readable presentation."""
    cleaned = clean_text(raw_name).strip(" -:,|")
    return cleaned


def normalize_organization_name_for_match(name: str) -> str:
    """Normalize organization name into a canonical comparison string for duplicate matching.

    Rules:
    - Lowercase, trim, collapse whitespace
    - Normalize '&' to 'and'
    - Strip legal suffixes (Pvt Ltd, Ltd, Inc) which do not alter core identity
    - Strip punctuation and symbols
    - Preserve differentiator tokens (school, college, academy, etc.)
    """
    cleaned = clean_text(name).lower()

    # Replace & with and
    cleaned = re.sub(r"\s*&\s*", " and ", cleaned)

    # Remove legal suffixes
    cleaned = LEGAL_SUFFIXES_REGEX.sub("", cleaned)

    # Remove non-alphanumeric characters except spaces
    cleaned = re.sub(r"[^\w\s]", "", cleaned)

    # Collapse whitespace
    tokens = [t for t in cleaned.split() if t]
    return " ".join(tokens)
