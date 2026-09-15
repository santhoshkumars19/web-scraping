"""
app/services/extraction/normalizer.py

Normalization helpers for phones, emails, addresses, and text.
"""

from __future__ import annotations

import html
import re

import phonenumbers
from phonenumbers import PhoneNumberFormat, NumberParseException

from app.core.logging import get_logger
from app.services.extraction.patterns import OBFUSCATED_EMAIL_REGEX

logger = get_logger(__name__)


def clean_text(text: str | None) -> str:
    """Unescape HTML entities, strip control characters, and collapse spaces."""
    if not text:
        return ""
    unescaped = html.unescape(text)
    # Remove null bytes and non-printable characters except whitespace
    sanitized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", unescaped)
    return " ".join(sanitized.split())


def normalize_phone_number(
    raw_number: str,
    default_region: str = "IN",
) -> tuple[str, str, bool]:
    """Parse and normalize phone number into standard display and E.164 formats.

    Args:
        raw_number: Raw phone string from HTML or tel: link.
        default_region: ISO 3166-1 alpha-2 country code (default: "IN").

    Returns:
        Tuple of (display_phone, e164_phone, is_valid)
    """
    cleaned = clean_text(raw_number).strip()
    # Strip non-phone characters except leading +
    cleaned = re.sub(r"[^\d+()\s.-]", "", cleaned)

    if not cleaned:
        return "", "", False

    try:
        parsed = phonenumbers.parse(cleaned, default_region)
        is_possible = phonenumbers.is_possible_number(parsed)
        is_valid = phonenumbers.is_valid_number(parsed)

        if is_possible or is_valid:
            e164_phone = phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
            international_phone = phonenumbers.format_number(parsed, PhoneNumberFormat.INTERNATIONAL)
            return international_phone, e164_phone, True
    except NumberParseException:
        pass

    # Fallback heuristic for standard 10-digit Indian mobile
    digits_only = re.sub(r"\D", "", cleaned)
    if len(digits_only) == 10 and digits_only[0] in "6789":
        e164 = f"+91{digits_only}"
        display = f"+91 {digits_only[:5]} {digits_only[5:]}"
        return display, e164, True
    elif len(digits_only) == 11 and digits_only.startswith("0") and digits_only[1] in "6789":
        e164 = f"+91{digits_only[1:]}"
        display = f"+91 {digits_only[1:6]} {digits_only[6:]}"
        return display, e164, True
    elif len(digits_only) == 12 and digits_only.startswith("91") and digits_only[2] in "6789":
        e164 = f"+{digits_only}"
        display = f"+91 {digits_only[2:7]} {digits_only[7:]}"
        return display, e164, True

    return cleaned, cleaned, False


def deobfuscate_email(raw: str) -> str:
    """De-obfuscate emails containing [at], (at), [dot], etc. into valid email format."""
    cleaned = clean_text(raw).strip()

    # If already a normal email
    if "@" in cleaned and "." in cleaned:
        # Strip trailing punctuation often caught in sentences (e.g. "contact@school.org.")
        return cleaned.rstrip(".,;:!?)")

    # Match obfuscated pattern: name [at] domain [dot] com
    match = OBFUSCATED_EMAIL_REGEX.search(cleaned)
    if match:
        user, domain, tld = match.groups()
        return f"{user.strip()}@{domain.strip()}.{tld.strip()}".lower()

    return cleaned
