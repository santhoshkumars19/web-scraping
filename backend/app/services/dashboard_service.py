"""
app/services/dashboard_service.py

Service layer for aggregating dashboard overview metrics scoped to an authenticated user:
  • total leads count
  • websites discovered count
  • verified leads count (HIGH/MEDIUM)
  • total scraping tasks count
  • recent tasks list
  • category summary
  • location summary
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead
from app.models.organization import Organization
from app.models.scraping_task import ScrapingTask
from app.schemas.dashboard import (
    CategorySummaryItem,
    DashboardSummaryData,
    LocationSummaryItem,
)
from app.schemas.task import ScrapingTaskListItem

PALETTE_COLORS = ["#2563EB", "#7C3AED", "#059669", "#D97706", "#DC2626", "#0891B2", "#4F46E5"]


class DashboardService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_summary(self, user_id: uuid.UUID) -> DashboardSummaryData:
        """Fetch aggregated metrics for the current user."""

        # 1. Total tasks
        tasks_count_stmt = select(func.count(ScrapingTask.id)).where(ScrapingTask.user_id == user_id)
        total_tasks_res = await self.db.execute(tasks_count_stmt)
        total_tasks = total_tasks_res.scalar_one_or_none() or 0

        # 2. Websites discovered sum
        websites_stmt = select(func.coalesce(func.sum(ScrapingTask.websites_found), 0)).where(
            ScrapingTask.user_id == user_id
        )
        websites_res = await self.db.execute(websites_stmt)
        total_websites = int(websites_res.scalar_one_or_none() or 0)

        # 3. Total leads (active / non-deleted)
        total_leads_stmt = (
            select(func.count(Lead.id))
            .join(ScrapingTask, Lead.task_id == ScrapingTask.id)
            .where(ScrapingTask.user_id == user_id, Lead.status != "DELETED")
        )
        total_leads_res = await self.db.execute(total_leads_stmt)
        total_leads = total_leads_res.scalar_one_or_none() or 0

        # 4. Verified leads (HIGH or MEDIUM)
        verified_stmt = (
            select(func.count(Lead.id))
            .join(ScrapingTask, Lead.task_id == ScrapingTask.id)
            .where(
                ScrapingTask.user_id == user_id,
                Lead.status != "DELETED",
                Lead.verification_status.in_(["HIGH", "MEDIUM"]),
            )
        )
        verified_res = await self.db.execute(verified_stmt)
        verified_leads = verified_res.scalar_one_or_none() or 0

        # 5. Recent tasks (latest 6)
        recent_tasks_stmt = (
            select(ScrapingTask)
            .where(ScrapingTask.user_id == user_id)
            .order_by(desc(ScrapingTask.created_at))
            .limit(6)
        )
        recent_res = await self.db.execute(recent_tasks_stmt)
        recent_tasks_db = recent_res.scalars().all()

        recent_task_items: list[ScrapingTaskListItem] = []
        for t in recent_tasks_db:
            duration = None
            if t.started_at and t.completed_at:
                duration = round((t.completed_at - t.started_at).total_seconds(), 2)

            recent_task_items.append(
                ScrapingTaskListItem(
                    task_id=t.task_id,
                    keyword=t.keyword,
                    location=t.location,
                    status=t.status,
                    progress=t.progress,
                    results_count=t.results_discovered,
                    verified_count=t.verified_count or 0,
                    created_at=t.created_at,
                    started_at=t.started_at,
                    completed_at=t.completed_at,
                    duration=duration,
                )
            )

        # 6. Category summary
        cat_stmt = (
            select(
                func.coalesce(Organization.category, "General").label("cat"),
                func.count(Lead.id).label("cnt"),
            )
            .join(Organization, Lead.organization_id == Organization.id)
            .join(ScrapingTask, Lead.task_id == ScrapingTask.id)
            .where(ScrapingTask.user_id == user_id, Lead.status != "DELETED")
            .group_by("cat")
            .order_by(desc("cnt"))
            .limit(6)
        )
        cat_res = await self.db.execute(cat_stmt)
        category_summary: list[CategorySummaryItem] = []
        for idx, (cat_name, count) in enumerate(cat_res.all()):
            color = PALETTE_COLORS[idx % len(PALETTE_COLORS)]
            category_summary.append(
                CategorySummaryItem(
                    category=cat_name,
                    leads=count,
                    color=color,
                )
            )

        # 7. Location summary
        loc_stmt = (
            select(
                func.coalesce(Organization.city, ScrapingTask.location, "Unknown").label("loc"),
                func.count(Lead.id).label("cnt"),
            )
            .join(Organization, Lead.organization_id == Organization.id)
            .join(ScrapingTask, Lead.task_id == ScrapingTask.id)
            .where(ScrapingTask.user_id == user_id, Lead.status != "DELETED")
            .group_by("loc")
            .order_by(desc("cnt"))
            .limit(6)
        )
        loc_res = await self.db.execute(loc_stmt)
        location_summary: list[LocationSummaryItem] = [
            LocationSummaryItem(location=loc_name, leads=count)
            for loc_name, count in loc_res.all()
        ]

        return DashboardSummaryData(
            total_leads=total_leads,
            websites_discovered=total_websites,
            verified_leads=verified_leads,
            scraping_tasks=total_tasks,
            recent_tasks=recent_task_items,
            category_summary=category_summary,
            location_summary=location_summary,
        )
