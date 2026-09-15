"""
app/services/cleaning/organization_matcher.py

Multi-signal weighted duplicate detection for organizations with branch safety protection.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from app.models.organization import Organization
from app.services.cleaning.organization_cleaner import normalize_organization_name_for_match

GENERIC_DOMAINS = {
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "twitter.com",
    "x.com",
    "youtube.com",
    "google.com",
    "justdial.com",
    "indiamart.com",
    "sulekha.com",
    "wikimapia.org",
    "wikipedia.org",
}

GENERIC_EMAIL_DOMAINS = {
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


@dataclass
class MatchScoreResult:
    """Result of comparing two organizations for duplicate detection."""

    score: int
    is_duplicate: bool
    is_potential: bool
    reasons: list[str] = field(default_factory=list)
    is_branch_conflict: bool = False


class OrganizationMatcher:
    """Computes duplicate match score between two organizations using multi-signal evidence."""

    @classmethod
    def extract_clean_domain(cls, url: str | None) -> str | None:
        """Extract clean normalized host without www."""
        if not url:
            return None
        raw = url if "://" in url else f"http://{url}"
        try:
            parts = urlsplit(raw)
            host = (parts.hostname or "").lower().strip()
            if host.startswith("www."):
                host = host[4:]
            return host if host else None
        except Exception:
            return None

    @classmethod
    def match(
        cls,
        org1: Organization,
        org2: Organization,
        auto_merge_threshold: int = 80,
        potential_threshold: int = 60,
    ) -> MatchScoreResult:
        """Compare two organizations and calculate duplicate confidence score (0-100)."""
        reasons: list[str] = []
        score = 0

        # ── 1. Domain Match (50 pts) ──────────────────────────────────────────
        domains1 = {
            cls.extract_clean_domain(w.normalized_url or w.url)
            for w in org1.websites
            if (w.normalized_url or w.url)
        }
        domains2 = {
            cls.extract_clean_domain(w.normalized_url or w.url)
            for w in org2.websites
            if (w.normalized_url or w.url)
        }
        # Filter out None and generic domains
        valid_d1 = {d for d in domains1 if d and d not in GENERIC_DOMAINS}
        valid_d2 = {d for d in domains2 if d and d not in GENERIC_DOMAINS}
        shared_domains = valid_d1.intersection(valid_d2)
        has_shared_domain = len(shared_domains) > 0

        if has_shared_domain:
            matched_d = next(iter(shared_domains))
            score += 50
            reasons.append(f"Shared website domain ({matched_d})")

        # ── 2. Phone Match (25 pts) ───────────────────────────────────────────
        phones1 = {
            p.normalized_phone
            for p in org1.phone_numbers
            if p.normalized_phone
        }
        phones2 = {
            p.normalized_phone
            for p in org2.phone_numbers
            if p.normalized_phone
        }
        shared_phones = phones1.intersection(phones2)
        has_shared_phone = len(shared_phones) > 0

        if has_shared_phone:
            matched_p = next(iter(shared_phones))
            score += 25
            reasons.append(f"Shared phone number ({matched_p})")

        # ── 3. Email Match (15 pts) ───────────────────────────────────────────
        emails1 = {
            e.normalized_email.lower().strip()
            for e in org1.email_addresses
            if e.normalized_email
        }
        emails2 = {
            e.normalized_email.lower().strip()
            for e in org2.email_addresses
            if e.normalized_email
        }
        shared_emails = emails1.intersection(emails2)

        if shared_emails:
            matched_e = next(iter(shared_emails))
            score += 15
            reasons.append(f"Shared email address ({matched_e})")
        else:
            # Check for non-generic email domains
            e_doms1 = {
                e.split("@", 1)[1] for e in emails1 if "@" in e and e.split("@", 1)[1] not in GENERIC_EMAIL_DOMAINS
            }
            e_doms2 = {
                e.split("@", 1)[1] for e in emails2 if "@" in e and e.split("@", 1)[1] not in GENERIC_EMAIL_DOMAINS
            }
            shared_e_doms = e_doms1.intersection(e_doms2)
            if shared_e_doms:
                matched_ed = next(iter(shared_e_doms))
                score += 10
                reasons.append(f"Shared institutional email domain ({matched_ed})")

        # ── 4. Name Match (up to 20 pts) ──────────────────────────────────────
        norm_name1 = normalize_organization_name_for_match(org1.name or "")
        norm_name2 = normalize_organization_name_for_match(org2.name or "")

        name_matched = False
        if norm_name1 and norm_name2:
            if norm_name1 == norm_name2:
                score += 20
                name_matched = True
                reasons.append(f"Matching normalized name ('{norm_name1}')")
            else:
                ratio = difflib.SequenceMatcher(None, norm_name1, norm_name2).ratio()
                tokens1 = set(norm_name1.split())
                tokens2 = set(norm_name2.split())
                if tokens1 == tokens2:
                    score += 20
                    name_matched = True
                    reasons.append(f"Matching name tokens ('{norm_name1}')")
                elif ratio >= 0.85:
                    score += 15
                    name_matched = True
                    reasons.append(f"High name similarity ({ratio:.0%})")
                elif (norm_name1 in norm_name2 or norm_name2 in norm_name1) and min(len(norm_name1), len(norm_name2)) >= 6:
                    score += 10
                    name_matched = True
                    reasons.append("Substring name containment")

        # ── 5. Address / Pincode Match (up to 15 pts) ─────────────────────────
        pincode1 = (org1.pincode or "").strip()
        pincode2 = (org2.pincode or "").strip()
        has_matching_pincode = bool(pincode1 and pincode2 and pincode1 == pincode2)

        addr1 = (org1.address or "").lower().strip()
        addr2 = (org2.address or "").lower().strip()

        if has_matching_pincode:
            score += 15
            reasons.append(f"Matching pincode ({pincode1})")
        elif addr1 and addr2 and (addr1 == addr2 or (len(addr1) > 10 and addr1 in addr2) or (len(addr2) > 10 and addr2 in addr1)):
            score += 15
            reasons.append("Matching address")

        # ── 6. City Match (5 pts) ─────────────────────────────────────────────
        city1 = (org1.city or "").strip().lower()
        city2 = (org2.city or "").strip().lower()
        has_matching_city = bool(city1 and city2 and city1 == city2)
        has_conflicting_city = bool(city1 and city2 and city1 != city2)

        if has_matching_city:
            score += 5
            reasons.append(f"Matching city ({org1.city})")

        # ── Branch Safety Check ───────────────────────────────────────────────
        # If both organizations have confirmed cities and they differ, they are distinct
        # branches or campuses unless they share a verified domain or direct phone.
        is_branch_conflict = False
        if has_conflicting_city and not (has_shared_domain or has_shared_phone):
            is_branch_conflict = True
            reasons.append(
                f"Branch safety: distinct confirmed cities ('{org1.city}' vs '{org2.city}') "
                f"without shared domain or phone"
            )

        # Cap score at 100
        final_score = min(100, score)

        if is_branch_conflict:
            is_duplicate = False
            is_potential = False
            final_score = min(final_score, 40)
        else:
            is_duplicate = final_score >= auto_merge_threshold
            is_potential = (final_score >= potential_threshold) and not is_duplicate

        return MatchScoreResult(
            score=final_score,
            is_duplicate=is_duplicate,
            is_potential=is_potential,
            reasons=reasons,
            is_branch_conflict=is_branch_conflict,
        )
