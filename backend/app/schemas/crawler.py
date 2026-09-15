"""
app/schemas/crawler.py

Pydantic schemas and DTOs for the Website Crawler (Backend Step 5).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class DiscoveredLink(BaseModel):
    """An internal link discovered within a crawled web page."""

    url: str
    normalized_url: str
    anchor_text: str = ""
    tentative_page_type: str = "OTHER"
    depth: int = 0


class FetchedPage(BaseModel):
    """A fetched HTML page ready for provenance storage and link parsing."""

    url: str
    final_url: str
    normalized_url: str
    status_code: int
    content_type: str
    html: str
    page_title: str | None = None
    page_type: str = "OTHER"
    level_used: Literal["HTTPX", "PLAYWRIGHT"] = "HTTPX"
    response_time_ms: float = 0.0
    discovered_at: datetime | None = None
    crawled_at: datetime | None = None
    internal_links: list[DiscoveredLink] = Field(default_factory=list)


class WebsiteCrawlResult(BaseModel):
    """Result of crawling a single website."""

    website_id: uuid.UUID
    url: str
    domain: str | None = None
    status: Literal["CRAWLED", "FAILED", "BLOCKED"]
    pages_crawled: int = 0
    pages_discovered: int = 0
    playwright_used_count: int = 0
    pages: list[FetchedPage] = Field(default_factory=list)
    error_reason: str | None = None
    duration_seconds: float = 0.0


class TaskCrawlSummary(BaseModel):
    """Summary of crawling all websites attached to a ScrapingTask."""

    task_id: str
    total_websites: int = 0
    websites_crawled: int = 0
    failed_websites: int = 0
    blocked_websites: int = 0
    total_pages_stored: int = 0
    playwright_total: int = 0
    duration_seconds: float = 0.0
    status: str = "Crawling completed"
    next_stage: str = "EXTRACTING"
