"""
app/api/routes/leads.py

FastAPI routes for Lead management and querying:
  • GET /api/leads              — Global paginated leads query with multi-field search and filters
  • GET /api/leads/{lead_id}    — Complete lead profile with provenance and verification audit trail
  • GET /api/tasks/{task_id}/leads — Paginated leads scoped to a specific scraping task
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.core.rate_limiter import check_api_rate_limit
from app.db.database import get_db
from app.models.user import User
from app.schemas.lead import (
    LeadDetailResponse,
    LeadListResponse,
    LeadPagination,
    LeadSortField,
    LeadSortOrder,
    LeadVerificationFilter,
)
from app.services.lead_service import LeadService

router = APIRouter()


@router.get(
    "/leads",
    summary="List leads globally",
    description="Retrieve paginated list of leads across accessible tasks with search, filtering, and sorting.",
    response_model=LeadListResponse,
)
async def list_leads(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    _rate_limit: Annotated[None, Depends(check_api_rate_limit)] = None,
    task_id: Annotated[str | None, Query(description="Filter leads by specific task ID")] = None,
    page: Annotated[int, Query(ge=1, description="Page number (1-based)")] = 1,
    limit: Annotated[int, Query(ge=1, le=100, description="Items per page (1–100)")] = 20,
    search: Annotated[
        str | None,
        Query(description="Case-insensitive search across name, category, location, phone, email, website, contact"),
    ] = None,
    category: Annotated[str | None, Query(description="Filter by category")] = None,
    location: Annotated[str | None, Query(description="Filter by city, state, or address")] = None,
    verification: Annotated[LeadVerificationFilter | None, Query(description="Filter by verification status")] = None,
    has_phone: Annotated[bool | None, Query(description="Only leads with phone numbers")] = None,
    has_email: Annotated[bool | None, Query(description="Only leads with email addresses")] = None,
    has_website: Annotated[bool | None, Query(description="Only leads with website URLs")] = None,
    has_whatsapp: Annotated[bool | None, Query(description="Only leads with WhatsApp numbers")] = None,
    has_contact: Annotated[bool | None, Query(description="Only leads with identified contact persons")] = None,
    has_social: Annotated[bool | None, Query(description="Only leads with social media profiles")] = None,
    scraped_from: Annotated[datetime | None, Query(description="Leads scraped on or after this timestamp")] = None,
    scraped_to: Annotated[datetime | None, Query(description="Leads scraped on or before this timestamp")] = None,
    sort_by: Annotated[
        LeadSortField,
        Query(description="Sort field: organization, category, location, verification, scraped_date"),
    ] = LeadSortField.SCRAPED_DATE,
    sort_order: Annotated[
        LeadSortOrder,
        Query(description="Sort order: asc or desc"),
    ] = LeadSortOrder.DESC,
) -> LeadListResponse:
    service = LeadService(db)
    items, total, total_pages = await service.list_leads(
        task_id=task_id,
        user_id=current_user.id,
        search=search,
        category=category,
        location=location,
        verification=verification.value if verification else None,
        has_phone=has_phone,
        has_email=has_email,
        has_website=has_website,
        has_whatsapp=has_whatsapp,
        has_contact=has_contact,
        has_social=has_social,
        scraped_from=scraped_from,
        scraped_to=scraped_to,
        sort_by=sort_by.value,
        sort_order=sort_order.value,
        page=page,
        limit=limit,
    )

    return LeadListResponse(
        success=True,
        data=items,
        pagination=LeadPagination(
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
    )


@router.get(
    "/tasks/{task_id}/leads",
    summary="List leads for a specific task",
    description="Retrieve paginated list of leads discovered by a specific scraping task.",
    response_model=LeadListResponse,
)
async def list_task_leads(
    task_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1, description="Page number (1-based)")] = 1,
    limit: Annotated[int, Query(ge=1, le=100, description="Items per page (1–100)")] = 20,
    search: Annotated[
        str | None,
        Query(description="Case-insensitive search across name, category, location, phone, email, website, contact"),
    ] = None,
    category: Annotated[str | None, Query(description="Filter by category")] = None,
    location: Annotated[str | None, Query(description="Filter by city, state, or address")] = None,
    verification: Annotated[LeadVerificationFilter | None, Query(description="Filter by verification status")] = None,
    has_phone: Annotated[bool | None, Query(description="Only leads with phone numbers")] = None,
    has_email: Annotated[bool | None, Query(description="Only leads with email addresses")] = None,
    has_website: Annotated[bool | None, Query(description="Only leads with website URLs")] = None,
    has_whatsapp: Annotated[bool | None, Query(description="Only leads with WhatsApp numbers")] = None,
    has_contact: Annotated[bool | None, Query(description="Only leads with identified contact persons")] = None,
    has_social: Annotated[bool | None, Query(description="Only leads with social media profiles")] = None,
    scraped_from: Annotated[datetime | None, Query(description="Leads scraped on or after this timestamp")] = None,
    scraped_to: Annotated[datetime | None, Query(description="Leads scraped on or before this timestamp")] = None,
    sort_by: Annotated[
        LeadSortField,
        Query(description="Sort field: organization, category, location, verification, scraped_date"),
    ] = LeadSortField.SCRAPED_DATE,
    sort_order: Annotated[
        LeadSortOrder,
        Query(description="Sort order: asc or desc"),
    ] = LeadSortOrder.DESC,
) -> LeadListResponse:
    service = LeadService(db)
    items, total, total_pages = await service.list_task_leads(
        task_id=task_id,
        user_id=current_user.id,
        search=search,
        category=category,
        location=location,
        verification=verification.value if verification else None,
        has_phone=has_phone,
        has_email=has_email,
        has_website=has_website,
        has_whatsapp=has_whatsapp,
        has_contact=has_contact,
        has_social=has_social,
        scraped_from=scraped_from,
        scraped_to=scraped_to,
        sort_by=sort_by.value,
        sort_order=sort_order.value,
        page=page,
        limit=limit,
    )

    return LeadListResponse(
        success=True,
        data=items,
        pagination=LeadPagination(
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
    )


@router.get(
    "/leads/{lead_id}",
    summary="Get lead profile and provenance",
    description="Retrieve full details for a single lead, including contacts, websites, phones, emails, social links, source pages, and verification assessment.",
    response_model=LeadDetailResponse,
)
async def get_lead(
    lead_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> LeadDetailResponse:
    service = LeadService(db)
    lead_response = await service.get_lead(lead_id, user_id=current_user.id)
    return LeadDetailResponse(
        success=True,
        data=lead_response,
    )
