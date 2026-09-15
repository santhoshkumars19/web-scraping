"""
app/services/cleaning/text_cleaner.py

General text cleaning, whitespace normalization, and placeholder detection.
"""

from __future__ import annotations

import html
import re

PLACEHOLDER_STRINGS = {
    "null", "none", "undefined", "n/a", "na", "not available", "not applicable",
    "-", "--", "---", "placeholder", "test", "sample", "demo", "dummy", "unknown",
    "no info", "no email", "no phone", "nil", "empty", "default", "lorem ipsum",
}


def clean_text(text: str | None) -> str:
    """Clean arbitrary string: decode HTML entities, remove control chars, collapse spaces."""
    if not text:
        return ""
    # Unescape HTML entities (e.g. &amp; -> &, &quot; -> ")
    decoded = html.unescape(text)
    # Strip non-printable ASCII control characters (0-8, 11, 12, 14-31, 127)
    sanitized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", decoded)
    # Collapse multiple whitespace (spaces, tabs, newlines) into a single space
    return " ".join(sanitized.split())


def is_placeholder(text: str | None) -> bool:
    """Return True if text is empty or a common placeholder / garbage value."""
    if text is None:
        return True
    cleaned = clean_text(text).lower()
    if not cleaned:
        return True
    if cleaned in PLACEHOLDER_STRINGS:
        return True
    # Repeating identical punctuation like "???" or "---"
    if len(set(cleaned)) == 1 and not cleaned[0].isalnum():
        return True
    return False
