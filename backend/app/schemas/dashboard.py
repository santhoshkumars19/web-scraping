"""
app/schemas/dashboard.py

Pydantic schemas for the dashboard overview and metrics aggregation endpoint:
  • GET /api/dashboard/summary
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from app.schemas.base import AppBaseModel
from app.schemas.task import ScrapingTaskListItem


class CategorySummaryItem(AppBaseModel):
    category: str
    leads: int = 0
    color: str | None = None


class LocationSummaryItem(AppBaseModel):
    location: str
    leads: int = 0


class DashboardSummaryData(AppBaseModel):
    total_leads: int = Field(default=0, description="Total leads collected across user's tasks")
    websites_discovered: int = Field(default=0, description="Total websites discovered/crawled")
    verified_leads: int = Field(default=0, description="Leads with HIGH or MEDIUM verification confidence")
    scraping_tasks: int = Field(default=0, description="Total scraping tasks created by the user")
    recent_tasks: list[ScrapingTaskListItem] = Field(default_factory=list, description="Latest scraping tasks")
    category_summary: list[CategorySummaryItem] = Field(default_factory=list, description="Leads count by top categories")
    location_summary: list[LocationSummaryItem] = Field(default_factory=list, description="Leads count by top locations")


class DashboardSummaryResponse(AppBaseModel):
    success: bool = True
    data: DashboardSummaryData
