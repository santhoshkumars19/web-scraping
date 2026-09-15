"""
app/services/extraction/extractor.py

Aggregates all specialized extractors to extract structured data from a SourcePage.
"""

from __future__ import annotations

from app.services.extraction.address_extractor import AddressExtractor
from app.services.extraction.base import ExtractedItem, ExtractionResult, PageContext, ParsedPage
from app.services.extraction.contact_extractor import ContactExtractor
from app.services.extraction.email_extractor import EmailExtractor
from app.services.extraction.organization_extractor import OrganizationExtractor
from app.services.extraction.phone_extractor import PhoneExtractor
from app.services.extraction.social_extractor import SocialExtractor
from app.services.extraction.website_extractor import WebsiteExtractor


class PageDataExtractor:
    """Master extractor delegating to all modular sub-extractors."""

    def __init__(self) -> None:
        self.phone_extractor = PhoneExtractor()
        self.email_extractor = EmailExtractor()
        self.address_extractor = AddressExtractor()
        self.contact_extractor = ContactExtractor()
        self.social_extractor = SocialExtractor()
        self.org_extractor = OrganizationExtractor()
        self.website_extractor = WebsiteExtractor()

    def extract(self, html: str, context: PageContext) -> ExtractionResult:
        """Parse HTML once and run all specialized extractors."""
        parsed_page = ParsedPage(html=html, base_url=context.source_url)
        return self.extract_parsed(parsed_page, context)

    def extract_parsed(self, parsed_page: ParsedPage, context: PageContext) -> ExtractionResult:
        """Extract data points from a pre-parsed page."""
        all_items: list[ExtractedItem] = []

        # 1. Phones & WhatsApp
        all_items.extend(self.phone_extractor.extract(parsed_page, context))

        # 2. Emails
        all_items.extend(self.email_extractor.extract(parsed_page, context))

        # 3. Addresses & Pincodes
        all_items.extend(self.address_extractor.extract(parsed_page, context))

        # 4. Contacts & Key Personnel
        all_items.extend(self.contact_extractor.extract(parsed_page, context))

        # 5. Social Links
        all_items.extend(self.social_extractor.extract(parsed_page, context))

        # 6. Organization Signals
        all_items.extend(self.org_extractor.extract(parsed_page, context))

        # 7. Website & Domain Signals
        all_items.extend(self.website_extractor.extract(parsed_page, context))

        return ExtractionResult(context=context, items=all_items)
