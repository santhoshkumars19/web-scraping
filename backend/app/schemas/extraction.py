"""
app/schemas/extraction.py

Schemas and DTOs for the Data Extraction Engine (Backend Step 6).
"""

from __future__ import annotations

from pydantic import BaseModel


class TaskExtractionSummary(BaseModel):
    """Summary of data extraction execution across all SourcePages for a task."""

    task_id: str
    pages_processed: int = 0
    phones_extracted: int = 0
    emails_extracted: int = 0
    addresses_extracted: int = 0
    contacts_extracted: int = 0
    social_links_extracted: int = 0
    provenance_records_created: int = 0
    duration_seconds: float = 0.0
    status: str = "Extraction completed"
    next_stage: str = "CLEANING"
