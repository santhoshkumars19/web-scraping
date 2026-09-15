"""
app/utils/url.py

URL normalization and domain extraction utilities for the LeadScout discovery engine.
"""

from __future__ import annotations

import re
import urllib.parse

# Tracking / marketing query parameters to strip safely
TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "gclsrc",
    "dclid",
    "zanpid",
    "msclkid",
    "mc_cid",
    "mc_eid",
    "ref",
    "source",
}


def normalize_url(url: str) -> str:
    """Normalize a URL to a clean, canonical representation.

    Rules:
    - Scheme: default to 'http' if missing, convert scheme to lowercase.
    - Host: lowercase, strip default ports (80 for http, 443 for https).
    - Path: strip repeated slashes, ensure '/' for root path.
    - Fragment: removed (e.g. '#section' removed).
    - Query parameters: stripped of tracking params, remaining params sorted deterministically.
    - Trailing slash: kept consistent on root, trimmed on nested paths unless root.
    """
    if not url:
        return ""

    raw = url.strip()
    if not raw.startswith(("http://", "https://")):
        raw = "http://" + raw

    parsed = urllib.parse.urlsplit(raw)

    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    # Strip default ports
    if scheme == "http" and netloc.endswith(":80"):
        netloc = netloc[:-3]
    elif scheme == "https" and netloc.endswith(":443"):
        netloc = netloc[:-4]

    # Path normalization
    path = parsed.path
    if not path:
        path = "/"
    else:
        # Collapse multiple slashes
        path = re.sub(r"/+", "/", path)
        if len(path) > 1 and path.endswith("/"):
            path = path.rstrip("/")

    # Query string normalization (strip analytics/tracking parameters)
    query = ""
    if parsed.query:
        query_items = urllib.parse.parse_qsl(parsed.query, keep_blank_values=False)
        filtered_items = [
            (k, v) for k, v in query_items if k.lower() not in TRACKING_PARAMS
        ]
        if filtered_items:
            filtered_items.sort(key=lambda x: x[0])
            query = urllib.parse.urlencode(filtered_items)

    # Reconstruct without fragment
    normalized = urllib.parse.urlunsplit((scheme, netloc, path, query, ""))
    return normalized


def extract_domain(url: str) -> str:
    """Extract the base domain from a URL.

    Example:
        'https://www.example.com/about' -> 'example.com'
        'http://sub.school.edu.in/contact' -> 'sub.school.edu.in'
    """
    if not url:
        return ""

    raw = url.strip()
    if not raw.startswith(("http://", "https://")):
        raw = "http://" + raw

    parsed = urllib.parse.urlsplit(raw)
    netloc = parsed.netloc.lower()

    # Remove port if present
    if ":" in netloc:
        netloc = netloc.split(":")[0]

    # Strip 'www.' prefix for standard domain comparison
    if netloc.startswith("www."):
        netloc = netloc[4:]

    return netloc
