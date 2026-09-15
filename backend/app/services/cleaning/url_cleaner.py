"""
app/services/cleaning/url_cleaner.py

URL cleaning, tracking parameter removal, and social link normalization.
"""

from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from app.services.cleaning.text_cleaner import clean_text
from app.utils.url import TRACKING_PARAMS, extract_domain, normalize_url


class CleanedURL(str):
    """Normalized URL string supporting tuple unpacking (url, normalized, is_valid)."""

    def __iter__(self):
        yield str(self)
        yield str(self)
        yield True


class CleanedSocialURL(str):
    """Normalized social URL string supporting tuple unpacking (url, is_valid)."""

    def __iter__(self):
        yield str(self)
        yield True


def clean_url(raw_url: str) -> CleanedURL | None:
    """Clean and normalize general website URLs, stripping fragments, www., and tracking parameters.

    Returns:
        CleanedURL string if valid, or None if invalid.
    """
    text = clean_text(raw_url).strip()
    if not text or len(text) < 4:
        return None

    if not text.startswith(("http://", "https://")):
        text = f"https://{text}"

    try:
        norm = normalize_url(text)
        domain = extract_domain(norm)
        if not domain or "." not in domain:
            return None

        # Strip www. from host
        parsed = urlparse(norm)
        netloc = parsed.netloc
        if netloc.startswith("www."):
            netloc = netloc[4:]
        norm = urlunparse((parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))

        return CleanedURL(norm)
    except Exception:
        return None


def clean_social_url(raw_url: str) -> CleanedSocialURL | None:
    """Clean social media profile URLs by removing tracking parameters while preserving profile paths.

    Returns:
        CleanedSocialURL string if valid, or None if invalid.
    """
    text = clean_text(raw_url).strip()
    if not text:
        return None

    if not text.startswith(("http://", "https://")):
        text = f"https://{text}"

    try:
        parsed = urlparse(text)
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]

        # Strip fragment
        path = parsed.path.rstrip("/")
        if not path:
            path = "/"

        # Strip all tracking params from query string
        clean_query = ""
        if parsed.query:
            filtered_params = [
                (k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=False)
                if k.lower() not in TRACKING_PARAMS and not k.lower().startswith("utm_")
            ]
            if filtered_params:
                clean_query = urlencode(filtered_params)

        cleaned = urlunparse(("https", netloc, path, "", clean_query, ""))
        return CleanedSocialURL(cleaned)
    except Exception:
        return None
