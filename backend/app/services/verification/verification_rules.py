"""
app/services/verification/verification_rules.py

Centralized configuration and rule definitions for Lead Data-Quality Verification.
"""

from __future__ import annotations

# ── Confidence Tier Thresholds ────────────────────────────────────────────────
HIGH_THRESHOLD: int = 80
MEDIUM_THRESHOLD: int = 60

# ── Overall Pillar Weights (Sum to 1.0) ─────────────────────────────────────────
COMPLETENESS_WEIGHT: float = 0.50
SOURCE_WEIGHT: float = 0.30
CONSISTENCY_WEIGHT: float = 0.20

# ── Default Field Weights (Sum to 100) ─────────────────────────────────────────
DEFAULT_FIELD_WEIGHTS: dict[str, int] = {
    "name": 15,
    "website": 15,
    "phone": 15,
    "email": 15,
    "address": 15,
    "whatsapp": 10,
    "contact_person": 10,
    "social_links": 5,
    "facebook": 5,
    "instagram": 5,
    "linkedin": 5,
    "youtube": 5,
    "twitter": 5,
    "other_social_links": 5,
}

# ── High-Value Source Page Types ───────────────────────────────────────────────
HIGH_VALUE_PAGE_TYPES: set[str] = {
    "CONTACT",
    "ABOUT",
    "ADMISSIONS",
    "MANAGEMENT",
    "PRINCIPAL",
    "FACULTY",
    "STAFF",
    "LOCATION",
    "BRANCH",
    "HOME",
}

# ── Common Public Directories ─────────────────────────────────────────────────
DIRECTORY_DOMAINS: set[str] = {
    "justdial.com",
    "sulekha.com",
    "indiamart.com",
    "yellowpages.in",
    "wikimapia.org",
    "wikipedia.org",
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "twitter.com",
    "youtube.com",
}

# ── Generic Webmail Domains ────────────────────────────────────────────────────
GENERIC_EMAIL_DOMAINS: set[str] = {
    "gmail.com",
    "yahoo.com",
    "yahoo.co.in",
    "hotmail.com",
    "outlook.com",
    "rediffmail.com",
    "icloud.com",
    "protonmail.com",
    "aol.com",
    "mail.com",
}
