"""
app/services/cleaning/phone_cleaner.py

Phone number validation, normalization to E.164, and noise filtering.
"""

from __future__ import annotations

import re

import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberFormat

from app.services.cleaning.text_cleaner import clean_text

DUMMY_PHONE_DIGITS = {
    "0000000000", "1111111111", "2222222222", "3333333333", "4444444444",
    "5555555555", "6666666666", "7777777777", "8888888888", "9999999999",
    "1234567890", "0123456789", "12345678", "123456",
}


class CleanedPhone:
    """Represents a validated and normalized phone number."""

    display: str
    e164: str

    def __init__(self, display: str, e164: str) -> None:
        self.display = display
        self.e164 = e164

    def __iter__(self):
        yield self.display
        yield self.e164
        yield True

    def __repr__(self) -> str:
        return f"CleanedPhone(display={self.display!r}, e164={self.e164!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, CleanedPhone):
            return self.e164 == other.e164 and self.display == other.display
        if isinstance(other, tuple) and len(other) == 3:
            return (self.display, self.e164, True) == other
        return False


def clean_phone_number(
    raw_number: str,
    default_region: str = "IN",
) -> CleanedPhone | None:
    """Clean, validate, and normalize a phone number.

    Args:
        raw_number: Raw phone string.
        default_region: Default country code (default: "IN").

    Returns:
        CleanedPhone instance if valid, or None if invalid or garbage.
    """
    if not raw_number:
        return None

    cleaned = clean_text(raw_number).strip()
    # Strip unwanted characters while keeping digits and leading +
    cleaned = re.sub(r"[^\d+()\s.-]", "", cleaned)
    digits_only = re.sub(r"\D", "", cleaned)

    # 1. Reject obvious garbage lengths and dummy sequences
    if len(digits_only) < 7 or len(digits_only) > 15:
        return None

    if digits_only in DUMMY_PHONE_DIGITS or len(set(digits_only)) <= 2:
        return None

    # 2. Parse with phonenumbers library
    try:
        parsed = phonenumbers.parse(cleaned, default_region)
        is_possible = phonenumbers.is_possible_number(parsed)
        is_valid = phonenumbers.is_valid_number(parsed)

        if is_possible or is_valid:
            e164 = phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
            display = phonenumbers.format_number(parsed, PhoneNumberFormat.INTERNATIONAL)
            return CleanedPhone(display=display, e164=e164)
    except NumberParseException:
        pass

    # 3. Fallback for Indian 10-digit mobile
    if len(digits_only) == 10 and digits_only[0] in "6789":
        e164 = f"+91{digits_only}"
        display = f"+91 {digits_only[:5]} {digits_only[5:]}"
        return CleanedPhone(display=display, e164=e164)
    elif len(digits_only) == 11 and digits_only.startswith("0") and digits_only[1] in "6789":
        e164 = f"+91{digits_only[1:]}"
        display = f"+91 {digits_only[1:6]} {digits_only[6:]}"
        return CleanedPhone(display=display, e164=e164)
    elif len(digits_only) == 12 and digits_only.startswith("91") and digits_only[2] in "6789":
        e164 = f"+{digits_only}"
        display = f"+91 {digits_only[2:7]} {digits_only[7:]}"
        return CleanedPhone(display=display, e164=e164)

    return None
