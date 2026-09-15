"""
app/api/routes/exports.py

FastAPI routes for exporting Leads data into CSV and Excel (.xlsx) formats:
  • GET /api/tasks/{task_id}/export/csv
  • GET /api/tasks/{task_id}/export/excel
  • GET /api/leads/export/csv
  • GET /api/leads/export/excel
  • GET /api/leads/{lead_id}/export/csv
  • GET /api/leads/{lead_id}/export/excel
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.lead import LeadSortField, LeadSortOrder, LeadVerificationFilter
from app.services.export import ExportService

router = APIRouter()

CSV_MEDIA_TYPE = "text/csv; charset=utf-8"
EXCEL_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


# ── 1. Task-Scoped Exports ───────────────────────────────────────────────────

@router.get(
    "/tasks/{task_id}/export/csv",
    summary="Export task leads as CSV",
    description="Download a UTF-8 CSV containing all leads discovered by a specific task.",
    responses={
        200: {
            "content": {CSV_MEDIA_TYPE: {}},
            "description": "Returns raw CSV file as download attachment.",
        },
        404: {"description": "Task not found or no leads to export."},
    },
)
async def export_task_csv(
    task_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    fields: Annotated[
        str | None,
        Query(description="Comma-separated field keys (e.g. 'name,phone,email,website')"),
    ] = None,
) -> Response:
    service = ExportService(db)
    content, filename = await service.export_task_csv(task_id, user_id=current_user.id, fields=fields)
    return Response(
        content=content,
        media_type=CSV_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/tasks/{task_id}/export/excel",
    summary="Export task leads as Excel (.xlsx)",
    description="Download an Excel spreadsheet containing all leads discovered by a specific task.",
    responses={
        200: {
            "content": {EXCEL_MEDIA_TYPE: {}},
            "description": "Returns .xlsx workbook as download attachment.",
        },
        404: {"description": "Task not found or no leads to export."},
    },
)
async def export_task_excel(
    task_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    fields: Annotated[
        str | None,
        Query(description="Comma-separated field keys (e.g. 'name,phone,email,website')"),
    ] = None,
) -> Response:
    service = ExportService(db)
    content, filename = await service.export_task_excel(task_id, user_id=current_user.id, fields=fields)
    return Response(
        content=content,
        media_type=EXCEL_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── 2. Global / Filtered / Selected Exports ──────────────────────────────────

@router.get(
    "/leads/export/csv",
    summary="Export leads globally or filtered as CSV",
    description="Download a UTF-8 CSV containing leads matching search, filters, or selected IDs.",
    responses={
        200: {
            "content": {CSV_MEDIA_TYPE: {}},
            "description": "Returns raw CSV file as download attachment.",
        },
        404: {"description": "No leads match the selected criteria."},
        413: {"description": "Export exceeds maximum allowed row limit."},
    },
)
async def export_leads_csv(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    task_id: Annotated[str | None, Query(description="Filter leads by specific task ID")] = None,
    ids: Annotated[str | None, Query(description="Comma-separated lead UUIDs to export")] = None,
    fields: Annotated[str | None, Query(description="Comma-separated fields to export")] = None,
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
) -> Response:
    service = ExportService(db)
    content, filename = await service.export_leads_csv(
        user_id=current_user.id,
        task_id=task_id,
        ids=ids,
        fields=fields,
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
    )
    return Response(
        content=content,
        media_type=CSV_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/leads/export/excel",
    summary="Export leads globally or filtered as Excel (.xlsx)",
    description="Download an Excel workbook containing leads matching search, filters, or selected IDs.",
    responses={
        200: {
            "content": {EXCEL_MEDIA_TYPE: {}},
            "description": "Returns .xlsx workbook as download attachment.",
        },
        404: {"description": "No leads match the selected criteria."},
        413: {"description": "Export exceeds maximum allowed row limit."},
    },
)
async def export_leads_excel(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    task_id: Annotated[str | None, Query(description="Filter leads by specific task ID")] = None,
    ids: Annotated[str | None, Query(description="Comma-separated lead UUIDs to export")] = None,
    fields: Annotated[str | None, Query(description="Comma-separated fields to export")] = None,
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
) -> Response:
    service = ExportService(db)
    content, filename = await service.export_leads_excel(
        user_id=current_user.id,
        task_id=task_id,
        ids=ids,
        fields=fields,
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
    )
    return Response(
        content=content,
        media_type=EXCEL_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── 3. Single Lead Exports ───────────────────────────────────────────────────

@router.get(
    "/leads/{lead_id}/export/csv",
    summary="Export single lead as CSV",
    description="Download a single lead profile and its provenance sources as CSV.",
    responses={
        200: {
            "content": {CSV_MEDIA_TYPE: {}},
            "description": "Returns raw CSV file as download attachment.",
        },
        404: {"description": "Lead not found."},
    },
)
async def export_single_lead_csv(
    lead_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    fields: Annotated[
        str | None,
        Query(description="Comma-separated field keys (e.g. 'name,phone,email,website')"),
    ] = None,
) -> Response:
    service = ExportService(db)
    content, filename = await service.export_single_lead_csv(lead_id, user_id=current_user.id, fields=fields)
    return Response(
        content=content,
        media_type=CSV_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/leads/{lead_id}/export/excel",
    summary="Export single lead as Excel (.xlsx)",
    description="Download a single lead profile and its provenance sources as an Excel spreadsheet.",
    responses={
        200: {
            "content": {EXCEL_MEDIA_TYPE: {}},
            "description": "Returns .xlsx workbook as download attachment.",
        },
        404: {"description": "Lead not found."},
    },
)
async def export_single_lead_excel(
    lead_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    fields: Annotated[
        str | None,
        Query(description="Comma-separated field keys (e.g. 'name,phone,email,website')"),
    ] = None,
) -> Response:
    service = ExportService(db)
    content, filename = await service.export_single_lead_excel(lead_id, user_id=current_user.id, fields=fields)
    return Response(
        content=content,
        media_type=EXCEL_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
