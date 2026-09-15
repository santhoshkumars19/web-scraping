"""
app/services/verification/consistency_checker.py

Checks consistency across extracted fields (domain match, valid syntax, conflict detection).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlparse

from app.models.organization import Organization
from app.services.verification.verification_rules import GENERIC_EMAIL_DOMAINS


@dataclass
class ConsistencyResult:
    """Evaluation of data coherence and conflict detection."""

    score: float
    flags: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    field_consistency: dict[str, str] = field(default_factory=dict)


def _extract_domain(url: str | None) -> str:
    if not url:
        return ""
    try:
        raw = url if "://" in url else f"http://{url}"
        netloc = urlparse(raw).netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return ""


def check_consistency(org: Organization) -> ConsistencyResult:
    """Assess cross-field consistency for an organization.

    Checks:
    - Website domain vs. Email domain compatibility.
    - Phone number normalization & E.164 validity.
    - Address presence and pincode compatibility.
    - Conflicting data points (multiple distinct phone numbers or emails).

    Returns:
        ConsistencyResult with numeric score (0-100), flags, and detected conflicts.
    """
    flags: list[str] = []
    conflicts: list[str] = []
    field_consistency: dict[str, str] = {}
    check_scores: list[float] = []

    # ── 1. Website vs. Email Domain Check ──────────────────────────────────────
    web_domains = {
        _extract_domain(w.normalized_url or w.url)
        for w in getattr(org, "websites", [])
        if (w.normalized_url or w.url)
    }
    web_domains = {d for d in web_domains if d and "." in d}

    emails = [
        (e.normalized_email or e.email or "").lower().strip()
        for e in getattr(org, "email_addresses", [])
        if (e.normalized_email or e.email)
    ]
    email_domains = {e.split("@")[1] for e in emails if "@" in e}

    if web_domains and email_domains:
        flags.append("WEBSITE_MATCH")
        matched_domain = False
        has_generic = False

        for edom in email_domains:
            if any(wdom in edom or edom in wdom for wdom in web_domains):
                matched_domain = True
                break
            if edom in GENERIC_EMAIL_DOMAINS:
                has_generic = True

        if matched_domain:
            flags.append("EMAIL_DOMAIN_MATCH")
            field_consistency["email"] = "STRONG"
            field_consistency["website"] = "STRONG"
            check_scores.append(100.0)
        elif has_generic:
            flags.append("WEAK_CONSISTENCY_SIGNAL")
            field_consistency["email"] = "MODERATE"
            field_consistency["website"] = "STRONG"
            check_scores.append(75.0)
        else:
            flags.append("EMAIL_DOMAIN_MISMATCH")
            field_consistency["email"] = "NEUTRAL"
            field_consistency["website"] = "STRONG"
            check_scores.append(50.0)
    elif web_domains:
        flags.append("WEBSITE_MATCH")
        field_consistency["website"] = "STRONG"
        check_scores.append(100.0)
    elif email_domains:
        field_consistency["email"] = "MODERATE"
        check_scores.append(85.0)

    # ── 2. Phone Validity & Conflict Check ────────────────────────────────────
    phones = [
        p for p in getattr(org, "phone_numbers", [])
        if (p.normalized_phone or p.phone_number)
    ]
    if phones:
        all_e164 = all(
            str(p.normalized_phone or "").startswith("+") and len(str(p.normalized_phone or "")) >= 10
            for p in phones
        )
        if all_e164:
            flags.append("VALID_PHONE")
            check_scores.append(100.0)
        else:
            check_scores.append(75.0)

        # Check for multiple distinct numbers
        distinct_numbers = {
            (p.normalized_phone or p.phone_number or "").strip()
            for p in phones
        }
        if len(distinct_numbers) > 1:
            flags.append("MULTIPLE_SOURCES")
            # If multiple numbers exist without differentiated roles (e.g. multiple primary or multiple office/main)
            primary_numbers = [p for p in phones if getattr(p, "is_primary", False)]
            main_types = [p for p in phones if getattr(p, "phone_type", "MAIN") in ("MAIN", "OFFICE")]
            if len(primary_numbers) > 1 or len(main_types) > 1:
                flags.append("POSSIBLE_CONFLICT")
                conflicts.append(f"Multiple primary/office phone numbers identified ({len(distinct_numbers)})")
                field_consistency["phone"] = "CONFLICT"
                check_scores.append(70.0)
            else:
                field_consistency["phone"] = "STRONG"
        else:
            field_consistency["phone"] = "STRONG"

    # ── 3. Address & Pincode Check ────────────────────────────────────────────
    if org.address or org.pincode or org.city:
        flags.append("ADDRESS_PRESENT")
        addr_score = 90.0
        if org.pincode and org.pincode.strip():
            # 6-digit valid pincode
            if len(org.pincode.strip()) == 6 and org.pincode.strip().isdigit():
                addr_score = 100.0
        field_consistency["address"] = "STRONG"
        check_scores.append(addr_score)

    # ── 4. Source Availability Signal ─────────────────────────────────────────
    source_pages = getattr(org, "source_pages", [])
    if source_pages and len(source_pages) > 0:
        flags.append("SOURCE_PRESENT")
        if len(source_pages) > 1:
            flags.append("MULTIPLE_SOURCES")
    else:
        flags.append("SOURCE_MISSING")

    avg_score = round(sum(check_scores) / len(check_scores), 2) if check_scores else 80.0

    return ConsistencyResult(
        score=avg_score,
        flags=flags,
        conflicts=conflicts,
        field_consistency=field_consistency,
    )
