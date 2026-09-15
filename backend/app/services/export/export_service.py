"""
app/services/export/export_service.py

ExportService — core business logic and orchestration for Lead data exports.
Handles parameter validation, security scoping, formatting, file generation,
and safe Content-Disposition metadata.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.models.lead import Lead
from app.models.scraping_task import ScrapingTask
from app.repositories.task_repository import TaskRepository
from app.services.export.csv_exporter import generate_csv_bytes
from app.services.export.excel_exporter import generate_excel_bytes
from app.services.export.export_formatter import (
    SUPPORTED_EXPORT_FIELDS,
    format_lead_to_export_row,
    normalize_requested_fields,
)
from app.services.export.export_query import ExportQueryBuilder
from app.services.export.filename import build_export_filename

logger = get_logger(__name__)

# Scoped demo user ID for development single-tenant operations
DEMO_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


class ExportService:
    """Service orchestrating export queries, formatting, and file assembly."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.query_builder = ExportQueryBuilder(db)
        self.task_repo = TaskRepository(db)

    # ── Internal Helpers ───────────────────────────────────────────────────────

    def _resolve_fields(self, fields_param: str | Sequence[str] | None) -> tuple[list[str], list[str]]:
        """Resolve requested field keys and their canonical display headers.

        Raises:
            AppException(422, 'INVALID_EXPORT_FIELD') if unsupported fields are requested.
        """
        try:
            active_keys = normalize_requested_fields(fields_param)
        except ValueError as ve:
            raise AppException(
                message=str(ve),
                status_code=422,
                code="INVALID_EXPORT_FIELD",
            ) from ve

        headers = [SUPPORTED_EXPORT_FIELDS[k] for k in active_keys]
        return active_keys, headers

    def _verify_row_limits(self, leads: list[Lead]) -> None:
        """Enforce non-empty results and maximum export bounds."""
        if not leads:
            raise AppException(
                message="No leads match the selected criteria.",
                status_code=404,
                code="NO_LEADS_TO_EXPORT",
            )

        if len(leads) > settings.MAX_EXPORT_ROWS:
            raise AppException(
                message=(
                    f"Export of {len(leads)} rows exceeds the maximum allowed "
                    f"limit of {settings.MAX_EXPORT_ROWS} rows. Please refine your filters."
                ),
                status_code=413,
                code="EXPORT_TOO_LARGE",
            )

    def _generate_rows(
        self,
        leads: list[Lead],
        active_keys: list[str],
    ) -> list[dict[str, str]]:
        """Format leads into canonical export rows."""
        return [format_lead_to_export_row(lead, active_keys) for lead in leads]

    async def _resolve_task(self, task_id: str, user_id: uuid.UUID | None = None) -> ScrapingTask:
        """Find a task by human ID or UUID. Raises 404 if not found or unauthorized."""
        task = await self.task_repo.get_by_task_id(task_id, user_id=user_id)
        if not task:
            try:
                task_uuid = uuid.UUID(task_id)
                stmt = select(ScrapingTask).where(ScrapingTask.id == task_uuid)
                if user_id is not None:
                    stmt = stmt.where(ScrapingTask.user_id == user_id)
                res = await self.db.execute(stmt)
                task = res.scalar_one_or_none()
            except ValueError:
                task = None

        if not task:
            raise AppException(
                message=f"Task '{task_id}' not found.",
                status_code=404,
                code="TASK_NOT_FOUND",
            )
        return task

    # ── Task Exports ──────────────────────────────────────────────────────────

    async def export_task_csv(
        self,
        task_id: str,
        *,
        user_id: uuid.UUID | None = None,
        fields: str | None = None,
    ) -> tuple[bytes, str]:
        """Export leads for a specific task as CSV."""
        task = await self._resolve_task(task_id, user_id=user_id)
        active_keys, headers = self._resolve_fields(fields)

        leads = await self.query_builder.get_export_leads(
            task_id=task.task_id,
            user_id=user_id,
        )
        self._verify_row_limits(leads)

        rows = self._generate_rows(leads, active_keys)
        content = generate_csv_bytes(headers, rows)
        filename = build_export_filename("task", task_id=task.task_id, extension="csv")

        logger.info(
            "EXPORT_COMPLETED: format=csv source=task task_id=%s rows=%d",
            task.task_id,
            len(leads),
        )
        return content, filename

    async def export_task_excel(
        self,
        task_id: str,
        *,
        user_id: uuid.UUID | None = None,
        fields: str | None = None,
    ) -> tuple[bytes, str]:
        """Export leads for a specific task as Excel (.xlsx)."""
        task = await self._resolve_task(task_id, user_id=user_id)
        active_keys, headers = self._resolve_fields(fields)

        leads = await self.query_builder.get_export_leads(
            task_id=task.task_id,
            user_id=user_id,
        )
        self._verify_row_limits(leads)

        rows = self._generate_rows(leads, active_keys)
        content = generate_excel_bytes(headers, rows)
        filename = build_export_filename("task", task_id=task.task_id, extension="xlsx")

        logger.info(
            "EXPORT_COMPLETED: format=excel source=task task_id=%s rows=%d",
            task.task_id,
            len(leads),
        )
        return content, filename

    # ── Global / Filtered Exports ─────────────────────────────────────────────

    async def export_leads_csv(
        self,
        *,
        user_id: uuid.UUID | None = None,
        task_id: str | None = None,
        search: str | None = None,
        category: str | None = None,
        location: str | None = None,
        verification: str | None = None,
        has_phone: bool | None = None,
        has_email: bool | None = None,
        has_website: bool | None = None,
        has_whatsapp: bool | None = None,
        has_contact: bool | None = None,
        has_social: bool | None = None,
        scraped_from: datetime | None = None,
        scraped_to: datetime | None = None,
        sort_by: str = "scraped_date",
        sort_order: str = "desc",
        fields: str | None = None,
        ids: str | None = None,
    ) -> tuple[bytes, str]:
        """Export leads globally matching filters or selected IDs as CSV."""
        if task_id:
            await self._resolve_task(task_id, user_id=user_id)

        active_keys, headers = self._resolve_fields(fields)
        parsed_ids = self._parse_ids(ids)

        leads = await self.query_builder.get_export_leads(
            task_id=task_id,
            user_id=user_id,
            lead_ids=parsed_ids,
            search=search,
            category=category,
            location=location,
            verification=verification,
            has_phone=has_phone,
            has_email=has_email,
            has_website=has_website,
            has_whatsapp=has_whatsapp,
            has_contact=has_contact,
            has_social=has_social,
            scraped_from=scraped_from,
            scraped_to=scraped_to,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        if parsed_ids:
            found_ids = {lead.id for lead in leads}
            if not set(parsed_ids).issubset(found_ids):
                raise AppException(
                    message="One or more selected leads not found.",
                    status_code=404,
                    code="LEAD_NOT_FOUND",
                )

        self._verify_row_limits(leads)

        rows = self._generate_rows(leads, active_keys)
        content = generate_csv_bytes(headers, rows)
        source_type = "selected" if parsed_ids else ("task" if task_id else "all")
        filename = build_export_filename(source_type, task_id=task_id, extension="csv")

        logger.info(
            "EXPORT_COMPLETED: format=csv source=%s rows=%d",
            source_type,
            len(leads),
        )
        return content, filename

    async def export_leads_excel(
        self,
        *,
        user_id: uuid.UUID | None = None,
        task_id: str | None = None,
        search: str | None = None,
        category: str | None = None,
        location: str | None = None,
        verification: str | None = None,
        has_phone: bool | None = None,
        has_email: bool | None = None,
        has_website: bool | None = None,
        has_whatsapp: bool | None = None,
        has_contact: bool | None = None,
        has_social: bool | None = None,
        scraped_from: datetime | None = None,
        scraped_to: datetime | None = None,
        sort_by: str = "scraped_date",
        sort_order: str = "desc",
        fields: str | None = None,
        ids: str | None = None,
    ) -> tuple[bytes, str]:
        """Export leads globally matching filters or selected IDs as Excel."""
        if task_id:
            await self._resolve_task(task_id, user_id=user_id)

        active_keys, headers = self._resolve_fields(fields)
        parsed_ids = self._parse_ids(ids)

        leads = await self.query_builder.get_export_leads(
            task_id=task_id,
            user_id=user_id,
            lead_ids=parsed_ids,
            search=search,
            category=category,
            location=location,
            verification=verification,
            has_phone=has_phone,
            has_email=has_email,
            has_website=has_website,
            has_whatsapp=has_whatsapp,
            has_contact=has_contact,
            has_social=has_social,
            scraped_from=scraped_from,
            scraped_to=scraped_to,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        if parsed_ids:
            found_ids = {lead.id for lead in leads}
            if not set(parsed_ids).issubset(found_ids):
                raise AppException(
                    message="One or more selected leads not found.",
                    status_code=404,
                    code="LEAD_NOT_FOUND",
                )

        self._verify_row_limits(leads)

        rows = self._generate_rows(leads, active_keys)
        content = generate_excel_bytes(headers, rows)
        source_type = "selected" if parsed_ids else ("task" if task_id else "all")
        filename = build_export_filename(source_type, task_id=task_id, extension="xlsx")

        logger.info(
            "EXPORT_COMPLETED: format=excel source=%s rows=%d",
            source_type,
            len(leads),
        )
        return content, filename

    # ── Single Lead Exports ───────────────────────────────────────────────────

    async def export_single_lead_csv(
        self,
        lead_id: str,
        *,
        user_id: uuid.UUID | None = None,
        fields: str | None = None,
    ) -> tuple[bytes, str]:
        """Export a single lead profile as CSV."""
        active_keys, headers = self._resolve_fields(fields)
        try:
            lead_uuid = uuid.UUID(lead_id)
        except ValueError as ve:
            raise AppException(
                message=f"Lead '{lead_id}' not found.",
                status_code=404,
                code="LEAD_NOT_FOUND",
            ) from ve

        leads = await self.query_builder.get_export_leads(
            lead_id=lead_uuid,
            user_id=user_id,
        )
        if not leads:
            raise AppException(
                message=f"Lead '{lead_id}' not found.",
                status_code=404,
                code="LEAD_NOT_FOUND",
            )

        lead = leads[0]
        rows = self._generate_rows([lead], active_keys)
        content = generate_csv_bytes(headers, rows)
        lead_name = getattr(lead.organization, "name", "lead") if lead.organization else "lead"
        filename = build_export_filename("single_lead", lead_name=lead_name, extension="csv")

        logger.info(
            "EXPORT_COMPLETED: format=csv source=single_lead lead_id=%s",
            lead_id,
        )
        return content, filename

    async def export_single_lead_excel(
        self,
        lead_id: str,
        *,
        user_id: uuid.UUID | None = None,
        fields: str | None = None,
    ) -> tuple[bytes, str]:
        """Export a single lead profile as Excel (.xlsx)."""
        active_keys, headers = self._resolve_fields(fields)
        try:
            lead_uuid = uuid.UUID(lead_id)
        except ValueError as ve:
            raise AppException(
                message=f"Lead '{lead_id}' not found.",
                status_code=404,
                code="LEAD_NOT_FOUND",
            ) from ve

        leads = await self.query_builder.get_export_leads(
            lead_id=lead_uuid,
            user_id=user_id,
        )
        if not leads:
            raise AppException(
                message=f"Lead '{lead_id}' not found.",
                status_code=404,
                code="LEAD_NOT_FOUND",
            )

        lead = leads[0]
        rows = self._generate_rows([lead], active_keys)
        content = generate_excel_bytes(headers, rows)
        lead_name = getattr(lead.organization, "name", "lead") if lead.organization else "lead"
        filename = build_export_filename("single_lead", lead_name=lead_name, extension="xlsx")

        logger.info(
            "EXPORT_COMPLETED: format=excel source=single_lead lead_id=%s",
            lead_id,
        )
        return content, filename

    def _parse_ids(self, ids_str: str | None) -> list[uuid.UUID] | None:
        """Parse and validate comma-separated UUID strings."""
        if not ids_str or not ids_str.strip():
            return None

        uuids: list[uuid.UUID] = []
        for raw in ids_str.split(","):
            val = raw.strip()
            if not val:
                continue
            try:
                uuids.append(uuid.UUID(val))
            except ValueError as ve:
                raise AppException(
                    message=f"Invalid lead ID format: '{val}'. Expected valid UUID.",
                    status_code=422,
                    code="INVALID_LEAD_ID",
                ) from ve

        return uuids if uuids else None
