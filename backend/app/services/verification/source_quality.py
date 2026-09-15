"""
app/services/verification/source_quality.py

Evaluates source credibility and provenance for extracted data points.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlparse

from app.models.extracted_field import ExtractedField
from app.models.organization import Organization
from app.models.source_page import SourcePage
from app.schemas.verification import SourceQualityDetails
from app.services.verification.verification_rules import (
    DIRECTORY_DOMAINS,
    HIGH_VALUE_PAGE_TYPES,
)


@dataclass
class FieldSourceInfo:
    """Provenance evaluation for a single field."""

    field_name: str
    source_present: bool = False
    source_type: str = "UNKNOWN"
    source_page_type: str | None = None
    source_url: str | None = None
    score: float = 0.0


@dataclass
class SourceQualityResult:
    """Aggregate result of source quality assessment."""

    score: float
    details: SourceQualityDetails
    field_sources: dict[str, FieldSourceInfo] = field(default_factory=dict)


def _normalize_host(url: str | None) -> str:
    if not url:
        return ""
    try:
        raw = url if "://" in url else f"http://{url}"
        host = urlparse(raw).netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return ""


def assess_source_quality(
    org: Organization,
    field_availability: dict[str, bool],
    extracted_fields: list[ExtractedField] | None = None,
    source_pages: list[SourcePage] | None = None,
) -> SourceQualityResult:
    """Assess source quality for all present fields on an organization.

    Args:
        org: The Organization being evaluated.
        field_availability: Dict mapping field_name -> bool presence.
        extracted_fields: Optional list of ExtractedField provenance records.
        source_pages: Optional list of SourcePages for the organization.

    Returns:
        SourceQualityResult with numeric score (0-100), counts, and per-field source info.
    """
    ef_list = extracted_fields if extracted_fields is not None else getattr(org, "extracted_fields", [])
    sp_list = source_pages if source_pages is not None else getattr(org, "source_pages", [])

    # Index source pages by ID
    sp_by_id: dict[object, SourcePage] = {sp.id: sp for sp in sp_list if hasattr(sp, "id")}

    # Group extracted fields by canonical field name
    ef_by_field: dict[str, list[ExtractedField]] = {}
    for ef in ef_list:
        fname = ef.field_name.lower().strip()
        # Map subfield names to core categories
        if fname in ("phone", "phone_number", "mobile", "landline", "whatsapp_number"):
            key = "phone"
        elif fname in ("email", "email_address"):
            key = "email"
        elif fname in ("address", "pincode", "city", "state", "postal_code"):
            key = "address"
        elif fname in ("contact_person", "principal", "director", "staff", "management"):
            key = "contact_person"
        elif fname in ("website", "url", "canonical_url"):
            key = "website"
        elif fname in ("facebook", "instagram", "linkedin", "twitter", "youtube", "social"):
            key = "social_links"
        elif fname in ("name", "organization_name", "title"):
            key = "name"
        else:
            key = fname

        ef_by_field.setdefault(key, []).append(ef)

    field_sources: dict[str, FieldSourceInfo] = {}
    field_scores: list[float] = []

    official_website_fields = 0
    directory_fields = 0
    fields_with_source = 0

    has_any_official_website = any(
        getattr(w, "is_official", False) for w in getattr(org, "websites", [])
    )

    for field_name, is_present in field_availability.items():
        if not is_present:
            continue

        info = FieldSourceInfo(field_name=field_name)
        matched_efs = ef_by_field.get(field_name, [])

        if matched_efs:
            # Find the highest-quality matching ExtractedField
            best_ef = matched_efs[0]
            best_sp = sp_by_id.get(best_ef.source_page_id)

            if best_sp is not None:
                info.source_present = True
                info.source_url = best_sp.url
                info.source_page_type = getattr(best_sp, "page_type", "OTHER")

                # Determine if page is from official site or directory
                sp_host = _normalize_host(best_sp.url)
                is_directory = any(sp_host.endswith(d) for d in DIRECTORY_DOMAINS)
                sp_is_official = getattr(getattr(best_sp, "website", None), "is_official", not is_directory)

                if is_directory or not sp_is_official:
                    info.source_type = "DIRECTORY"
                    info.score = 60.0
                    directory_fields += 1
                else:
                    info.source_type = "OFFICIAL_WEBSITE"
                    official_website_fields += 1
                    # Base official score
                    base_score = 80.0
                    page_type = str(info.source_page_type or "").upper()
                    if page_type in ("CONTACT", "ADMISSIONS", "MANAGEMENT", "PRINCIPAL", "STAFF"):
                        base_score = 100.0
                    elif page_type in HIGH_VALUE_PAGE_TYPES:
                        base_score = 95.0
                    info.score = base_score

                fields_with_source += 1
            else:
                info.source_present = False
                info.source_type = "EXTRACTED_WITHOUT_PAGE"
                info.score = 55.0
        else:
            # Present on Organization entity without ExtractedField link
            info.source_present = False
            if has_any_official_website:
                info.source_type = "OFFICIAL_WEBSITE_INFERRED"
                info.score = 75.0
            else:
                info.source_type = "INFERRED"
                info.score = 45.0

        field_sources[field_name] = info
        field_scores.append(info.score)

    total_evaluated = len(field_scores)
    avg_score = round(sum(field_scores) / total_evaluated, 2) if total_evaluated > 0 else 0.0

    details = SourceQualityDetails(
        official_website_fields=official_website_fields,
        directory_fields=directory_fields,
        fields_with_source=fields_with_source,
        total_evaluated_fields=total_evaluated,
    )

    return SourceQualityResult(
        score=avg_score,
        details=details,
        field_sources=field_sources,
    )
