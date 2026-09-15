"""
app/api/routes/dashboard.py

FastAPI routes for Dashboard overview metrics and aggregation:
  • GET /api/dashboard/summary — Summary statistics, counts, recent tasks, and distributions
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get(
    "/dashboard/summary",
    summary="Get user dashboard summary metrics",
    description="Retrieve aggregated statistics including total leads, verified leads, websites, recent tasks, and category/location distributions for the authenticated user.",
    response_model=DashboardSummaryResponse,
)
async def get_dashboard_summary(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DashboardSummaryResponse:
    service = DashboardService(db)
    data = await service.get_summary(user_id=current_user.id)
    return DashboardSummaryResponse(
        success=True,
        data=data,
    )
