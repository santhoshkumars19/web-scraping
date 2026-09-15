"""
app/services/extraction/phone_extractor.py

Extracts, validates, and classifies phone numbers from HTML text, tel: links,
WhatsApp links, and JSON-LD structured data.
"""

from __future__ import annotations

import re

from app.services.extraction.base import ExtractedItem, PageContext, ParsedPage
from app.services.extraction.normalizer import clean_text, normalize_phone_number
from app.services.extraction.patterns import (
    PHONE_REGEX,
    PHONE_TYPE_KEYWORDS,
    TEL_LINK_REGEX,
    WHATSAPP_URL_REGEX,
)


class PhoneExtractor:
    """Specialized extractor for phone and WhatsApp numbers."""

    @classmethod
    def extract(cls, page: ParsedPage, context: PageContext) -> list[ExtractedItem]:
        """Extract unique phone numbers from the parsed page."""
        items: list[ExtractedItem] = []
        seen_normalized: set[str] = set()

        def add_phone(
            raw: str,
            method: str,
            forced_type: str | None = None,
            is_whatsapp: bool = False,
            nearby_context: str = "",
        ) -> None:
            display_num, norm_num, is_valid = normalize_phone_number(raw)
            if not is_valid or not norm_num:
                return

            if norm_num in seen_normalized:
                # Update whatsapp flag if this instance was whatsapp
                if is_whatsapp:
                    for it in items:
                        if it.normalized_value == norm_num:
                            it.metadata["is_whatsapp"] = True
                            if it.metadata.get("phone_type") == "MAIN":
                                it.metadata["phone_type"] = "WHATSAPP"
                return

            seen_normalized.add(norm_num)

            # Determine phone type
            phone_type = forced_type
            if not phone_type:
                phone_type = cls._classify_phone_type(
                    norm_num=norm_num,
                    nearby_context=f"{nearby_context} {context.page_type}".lower(),
                    is_whatsapp=is_whatsapp,
                    is_first=(len(items) == 0),
                )

            is_primary = (len(items) == 0 and phone_type in ("MAIN", "OFFICE"))

            items.append(
                ExtractedItem(
                    field_name="PHONE",
                    raw_value=raw.strip(),
                    normalized_value=norm_num,
                    method=method,
                    metadata={
                        "display_phone": display_num,
                        "phone_type": phone_type,
                        "is_whatsapp": is_whatsapp,
                        "is_primary": is_primary,
                    },
                )
            )

        # 1. Extract from tel: links
        for a in page.anchors:
            href = a.get("href", "").strip()
            tel_match = TEL_LINK_REGEX.search(href)
            if tel_match:
                raw_tel = tel_match.group(1)
                anchor_text = a.get_text()
                parent_text = a.parent.get_text() if a.parent else ""
                add_phone(
                    raw=raw_tel,
                    method="tel_link",
                    nearby_context=f"{anchor_text} {parent_text}",
                )

        # 2. Extract from WhatsApp URLs
        for a in page.anchors:
            href = a.get("href", "").strip()
            wa_match = WHATSAPP_URL_REGEX.search(href)
            if wa_match:
                raw_wa = wa_match.group(1)
                add_phone(
                    raw=raw_wa,
                    method="whatsapp_link",
                    forced_type="WHATSAPP",
                    is_whatsapp=True,
                )

        # 3. Extract from JSON-LD
        for obj in page.json_ld:
            if "telephone" in obj:
                tel_val = obj["telephone"]
                if isinstance(tel_val, str):
                    add_phone(raw=tel_val, method="json_ld", nearby_context="schema.org")
                elif isinstance(tel_val, list):
                    for t in tel_val:
                        if isinstance(t, str):
                            add_phone(raw=t, method="json_ld", nearby_context="schema.org")

        # 4. Extract from visible text using regex
        for match in PHONE_REGEX.finditer(page.visible_text):
            raw_text_phone = match.group(0)
            start, end = match.span()
            # Capture context 50 chars before and after
            ctx_start = max(0, start - 50)
            ctx_end = min(len(page.visible_text), end + 50)
            surrounding = page.visible_text[ctx_start:ctx_end]

            is_wa = any(kw in surrounding.lower() for kw in ("whatsapp", "wa.me", "chat with us"))

            add_phone(
                raw=raw_text_phone,
                method="regex",
                is_whatsapp=is_wa,
                nearby_context=surrounding,
            )

        return items

    @classmethod
    def _classify_phone_type(
        cls,
        norm_num: str,
        nearby_context: str,
        is_whatsapp: bool,
        is_first: bool,
    ) -> str:
        """Classify phone into MAIN, OFFICE, ADMISSIONS, LANDLINE, WHATSAPP, ALTERNATE, or OTHER."""
        if is_whatsapp:
            return "WHATSAPP"

        # Check surrounding keywords
        for p_type, keywords in PHONE_TYPE_KEYWORDS:
            if any(kw in nearby_context for kw in keywords):
                return p_type

        # Landline check: Indian fixed line numbers typically start with 02, 03, 04, 080 (non mobile)
        digits = re.sub(r"\D", "", norm_num)
        if digits.startswith("91") and len(digits) > 2:
            lead_digit = digits[2]
            # Mobile numbers in India start with 6, 7, 8, 9
            if lead_digit not in "6789":
                return "LANDLINE"

        if is_first:
            return "MAIN"

        return "OTHER"
