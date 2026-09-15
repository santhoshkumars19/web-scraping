"""
app/schemas/lead.py

Pydantic v2 schemas for Lead records, contacts, provenance sources,
verification metrics, and pagination.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field

from app.schemas.base import AppBaseModel


# ── Sort & Filter Enums ───────────────────────────────────────────────────────

class LeadSortField(str, Enum):
    ORGANIZATION = "organization"
    CATEGORY = "category"
    LOCATION = "location"
    VERIFICATION = "verification"
    SCRAPED_DATE = "scraped_date"


class LeadSortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class LeadVerificationFilter(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    PENDING = "PENDING"


# ── Sub-entity Schemas ────────────────────────────────────────────────────────

class LeadOrganization(AppBaseModel):
    """Normalized organization details embedded within lead responses."""
    id: uuid.UUID
    name: str
    category: str | None = None
    website: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None


class LeadPhone(AppBaseModel):
    """Phone number record with type and WhatsApp indicator."""
    id: uuid.UUID
    number: str
    normalized_number: str
    type: str
    is_primary: bool = False
    is_whatsapp: bool = False


class LeadEmail(AppBaseModel):
    """Email record with type and primary indicator."""
    id: uuid.UUID
    email: str
    normalized_email: str
    type: str
    is_primary: bool = False


class LeadContact(AppBaseModel):
    """Contact person or department."""
    id: uuid.UUID
    name: str
    designation: str | None = None


class LeadSocialLink(AppBaseModel):
    """Public social media link."""
    platform: str
    url: str
    is_official: bool = False


class LeadWebsite(AppBaseModel):
    """Website URL linked to the organization."""
    id: uuid.UUID
    url: str
    domain: str | None = None
    is_official: bool = False


class LeadSourceRecord(AppBaseModel):
    """Source page provenance record for an extracted data point."""
    field: str
    value: str
    source_url: str
    page_type: str | None = None
    page_title: str | None = None


# ── Verification Schemas ─────────────────────────────────────────────────────

class LeadVerificationSummary(AppBaseModel):
    """Compact verification summary for list views."""
    status: str
    score: int = 0
    fields_found: int = 0
    total_fields: int = 0


class LeadVerificationDetail(AppBaseModel):
    """Full verification assessment breakdown for detail views."""
    status: str
    score: int = 0
    fields_found: int = 0
    total_fields: int = 0
    completeness_percentage: float = 0.0
    source_quality_score: float = 0.0
    consistency_score: float = 0.0
    reasons: dict[str, Any] = Field(default_factory=dict)
    source_quality_details: dict[str, Any] = Field(default_factory=dict)
    verified_at: datetime | None = None


class LeadTaskSummary(AppBaseModel):
    """Metadata summary of the discovery task that originated the lead."""
    task_id: str
    keyword: str
    location: str
    status: str
    created_at: datetime
    completed_at: datetime | None = None


# ── Main Lead Schemas ────────────────────────────────────────────────────────

class LeadListItem(AppBaseModel):
    """Lightweight lead schema optimised for table listing and bulk queries."""
    id: str
    task_id: str
    organization: LeadOrganization
    phone: str | None = None
    alternate_phone: str | None = None
    whatsapp: str | None = None
    email: str | None = None
    website: str | None = None
    location: str | None = None
    contact_person: str | None = None
    designation: str | None = None
    verification: LeadVerificationSummary
    scraped_date: datetime


class LeadResponse(AppBaseModel):
    """Comprehensive lead profile with full provenance and all associated records."""
    id: str
    task_id: str
    task: LeadTaskSummary | None = None
    organization: LeadOrganization
    websites: list[LeadWebsite] = Field(default_factory=list)
    phones: list[LeadPhone] = Field(default_factory=list)
    emails: list[LeadEmail] = Field(default_factory=list)
    contacts: list[LeadContact] = Field(default_factory=list)
    social_links: list[LeadSocialLink] = Field(default_factory=list)
    sources: list[LeadSourceRecord] = Field(default_factory=list)
    verification: LeadVerificationDetail
    scraped_date: datetime


# ── Pagination & List Envelopes ──────────────────────────────────────────────

class LeadPagination(AppBaseModel):
    """Pagination metadata for lead listing."""
    page: int
    limit: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


class LeadListResponse(AppBaseModel):
    """Envelope for paginated lead query results."""
    success: bool = True
    data: list[LeadListItem]
    pagination: LeadPagination


class LeadDetailResponse(AppBaseModel):
    """Envelope for single lead detail response."""
    success: bool = True
    data: LeadResponse
