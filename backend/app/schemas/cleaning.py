"""
app/schemas/cleaning.py

Schemas and DTOs for the Data Cleaning and Deduplication Pipeline (Backend Step 7).
"""

from __future__ import annotations

from pydantic import BaseModel


class CleaningResult(BaseModel):
    """Summary of data cleaning and deduplication execution for a ScrapingTask."""

    task_id: str
    organizations_processed: int = 0
    organizations_merged: int = 0
    exact_duplicates_removed: int = 0
    phones_cleaned: int = 0
    emails_cleaned: int = 0
    addresses_cleaned: int = 0
    invalid_phones_removed: int = 0
    invalid_emails_removed: int = 0
    potential_duplicates_flagged: int = 0
    total_duplicates_removed: int = 0
    duration_seconds: float = 0.0
    status: str = "Cleaning completed"
    next_stage: str = "VERIFYING"
