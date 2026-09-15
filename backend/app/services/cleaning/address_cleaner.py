"""
app/services/cleaning/address_cleaner.py

Physical address and postal code cleaning and normalization.
"""

from __future__ import annotations

import re

from app.services.cleaning.text_cleaner import clean_text, is_placeholder
from app.services.extraction.patterns import PINCODE_REGEX


def clean_address(raw_address: str | None) -> str | None:
    """Clean address string: collapse line breaks and whitespace, remove redundant punctuation."""
    if not raw_address or is_placeholder(raw_address):
        return None

    # Replace newlines and tabs with commas
    normalized = re.sub(r"[\r\n\t]+", ", ", raw_address)
    cleaned = clean_text(normalized)

    # Collapse repeated commas or spaces around commas (e.g. ", , " -> ", ")
    cleaned = re.sub(r"\s*,\s*(?:,\s*)+", ", ", cleaned)
    cleaned = cleaned.strip(" ,.-")

    if len(cleaned) < 5 or is_placeholder(cleaned):
        return None

    return cleaned


def clean_pincode(raw_pincode: str | None) -> str | None:
    """Validate and normalize 6-digit Indian postal code."""
    if not raw_pincode or is_placeholder(raw_pincode):
        return None

    digits = re.sub(r"\D", "", raw_pincode)
    if len(digits) == 6 and digits[0] != "0":
        return digits

    # Try regex search in case pincode is embedded in a label
    match = PINCODE_REGEX.search(raw_pincode)
    if match:
        return match.group(0)

    return None
