"""
app/services/discovery/query_builder.py

Generates deterministic search queries combining keyword and location.
"""

from __future__ import annotations


def build_discovery_queries(keyword: str, location: str) -> list[str]:
    """Generate a clean, deterministic set of targeted queries for search providers.

    Args:
        keyword: Target niche/category (e.g. "CBSE Schools").
        location: City/region (e.g. "Puducherry").

    Returns:
        Ordered list of deterministic search queries.
    """
    clean_keyword = keyword.strip()
    clean_location = location.strip()

    if not clean_keyword or not clean_location:
        return [clean_keyword or clean_location]

    queries = [
        f"{clean_keyword} in {clean_location}",
        f"{clean_keyword} {clean_location} official website",
        f"{clean_keyword} {clean_location} contact",
        f"{clean_keyword} {clean_location}",
    ]

    # Deduplicate while preserving order
    seen = set()
    unique_queries = []
    for q in queries:
        q_norm = q.lower()
        if q_norm not in seen:
            seen.add(q_norm)
            unique_queries.append(q)

    return unique_queries
