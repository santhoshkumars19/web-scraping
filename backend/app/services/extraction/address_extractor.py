"""
app/services/extraction/address_extractor.py

Extracts address blocks, cities, states, and pincodes from HTML and JSON-LD.
"""

from __future__ import annotations

import re

from app.services.extraction.base import ExtractedItem, PageContext, ParsedPage
from app.services.extraction.normalizer import clean_text
from app.services.extraction.patterns import INDIAN_STATES_AND_UTS, PINCODE_REGEX


class AddressExtractor:
    """Specialized extractor for physical addresses, cities, states, and postal codes."""

    @classmethod
    def extract(cls, page: ParsedPage, context: PageContext) -> list[ExtractedItem]:
        """Extract address candidates from the parsed page."""
        items: list[ExtractedItem] = []
        seen_addresses: set[str] = set()

        def add_address(raw: str, method: str, city: str | None = None, state: str | None = None, pincode: str | None = None) -> None:
            cleaned = clean_text(raw).strip()
            if len(cleaned) < 10:
                return

            if cleaned in seen_addresses:
                return
            seen_addresses.add(cleaned)

            # Detect pincode if not provided
            if not pincode:
                p_match = PINCODE_REGEX.search(cleaned)
                if p_match:
                    pincode = p_match.group(0)

            # Detect state if not provided
            if not state:
                for st in INDIAN_STATES_AND_UTS:
                    if re.search(rf"\b{re.escape(st)}\b", cleaned, re.IGNORECASE):
                        state = st
                        break

            # Fallback city from context if present in address text
            if not city and context.page_title:
                pass

            items.append(
                ExtractedItem(
                    field_name="ADDRESS",
                    raw_value=raw.strip(),
                    normalized_value=cleaned,
                    method=method,
                    metadata={
                        "city": city,
                        "state": state,
                        "pincode": pincode,
                    },
                )
            )

        # 1. Extract from JSON-LD Schema.org PostalAddress
        for obj in page.json_ld:
            addr_obj = obj.get("address")
            if isinstance(addr_obj, dict):
                street = addr_obj.get("streetAddress", "")
                locality = addr_obj.get("addressLocality", "")
                region = addr_obj.get("addressRegion", "")
                postal = addr_obj.get("postalCode", "")
                full_parts = [p for p in (street, locality, region, postal) if p]
                if full_parts:
                    add_address(
                        raw=", ".join(full_parts),
                        method="json_ld",
                        city=locality or None,
                        state=region or None,
                        pincode=postal or None,
                    )
            elif isinstance(addr_obj, str):
                add_address(raw=addr_obj, method="json_ld")

        # 2. Extract from <address> tags
        for addr_tag in page.address_tags:
            text = addr_tag.get_text()
            if text:
                add_address(raw=text, method="address_element")

        # 3. Extract from elements with address/location classes or IDs
        selectors = [
            ".address", "#address", ".contact-address", ".footer-address",
            "[class*='address']", "[class*='location']",
        ]
        for sel in selectors:
            for el in page.soup.select(sel):
                # Avoid selecting large outer containers
                if len(el.get_text()) > 300:
                    continue
                text = el.get_text()
                # Must look like an address (has pincode or comma or numbers)
                if PINCODE_REGEX.search(text) or ("," in text and any(char.isdigit() for char in text)):
                    add_address(raw=text, method="css_selector")

        # 4. Extract from explicit labels in visible text: "Address: ..."
        addr_label_match = re.search(
            r"(?:Address|Campus Address|Office Address|Location)\s*[:\-]\s*([^<\n\r]{15,200})",
            page.visible_text,
            re.IGNORECASE,
        )
        if addr_label_match:
            add_address(raw=addr_label_match.group(1), method="regex_label")

        return items
