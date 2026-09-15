"""app/models/__init__.py

Export all SQLAlchemy ORM models here so Alembic can discover their
metadata when importing this package, and callers can import models cleanly.
"""

from app.models.user import User, UserRole
from app.models.scraping_task import ScrapingTask
from app.models.organization import Organization, task_organizations
from app.models.lead import Lead
from app.models.lead_verification import LeadVerification
from app.models.website import Website
from app.models.contact import Contact
from app.models.phone_number import PhoneNumber
from app.models.email_address import EmailAddress
from app.models.source_page import SourcePage
from app.models.social_link import SocialLink
from app.models.extracted_field import ExtractedField
from app.models.organization_merge_event import OrganizationMergeEvent
from app.models.scraping_log import ScrapingLog

__all__ = [
    "User",
    "UserRole",
    "ScrapingTask",
    "Organization",
    "task_organizations",
    "Lead",
    "LeadVerification",
    "Website",
    "Contact",
    "PhoneNumber",
    "EmailAddress",
    "SourcePage",
    "SocialLink",
    "ExtractedField",
    "OrganizationMergeEvent",
    "ScrapingLog",
]

