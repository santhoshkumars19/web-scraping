"""
app/schemas/task.py

Pydantic v2 schemas for Scraping Task requests, responses, lists, and details.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field, field_validator, model_validator

from app.schemas.base import AppBaseModel


# ── Enums ─────────────────────────────────────────────────────────────────────

class TaskStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TaskStage(str, Enum):
    CREATING_TASK = "CREATING_TASK"
    DISCOVERING = "DISCOVERING"
    FINDING_WEBSITES = "FINDING_WEBSITES"
    CRAWLING = "CRAWLING"
    EXTRACTING = "EXTRACTING"
    CLEANING = "CLEANING"
    DEDUPLICATING = "DEDUPLICATING"
    VERIFYING = "VERIFYING"
    SAVING = "SAVING"
    COMPLETED = "COMPLETED"


# ── Supported extraction fields ───────────────────────────────────────────────

SUPPORTED_FIELDS = {
    "name",
    "category",
    "phone",
    "alternate_phone",
    "email",
    "website",
    "address",
    "city",
    "state",
    "pincode",
    "whatsapp",
    "contact_person",
    "designation",
    "social_links",
    "facebook",
    "instagram",
    "linkedin",
    "youtube",
    "twitter",
    "other_social_links",
}


# ── Request Schemas ───────────────────────────────────────────────────────────

class ScrapingTaskCreate(AppBaseModel):
    """Payload for creating a new web scraping discovery task."""

    location: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Geographical location or city name (2–255 characters)",
        examples=["Puducherry", "Bengaluru, Karnataka"],
    )
    keyword: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Target industry, niche, or organization query (2–255 characters)",
        examples=["CBSE Schools", "International Schools"],
    )
    search_radius: int = Field(
        default=25,
        ge=1,
        le=500,
        description="Discovery search radius in kilometers (1–500)",
    )
    max_results: int = Field(
        default=100,
        ge=1,
        le=5000,
        description="Maximum number of organizations to discover (1–5000)",
    )
    max_pages_per_site: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum crawl pages per discovered website (1–100)",
    )
    crawl_depth: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum crawler depth from base URL (1–10)",
    )
    selected_fields: list[str] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of fields to extract. Must contain at least one valid field.",
        examples=[["name", "phone", "email", "website", "address"]],
    )

    # Strategy options
    follow_internal_links: bool = Field(
        default=True,
        description="Whether to follow internal same-domain links",
    )
    prioritize_contact: bool = Field(
        default=True,
        description="Prioritize crawling /contact and /reach-us pages",
    )
    prioritize_about: bool = Field(
        default=True,
        description="Prioritize crawling /about and overview pages",
    )
    prioritize_admissions: bool = Field(
        default=False,
        description="Prioritize crawling /admissions pages",
    )
    prioritize_staff_management: bool = Field(
        default=False,
        description="Prioritize crawling /faculty and /management pages",
    )

    @field_validator("location", "keyword", mode="before")
    @classmethod
    def clean_text(cls, v: Any) -> Any:
        if isinstance(v, str):
            v = v.strip()
            if len(v) < 2:
                raise ValueError("Value must contain at least 2 non-whitespace characters.")
        return v

    @field_validator("selected_fields", mode="before")
    @classmethod
    def validate_and_normalize_fields(cls, v: Any) -> list[str]:
        if not isinstance(v, list) or len(v) == 0:
            raise ValueError("selected_fields must be a non-empty list of strings.")

        normalized: list[str] = []
        for item in v:
            if not isinstance(item, str):
                raise ValueError(f"Invalid field type: {type(item).__name__}. Must be string.")
            field_clean = item.strip().lower()
            if not field_clean:
                continue
            if field_clean not in SUPPORTED_FIELDS:
                raise ValueError(
                    f"Unsupported field '{item}'. Allowed fields: {sorted(list(SUPPORTED_FIELDS))}"
                )
            if field_clean not in normalized:
                normalized.append(field_clean)

        if not normalized:
            raise ValueError("selected_fields must contain at least one supported field.")
        return normalized


# ── Response Schemas ──────────────────────────────────────────────────────────

class ScrapingTaskResponse(AppBaseModel):
    """Succinct response returned upon task creation."""

    task_id: str
    status: str
    location: str
    keyword: str
    max_results: int
    max_pages_per_site: int
    progress: int
    queued: bool = True
    celery_task_id: str | None = None
    created_at: datetime


class ScrapingTaskListItem(AppBaseModel):
    """Single item in the task history list."""

    task_id: str
    keyword: str
    location: str
    status: str
    progress: int
    results_count: int
    verified_count: int
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration: float | None = None  # Duration in seconds


class ScrapingTaskDetail(AppBaseModel):
    """Complete detail view of a single scraping task."""

    task_id: str
    status: str
    current_stage: str
    progress: int
    location: str
    keyword: str
    search_radius: int
    max_results: int
    max_pages_per_site: int
    crawl_depth: int
    selected_fields: list[str] = Field(default_factory=list)
    follow_internal_links: bool
    prioritize_contact: bool
    prioritize_about: bool
    prioritize_admissions: bool
    prioritize_staff_management: bool

    # Metric counts
    results_discovered: int
    websites_found: int
    websites_crawled: int
    phones_found: int
    emails_found: int
    addresses_found: int
    duplicates_removed: int
    failed_websites: int

    # Timestamps
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    failure_reason: str | None


class TaskPagination(AppBaseModel):
    """Pagination metadata for task listing."""

    page: int
    limit: int
    total: int
    total_pages: int


class ScrapingTaskListResponse(AppBaseModel):
    """Envelope for paginated task list."""

    success: bool = True
    data: list[ScrapingTaskListItem]
    pagination: TaskPagination
