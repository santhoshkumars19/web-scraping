"""
app/services/export/export_formatter.py

Data transformation and canonical field mapping for CSV and Excel exports.
Converts Lead database models and their related entities into stable, typed,
sanitized row dictionaries.
"""

from __future__ import annotations

from typing import Sequence

from app.models.lead import Lead

# Canonical field definitions: key -> display header
SUPPORTED_EXPORT_FIELDS: dict[str, str] = {
    "name": "Organization Name",
    "category": "Category",
    "website": "Website",
    "address": "Address",
    "city": "City",
    "state": "State",
    "pincode": "Pincode",
    "phone": "Phone",
    "alternate_phone": "Alternate Phone",
    "email": "Email",
    "whatsapp": "WhatsApp",
    "contact_person": "Contact Person",
    "designation": "Designation",
    "facebook": "Facebook",
    "instagram": "Instagram",
    "linkedin": "LinkedIn",
    "youtube": "YouTube",
    "other_social_links": "Other Social Links",
    "source_urls": "Source URLs",
    "verification": "Verification",
    "scraped_date": "Scraped Date",
    "task_id": "Task ID",
}

# Aliases for client compatibility (snake_case and camelCase)
FIELD_ALIASES: dict[str, str] = {
    "organization_name": "name",
    "org_name": "name",
    "organizationname": "name",
    "alternatephone": "alternate_phone",
    "contact": "contact_person",
    "contactperson": "contact_person",
    "othersocial": "other_social_links",
    "othersociallinks": "other_social_links",
    "social": "other_social_links",
    "sourceurls": "source_urls",
    "scrapeddate": "scraped_date",
    "taskid": "task_id",
}

DEFAULT_EXPORT_FIELDS: list[str] = list(SUPPORTED_EXPORT_FIELDS.keys())


def normalize_requested_fields(raw_fields: Sequence[str] | str | None) -> list[str]:
    """Validate and normalize requested export fields.

    Handles string comma separation, trimming, case-insensitivity, and aliases.
    Raises ValueError if any requested field is unsupported or forbidden.
    """
    if not raw_fields:
        return list(DEFAULT_EXPORT_FIELDS)

    if isinstance(raw_fields, str):
        candidates = [f.strip().lower() for f in raw_fields.split(",") if f.strip()]
    else:
        candidates = []
        for item in raw_fields:
            if isinstance(item, str):
                candidates.extend([f.strip().lower() for f in item.split(",") if f.strip()])

    if not candidates:
        return list(DEFAULT_EXPORT_FIELDS)

    resolved_fields: list[str] = []
    invalid_fields: list[str] = []

    for c in candidates:
        actual_key = FIELD_ALIASES.get(c, FIELD_ALIASES.get(c.replace("_", ""), c))
        if actual_key in SUPPORTED_EXPORT_FIELDS:
            if actual_key not in resolved_fields:
                resolved_fields.append(actual_key)
        else:
            invalid_fields.append(c)

    if invalid_fields:
        raise ValueError(
            f"Invalid export fields: {', '.join(invalid_fields)}. "
            f"Allowed fields: {', '.join(SUPPORTED_EXPORT_FIELDS.keys())}"
        )

    return resolved_fields


