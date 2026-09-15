"""
app/services/extraction/contact_extractor.py

Extracts key leadership and contact persons (Principals, Directors, Heads)
along with their official designations.
"""

from __future__ import annotations

import re

from app.services.extraction.base import ExtractedItem, PageContext, ParsedPage
from app.services.extraction.normalizer import clean_text
from app.services.extraction.patterns import DESIGNATION_KEYWORDS


class ContactExtractor:
    """Specialized extractor for key personnel, leadership, and contact persons."""

    NAME_PREFIXES = r"(?:Dr\.|Prof\.|Mr\.|Mrs\.|Ms\.|Shri|Smt\.)?"
    # Matches a typical 2 to 4 word capitalized human name
    NAME_PATTERN = rf"{NAME_PREFIXES}\s*([A-Z][a-zA-Z'.]{{1,25}}(?:\s+[A-Z][a-zA-Z'.]{{1,25}}){{1,3}})"

    @classmethod
    def extract(cls, page: ParsedPage, context: PageContext) -> list[ExtractedItem]:
        """Extract contact person records from page DOM and structured content."""
        items: list[ExtractedItem] = []
        seen_names: set[str] = set()

        def add_contact(name: str, designation: str, method: str) -> None:
            clean_n = clean_text(name).strip()
            clean_d = clean_text(designation).strip()

            # Sanity checks for name
            if not clean_n or len(clean_n) < 3 or len(clean_n) > 70:
                return
            if any(char.isdigit() for char in clean_n):
                return

            key = f"{clean_n.lower()}|{clean_d.lower()}"
            if key in seen_names:
                return
            seen_names.add(key)

            items.append(
                ExtractedItem(
                    field_name="CONTACT_PERSON",
                    raw_value=f"{clean_n} - {clean_d}",
                    normalized_value=clean_n,
                    method=method,
                    metadata={
                        "name": clean_n,
                        "designation": clean_d,
                    },
                )
            )

        # 1. Extract from JSON-LD Schema.org Person / employee / founder
        for obj in page.json_ld:
            for field_key in ("founder", "employee", "alumni", "contactPoint"):
                person_data = obj.get(field_key)
                if isinstance(person_data, dict) and person_data.get("@type") == "Person":
                    p_name = person_data.get("name")
                    p_job = person_data.get("jobTitle") or "Contact Person"
                    if p_name:
                        add_contact(p_name, p_job, "json_ld")

        # 2. Extract from staff cards / leadership blocks
        staff_selectors = [
            ".staff-card", ".team-card", ".faculty-member", ".principal-message",
            "[class*='principal']", "[class*='leadership']", "[class*='director']",
        ]
        for sel in staff_selectors:
            for card in page.soup.select(sel):
                card_text = card.get_text(separator="\n")
                lines = [clean_text(line) for line in card_text.splitlines() if clean_text(line)]
                # Look for designation keywords in the lines
                for i, line in enumerate(lines):
                    for kw in DESIGNATION_KEYWORDS:
                        if kw.lower() in line.lower():
                            # Name is often the line before or the line itself
                            if i > 0 and cls._is_potential_name(lines[i - 1]):
                                add_contact(lines[i - 1], line, "staff_card")
                            elif i + 1 < len(lines) and cls._is_potential_name(lines[i + 1]):
                                add_contact(lines[i + 1], line, "staff_card")
                            break

        # 3. Heuristic text patterns: "Principal: Ramesh Kumar" or "Principal - Dr. Ananya Sharma"
        for kw in DESIGNATION_KEYWORDS:
            regex_str = rf"\b{re.escape(kw)}\s*[:\-]\s*{cls.NAME_PATTERN}"
            for match in re.finditer(regex_str, page.visible_text, re.IGNORECASE):
                candidate_name = match.group(1).strip()
                if cls._is_potential_name(candidate_name):
                    add_contact(candidate_name, kw, "regex_label")

        return items

    @classmethod
    def _is_potential_name(cls, text: str) -> bool:
        """Verify that a string is likely a human name and not a generic sentence."""
        words = text.split()
        if len(words) < 2 or len(words) > 5:
            return False

        # Words should start with uppercase
        if not all(w[0].isupper() or w in ("and", "of", "the", "Dr.", "Prof.", "Mr.", "Mrs.", "Ms.") for w in words):
            return False

        # Disallow common false positives
        low = text.lower()
        if any(bad in low for bad in ("school", "academy", "college", "contact", "address", "phone", "email", "menu", "page", "welcome", "about")):
            return False

        return True
