"""
app/services/discovery/ranking.py

Candidate ranking, relevance scoring, and official website identification.
"""

from __future__ import annotations

import re

from app.schemas.discovery import DiscoveryCandidate

# Known public directories and aggregator domains that should not be marked as official
DIRECTORY_DOMAINS = {
    "wikipedia.org",
    "justdial.com",
    "sulekha.com",
    "indiamart.com",
    "yellowpages.com",
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "twitter.com",
    "x.com",
    "youtube.com",
    "shiksha.com",
    "collegedunia.com",
    "eduvidya.com",
    "openstreetmap.org",
    "duckduckgo.com",
    "google.com",
    "bing.com",
    "yahoo.com",
}


def score_candidate(
    candidate: DiscoveryCandidate,
    *,
    target_keyword: str,
    target_location: str,
) -> float:
    """Calculate a 0–100 relevance score for a discovery candidate.

    Factors:
    - Keyword match in candidate name, title, or description: up to 35 pts
    - Location match in address, location text, or title: up to 25 pts
    - Source confidence (e.g. USER_URL: 30, DIRECTORY: 20, PUBLIC_SEARCH: 20): up to 20 pts
    - Domain quality (direct organization domain vs generic directory): up to 20 pts
    """
    score = 0.0

    kw_words = [w.lower() for w in re.findall(r"\w+", target_keyword) if len(w) > 2]
    loc_words = [w.lower() for w in re.findall(r"\w+", target_location) if len(w) > 2]

    search_corpus = f"{candidate.name} {candidate.category or ''} {candidate.title or ''} {candidate.description or ''}".lower()
    location_corpus = f"{candidate.location or ''} {candidate.address or ''} {search_corpus}".lower()

    # 1. Keyword match (up to 35 pts)
    if kw_words:
        matches = sum(
            1
            for w in kw_words
            if w in search_corpus or (len(w) > 3 and w.rstrip("s") in search_corpus)
        )
        score += (matches / len(kw_words)) * 35.0
    else:
        score += 20.0

    # 2. Location match (up to 25 pts)
    if loc_words:
        loc_matches = sum(1 for w in loc_words if w in location_corpus)
        score += (loc_matches / len(loc_words)) * 25.0
    else:
        score += 15.0

    # 3. Source weight (up to 20 pts)
    source_upper = candidate.source.upper()
    if source_upper == "USER_URL":
        score += 20.0
    elif source_upper in {"PUBLIC_DIRECTORY", "FIXTURE"}:
        score += 18.0
    else:
        score += 15.0

    # 4. Domain check (up to 20 pts)
    domain_lower = candidate.domain.lower()
    is_directory = any(d in domain_lower for d in DIRECTORY_DOMAINS)

    if not is_directory and domain_lower:
        score += 20.0
    elif is_directory:
        score += 5.0

    return min(100.0, round(score, 1))


def is_candidate_official_website(candidate: DiscoveryCandidate) -> bool:
    """Determine whether the candidate URL is plausible as the organization's official website.

    Returns True if:
    - Not a known aggregator/directory/social media domain
    - Confidence score is sufficiently high (>= 60)
    - Domain contains part of the organization's name tokens or acronym
    """
    domain_lower = candidate.domain.lower()
    if not domain_lower:
        return False

    if any(d in domain_lower for d in DIRECTORY_DOMAINS):
        return False

    if candidate.confidence < 60.0:
        return False

    # Check for name or acronym overlap in the domain
    name_tokens = [w.lower() for w in re.findall(r"[a-zA-Z0-9]+", candidate.name) if len(w) >= 3]
    if any(token in domain_lower for token in name_tokens):
        return True

    # Check acronym (e.g. "ABC School" -> "abc")
    acronym = "".join([w[0].lower() for w in re.findall(r"[a-zA-Z]+", candidate.name) if w])
    if len(acronym) >= 3 and acronym in domain_lower:
        return True

    # Dedicated education / enterprise TLDs with high confidence
    if any(domain_lower.endswith(tld) for tld in [".edu", ".edu.in", ".ac.in", ".org", ".ac"]):
        return True

    return False
