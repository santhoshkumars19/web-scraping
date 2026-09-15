"""
app/schemas/verification.py

Schemas and DTOs for Lead Data-Quality Verification & Confidence Scoring (Backend Step 8).
"""

from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field


VerificationStatus = Literal["HIGH", "MEDIUM", "LOW", "PENDING"]


class FieldVerification(BaseModel):
    """Evaluation breakdown for an individual extracted field."""

    field_name: str
    available: bool = False
    source_present: bool = False
    source_type: str | None = None
    source_page_type: str | None = None
    source_url: str | None = None
    consistency: str = "NEUTRAL"


class SourceQualityDetails(BaseModel):
    """Aggregate statistics on source origins for a lead's data points."""

    official_website_fields: int = 0
    directory_fields: int = 0
    fields_with_source: int = 0
    total_evaluated_fields: int = 0


class VerificationResult(BaseModel):
    """Full data confidence assessment for a single Lead / Organization."""

    task_id: str
    organization_id: uuid.UUID
    lead_id: uuid.UUID | None = None
    status: VerificationStatus = "PENDING"
    score: int = Field(default=0, ge=0, le=100)
    fields_found: int = 0
    total_fields: int = 0
    completeness_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    source_quality_score: float = Field(default=0.0, ge=0.0, le=100.0)
    consistency_score: float = Field(default=0.0, ge=0.0, le=100.0)
    reasons: dict[str, str] = Field(default_factory=dict)
    flags: list[str] = Field(default_factory=list)
    field_verifications: dict[str, FieldVerification] = Field(default_factory=dict)
    source_quality_details: SourceQualityDetails = Field(default_factory=SourceQualityDetails)


class TaskVerificationSummary(BaseModel):
    """Summary of data verification execution across all leads for a ScrapingTask."""

    task_id: str
    leads_processed: int = 0
    high_confidence_count: int = 0
    medium_confidence_count: int = 0
    low_confidence_count: int = 0
    pending_count: int = 0
    average_completeness: float = 0.0
    average_source_quality: float = 0.0
    average_consistency: float = 0.0
    duration_seconds: float = 0.0
    status: str = "Verification completed"
    next_stage: str = "SAVING"
