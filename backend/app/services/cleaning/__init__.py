"""
app/services/cleaning/__init__.py

Data Cleaning, Normalization & Deduplication Package (Backend Step 7).
"""

from app.services.cleaning.address_cleaner import clean_address, clean_pincode
from app.services.cleaning.cleaning_service import CleaningService
from app.services.cleaning.deduplication_service import DeduplicationService
from app.services.cleaning.email_cleaner import clean_email
from app.services.cleaning.merge_service import MergeService
from app.services.cleaning.organization_cleaner import (
    clean_organization_name,
    normalize_organization_name_for_match,
)
from app.services.cleaning.organization_matcher import MatchScoreResult, OrganizationMatcher
from app.services.cleaning.phone_cleaner import clean_phone_number
from app.services.cleaning.text_cleaner import clean_text, is_placeholder
from app.services.cleaning.url_cleaner import clean_social_url, clean_url

__all__ = [
    "clean_text",
    "is_placeholder",
    "clean_phone_number",
    "clean_email",
    "clean_url",
    "clean_social_url",
    "clean_address",
    "clean_pincode",
    "clean_organization_name",
    "normalize_organization_name_for_match",
    "DeduplicationService",
    "OrganizationMatcher",
    "MatchScoreResult",
    "MergeService",
    "CleaningService",
]
