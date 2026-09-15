"""
app/services/extraction/email_extractor.py

Extracts, validates, de-obfuscates, and classifies email addresses.
"""

from __future__ import annotations

import os
from urllib.parse import unquote

from app.services.extraction.base import ExtractedItem, PageContext, ParsedPage
from app.services.extraction.normalizer import clean_text, deobfuscate_email
from app.services.extraction.patterns import (
    EMAIL_REGEX,
    EMAIL_TYPE_KEYWORDS,
    IGNORED_EMAIL_DOMAINS,
    IGNORED_EMAIL_EXTENSIONS,
    OBFUSCATED_EMAIL_REGEX,
)


class EmailExtractor:
    """Specialized extractor for email addresses."""

    @classmethod
    def extract(cls, page: ParsedPage, context: PageContext) -> list[ExtractedItem]:
        """Extract unique, validated emails from the parsed page."""
        items: list[ExtractedItem] = []
        seen_normalized: set[str] = set()

        def add_email(raw: str, method: str, nearby_context: str = "") -> None:
            normalized = deobfuscate_email(raw).lower()
            if not cls._is_valid_email(normalized):
                return

            if normalized in seen_normalized:
                return
            seen_normalized.add(normalized)

            email_type = cls._classify_email_type(
                email=normalized,
                nearby_context=f"{nearby_context} {context.page_type}".lower(),
                is_first=(len(items) == 0),
            )

            is_primary = (len(items) == 0 and email_type in ("GENERAL", "CONTACT", "ADMISSIONS"))

            items.append(
                ExtractedItem(
                    field_name="EMAIL",
                    raw_value=raw.strip(),
                    normalized_value=normalized,
                    method=method,
                    metadata={
                        "email_type": email_type,
                        "is_primary": is_primary,
                    },
                )
            )

        # 1. Extract from mailto: links
        for a in page.anchors:
            href = a.get("href", "").strip()
            if href.lower().startswith("mailto:"):
                raw_mail = href[7:].split("?")[0].strip()
                raw_mail = unquote(raw_mail)
                anchor_text = a.get_text()
                parent_text = a.parent.get_text() if a.parent else ""
                add_email(
                    raw=raw_mail,
                    method="mailto_link",
                    nearby_context=f"{anchor_text} {parent_text}",
                )

        # 2. Extract from JSON-LD
        for obj in page.json_ld:
            if "email" in obj:
                mail_val = obj["email"]
                if isinstance(mail_val, str):
                    add_email(raw=mail_val, method="json_ld", nearby_context="schema.org")
                elif isinstance(mail_val, list):
                    for m in mail_val:
                        if isinstance(m, str):
                            add_email(raw=m, method="json_ld", nearby_context="schema.org")

        # 3. Extract standard emails from visible text
        for match in EMAIL_REGEX.finditer(page.visible_text):
            raw_text_email = match.group(0)
            start, end = match.span()
            ctx_start = max(0, start - 40)
            ctx_end = min(len(page.visible_text), end + 40)
            surrounding = page.visible_text[ctx_start:ctx_end]
            add_email(raw=raw_text_email, method="regex", nearby_context=surrounding)

        # 4. Extract obfuscated emails (e.g. info [at] school [dot] com)
        for match in OBFUSCATED_EMAIL_REGEX.finditer(page.visible_text):
            raw_obfuscated = match.group(0)
            start, end = match.span()
            ctx_start = max(0, start - 40)
            ctx_end = min(len(page.visible_text), end + 40)
            surrounding = page.visible_text[ctx_start:ctx_end]
            add_email(raw=raw_obfuscated, method="obfuscated_regex", nearby_context=surrounding)

        return items

    @classmethod
    def _is_valid_email(cls, email: str) -> bool:
        """Validate email format and reject common false positives."""
        if not email or "@" not in email:
            return False

        if not EMAIL_REGEX.fullmatch(email):
            return False

        # Reject image or asset false positives (e.g. "image@2x.png")
        _, ext = os.path.splitext(email)
        if ext.lower() in IGNORED_EMAIL_EXTENSIONS:
            return False

        domain = email.split("@")[1].lower()
        if domain in IGNORED_EMAIL_DOMAINS:
            return False

        # TLD must be at least 2 alpha characters
        tld = domain.split(".")[-1]
        if not tld.isalpha() or len(tld) < 2:
            return False

        return True

    @classmethod
    def _classify_email_type(cls, email: str, nearby_context: str, is_first: bool) -> str:
        """Classify email into GENERAL, CONTACT, ADMISSIONS, MANAGEMENT, or OTHER."""
        prefix = email.split("@")[0].lower()

        # Check prefix first (e.g. info@ -> GENERAL, admissions@ -> ADMISSIONS)
        for e_type, keywords in EMAIL_TYPE_KEYWORDS:
            if any(kw in prefix for kw in keywords):
                return e_type

        # Check nearby context second
        for e_type, keywords in EMAIL_TYPE_KEYWORDS:
            if any(kw in nearby_context for kw in keywords):
                return e_type

        if is_first:
            return "GENERAL"

        return "OTHER"

