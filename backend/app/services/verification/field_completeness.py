"""
app/services/verification/field_completeness.py

Calculates field completeness against task.selected_fields with normalized weighting.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.models.organization import Organization
from app.services.cleaning.text_cleaner import is_placeholder
from app.services.verification.verification_rules import DEFAULT_FIELD_WEIGHTS


@dataclass
class CompletenessResult:
    """Breakdown of field completeness evaluation."""

    fields_found: int
    total_fields: int
    percentage: float
    weighted_score: float
    field_availability: dict[str, bool] = field(default_factory=dict)


def evaluate_field_presence(org: Organization, field_name: str) -> bool:
    """Check if a specific field is present and non-empty on an organization."""
    fname = field_name.lower().strip()

    if fname == "name":
        return bool(org.name and org.name.strip() and not is_placeholder(org.name))

    if fname == "website":
        return bool(org.websites and any((w.normalized_url or w.url) for w in org.websites))

    if fname in ("phone", "phone_number"):
        return bool(org.phone_numbers and any((p.normalized_phone or p.phone_number) for p in org.phone_numbers))

    if fname in ("alternate_phone", "alternate"):
        valid_phones = [p for p in org.phone_numbers if (p.normalized_phone or p.phone_number)]
        return len(valid_phones) > 1

    if fname == "email":
        return bool(org.email_addresses and any((e.normalized_email or e.email) for e in org.email_addresses))

    if fname == "address":
        has_addr = bool(org.address and org.address.strip() and not is_placeholder(org.address))
        has_pin = bool(org.pincode and org.pincode.strip() and not is_placeholder(org.pincode))
        has_city = bool(org.city and org.city.strip() and not is_placeholder(org.city))
        return has_addr or has_pin or has_city

    if fname == "city":
        return bool(org.city and org.city.strip() and not is_placeholder(org.city))

    if fname == "state":
        return bool(org.state and org.state.strip() and not is_placeholder(org.state))

    if fname == "pincode":
        return bool(org.pincode and org.pincode.strip() and not is_placeholder(org.pincode))

    if fname == "category":
        return bool(org.category and org.category.strip() and not is_placeholder(org.category))

    if fname == "whatsapp":
        return bool(any(p.is_whatsapp for p in org.phone_numbers))

    if fname in ("contact_person", "contact", "designation"):
        return bool(org.contacts and any(c.name and c.name.strip() and not is_placeholder(c.name) for c in org.contacts))

    if fname in ("social_links", "social", "other_social_links"):
        return bool(org.social_links and any((s.normalized_url or s.url) for s in org.social_links))

    if fname in ("facebook", "instagram", "linkedin", "youtube", "twitter"):
        plat = fname.upper()
        return bool(
            org.social_links
            and any(
                getattr(s, "platform", "").upper() == plat or fname in (getattr(s, "normalized_url", None) or getattr(s, "url", None) or "").lower()
                for s in org.social_links
            )
        )

    # Fallback attribute check
    if hasattr(org, fname):
        val = getattr(org, fname)
        return bool(val and str(val).strip() and not is_placeholder(str(val)))

    return False


def calculate_field_completeness(
    org: Organization,
    selected_fields: list[str] | None = None,
    custom_weights: dict[str, int] | None = None,
) -> CompletenessResult:
    """Calculate field completeness for an organization based on the task's selected fields.

    Args:
        org: Organization entity to inspect.
        selected_fields: Optional list of fields requested by the user task.
        custom_weights: Optional custom field weighting dictionary.

    Returns:
        CompletenessResult with count, percentage, weighted score, and availability map.
    """
    weights = custom_weights or DEFAULT_FIELD_WEIGHTS

    if selected_fields and len(selected_fields) > 0:
        requested = [f.lower().strip() for f in selected_fields if f and f.strip()]
    else:
        requested = list(DEFAULT_FIELD_WEIGHTS.keys())

    # De-duplicate requested fields while preserving order
    unique_requested: list[str] = []
    for f in requested:
        if f not in unique_requested:
            unique_requested.append(f)

    if not unique_requested:
        unique_requested = list(DEFAULT_FIELD_WEIGHTS.keys())

    availability: dict[str, bool] = {}
    found_count = 0

    total_weight = 0
    found_weight = 0

    for fname in unique_requested:
        is_present = evaluate_field_presence(org, fname)
        availability[fname] = is_present
        if is_present:
            found_count += 1

        w = weights.get(fname, 10)
        total_weight += w
        if is_present:
            found_weight += w

    total_count = len(unique_requested)
    percentage = round((found_count / total_count) * 100.0, 2) if total_count > 0 else 100.0
    weighted_score = round((found_weight / total_weight) * 100.0, 2) if total_weight > 0 else 100.0

    return CompletenessResult(
        fields_found=found_count,
        total_fields=total_count,
        percentage=percentage,
        weighted_score=weighted_score,
        field_availability=availability,
    )
