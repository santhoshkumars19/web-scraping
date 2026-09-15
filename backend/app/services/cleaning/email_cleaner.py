"""
app/services/cleaning/email_cleaner.py

Email address cleaning, de-obfuscation, structure validation, and noise filtering.
"""

from __future__ import annotations

import os
import re

from app.services.cleaning.text_cleaner import clean_text
from app.services.extraction.normalizer import deobfuscate_email
from app.services.extraction.patterns import (
    EMAIL_REGEX,
    IGNORED_EMAIL_DOMAINS,
    IGNORED_EMAIL_EXTENSIONS,
)

DUMMY_EMAIL_USERNAMES = {"admin", "test", "demo", "sample", "user", "root"}


class CleanedEmail(str):
    """Represents a validated and normalized email address (inherits from str)."""

    normalized: str
    domain: str

    def __new__(cls, normalized: str, domain: str) -> CleanedEmail:
        obj = super().__new__(cls, normalized)
        obj.normalized = normalized
        obj.domain = domain
        return obj

    def __iter__(self):
        yield self.normalized
        yield True


def clean_email(raw_email: str) -> CleanedEmail | None:
    """Clean and validate an email address.

    Args:
        raw_email: Raw email string.

    Returns:
        CleanedEmail instance if valid, or None if invalid or dummy.
    """
    cleaned = clean_text(raw_email).strip()
    if not cleaned:
        return None

    # De-obfuscate if needed (e.g. info [at] domain [dot] com)
    cleaned = deobfuscate_email(cleaned)

    # Remove interior whitespace if accidental
    cleaned = re.sub(r"\s+", "", cleaned).lower()

    # Strip trailing punctuation
    cleaned = cleaned.rstrip(".,;:!?)")

    if not EMAIL_REGEX.fullmatch(cleaned):
        return None

    parts = cleaned.split("@")
    if len(parts) != 2:
        return None

    username, domain = parts

    # Reject asset extensions caught as emails in username or domain
    _, u_ext = os.path.splitext(username)
    if u_ext.lower() in IGNORED_EMAIL_EXTENSIONS:
        return None

    _, d_ext = os.path.splitext(domain)
    if d_ext.lower() in IGNORED_EMAIL_EXTENSIONS:
        return None

    # Reject dummy placeholder domains
    if domain.lower() in IGNORED_EMAIL_DOMAINS:
        return None

    # TLD must be valid
    tld = domain.split(".")[-1]
    if not tld.isalpha() or len(tld) < 2:
        return None

    return CleanedEmail(cleaned, domain)