def format_lead_to_export_row(
    lead: Lead,
    active_field_keys: list[str],
) -> dict[str, str]:
    """Transform a Lead model into a canonical display-header keyed dictionary.

    Consistently formats multi-value relations (semicolon-separated), social links,
    text-safe phones, and clean date strings.
    """
    org = lead.organization

    # ── Websites ──────────────────────────────────────────────────────────────
    websites = getattr(org, "websites", []) if org else []
    primary_website = ""
    if websites:
        official = next((w.url for w in websites if getattr(w, "is_official", False)), None)
        primary_website = official or websites[0].url

    # ── Phones & WhatsApp ─────────────────────────────────────────────────────
    phones = getattr(org, "phone_numbers", []) if org else []
    primary_phone_obj = next((p for p in phones if getattr(p, "is_primary", False)), None)
    if not primary_phone_obj and phones:
        primary_phone_obj = phones[0]

    primary_phone = primary_phone_obj.phone_number if primary_phone_obj else ""

    alt_phone_objs = [p for p in phones if p != primary_phone_obj]
    alt_phones = "; ".join([p.phone_number for p in alt_phone_objs if p.phone_number])

    whatsapp_obj = next((p for p in phones if getattr(p, "is_whatsapp", False)), None)
    whatsapp = whatsapp_obj.phone_number if whatsapp_obj else ""

    # ── Emails ────────────────────────────────────────────────────────────────
    emails = getattr(org, "email_addresses", []) if org else []
    primary_email_obj = next((e for e in emails if getattr(e, "is_primary", False)), None)
    if not primary_email_obj and emails:
        primary_email_obj = emails[0]

    if primary_email_obj:
        other_emails = [e.email for e in emails if e != primary_email_obj and e.email]
        if other_emails:
            email_val = f"{primary_email_obj.email}; {'; '.join(other_emails)}"
        else:
            email_val = primary_email_obj.email
    else:
        email_val = ""

    # ── Contacts & Designations ───────────────────────────────────────────────
    contacts = getattr(org, "contacts", []) if org else []
    contact_names = "; ".join([c.name for c in contacts if c.name])
    designations = "; ".join([c.designation for c in contacts if getattr(c, "designation", None)])

    # ── Social Links ──────────────────────────────────────────────────────────
    social_links = getattr(org, "social_links", []) if org else []
    social_map: dict[str, str] = {
        "facebook": "",
        "instagram": "",
        "linkedin": "",
        "youtube": "",
    }
    other_socials: list[str] = []

    for s in social_links:
        platform = getattr(s, "platform", "").upper()
        url = getattr(s, "url", "")
        if not url:
            continue
        if platform == "FACEBOOK" and not social_map["facebook"]:
            social_map["facebook"] = url
        elif platform == "INSTAGRAM" and not social_map["instagram"]:
            social_map["instagram"] = url
        elif platform == "LINKEDIN" and not social_map["linkedin"]:
            social_map["linkedin"] = url
        elif platform == "YOUTUBE" and not social_map["youtube"]:
            social_map["youtube"] = url
        else:
            other_socials.append(url)

    other_social_links_val = "; ".join(other_socials)

    # ── Source URLs ───────────────────────────────────────────────────────────
    source_pages = getattr(org, "source_pages", []) if org else []
    unique_sources: list[str] = []
    for sp in source_pages:
        url = getattr(sp, "url", "")
        if url and url not in unique_sources:
            unique_sources.append(url)
    source_urls_val = "; ".join(unique_sources)

    # ── Verification ──────────────────────────────────────────────────────────
    ver_status = getattr(lead, "verification_status", "PENDING")
    ver_obj = getattr(lead, "verification", None)
    if ver_obj:
        ver_status = getattr(ver_obj, "status", ver_status)

    # ── Scraped Date ──────────────────────────────────────────────────────────
    scraped_dt = getattr(lead, "created_at", None)
    scraped_date_str = scraped_dt.strftime("%Y-%m-%d") if scraped_dt else ""

    # ── Task ID ───────────────────────────────────────────────────────────────
    task_obj = getattr(lead, "task", None)
    task_id_str = getattr(task_obj, "task_id", "") if task_obj else ""

    # Raw value lookup table
    raw_data: dict[str, str] = {
        "name": getattr(org, "name", "") if org else "",
        "category": getattr(org, "category", "") or "" if org else "",
        "website": primary_website,
        "address": getattr(org, "address", "") or "" if org else "",
        "city": getattr(org, "city", "") or "" if org else "",
        "state": getattr(org, "state", "") or "" if org else "",
        "pincode": getattr(org, "pincode", "") or "" if org else "",
        "phone": primary_phone,
        "alternate_phone": alt_phones,
        "email": email_val,
        "whatsapp": whatsapp,
        "contact_person": contact_names,
        "designation": designations,
        "facebook": social_map["facebook"],
        "instagram": social_map["instagram"],
        "linkedin": social_map["linkedin"],
        "youtube": social_map["youtube"],
        "other_social_links": other_social_links_val,
        "source_urls": source_urls_val,
        "verification": ver_status,
        "scraped_date": scraped_date_str,
        "task_id": task_id_str,
    }

    # Build output row mapped by canonical display header
    row: dict[str, str] = {}
    for key in active_field_keys:
        header = SUPPORTED_EXPORT_FIELDS[key]
        row[header] = raw_data.get(key, "")

    return row
