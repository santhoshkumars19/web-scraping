"""
app/services/extraction/organization_extractor.py

Extracts organization name and category signals from page title, headings,
meta tags, and JSON-LD structured data.
"""

from __future__ import annotations

from app.services.extraction.base import ExtractedItem, PageContext, ParsedPage
from app.services.extraction.normalizer import clean_text


class OrganizationExtractor:
    """Extracts organization metadata and classification hints."""

    @classmethod
    def extract(cls, page: ParsedPage, context: PageContext) -> list[ExtractedItem]:
        """Extract organization name and category candidates from parsed page."""
        items: list[ExtractedItem] = []

        # 1. Check JSON-LD structured data
        for obj in page.json_ld:
            schema_type = obj.get("@type")
            if schema_type in ("EducationalOrganization", "School", "CollegeOrUniversity", "Organization", "LocalBusiness"):
                name = obj.get("name") or obj.get("legalName")
                if name and isinstance(name, str):
                    items.append(
                        ExtractedItem(
                            field_name="ORGANIZATION_NAME",
                            raw_value=name,
                            normalized_value=clean_text(name),
                            method="json_ld",
                            metadata={"confidence": 0.9},
                        )
                    )

                if schema_type:
                    items.append(
                        ExtractedItem(
                            field_name="CATEGORY",
                            raw_value=schema_type,
                            normalized_value=schema_type,
                            method="json_ld",
                        )
                    )

        # 2. Check OpenGraph meta og:site_name
        og_site_name = page.soup.find("meta", property="og:site_name")
        if og_site_name and og_site_name.get("content"):
            name_val = og_site_name["content"].strip()
            items.append(
                ExtractedItem(
                    field_name="ORGANIZATION_NAME",
                    raw_value=name_val,
                    normalized_value=clean_text(name_val),
                    method="og_meta",
                    metadata={"confidence": 0.8},
                )
            )

        # 3. Check H1 tag if on home or about page and no structured name was found
        has_strong_name = any(it.field_name == "ORGANIZATION_NAME" for it in items)
        if not has_strong_name and context.page_type in ("HOME", "ABOUT"):
            for h1 in page.h1_tags:
                h1_text = clean_text(h1.get_text())
                if h1_text.lower() in ("welcome", "home", "about us", "contact us", "overview", "introduction"):
                    continue
                if 5 <= len(h1_text) <= 100:
                    items.append(
                        ExtractedItem(
                            field_name="ORGANIZATION_NAME",
                            raw_value=h1_text,
                            normalized_value=h1_text,
                            method="h1_heading",
                            metadata={"confidence": 0.7},
                        )
                    )
                    break


        return items
