"""
app/services/verification/verification_service.py

Lead Data-Quality Verification & Confidence Scoring Service (Backend Step 8).

Orchestrates data evaluation across:
1. Field completeness against task.selected_fields
2. Source quality and provenance assessment
3. Cross-field consistency and conflict detection
4. Deterministic confidence scoring (0–100) and tier mapping (HIGH/MEDIUM/LOW)
5. Idempotent persistence of LeadVerification records
6. Task metrics and stage advancement to SAVING
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.models.extracted_field import ExtractedField
from app.models.lead import Lead
from app.models.lead_verification import LeadVerification
from app.models.organization import Organization, task_organizations
from app.models.scraping_log import ScrapingLog
from app.models.scraping_task import ScrapingTask
from app.repositories.task_repository import TaskRepository
from app.schemas.verification import TaskVerificationSummary, VerificationResult
from app.services.verification.confidence_scorer import ConfidenceScorer
from app.services.verification.consistency_checker import check_consistency
from app.services.verification.field_completeness import calculate_field_completeness
from app.services.verification.source_quality import assess_source_quality

logger = get_logger(__name__)


class VerificationService:
    """Orchestrates data confidence scoring and quality verification for scraping tasks."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = TaskRepository(session)

    async def verify_task(self, task_id: str | uuid.UUID) -> TaskVerificationSummary:
        """Run the verification engine on all leads belonging to a task.

        Args:
            task_id: Task UUID or human-readable task ID (e.g. "TASK-000124").

        Returns:
            TaskVerificationSummary with aggregate metrics and confirmation of stage advancement.
        """
        start_time = time.monotonic()

        # ── 1. Resolve Scraping Task ──────────────────────────────────────────
        task: ScrapingTask | None = None
        if isinstance(task_id, uuid.UUID):
            task = await self.repository.get_by_id(task_id)
        elif isinstance(task_id, str):
            if task_id.startswith("TASK-"):
                task = await self.repository.get_by_task_id(task_id)
            else:
                try:
                    uid = uuid.UUID(task_id)
                    task = await self.repository.get_by_id(uid)
                except ValueError:
                    task = await self.repository.get_by_task_id(task_id)

        if task is None:
            raise AppException(
                message="Scraping task not found.",
                status_code=404,
                code="TASK_NOT_FOUND",
            )

        logger.info("Starting verification engine for task %s", task.task_id)

        # ── 2. Ensure Lead records exist for all task organizations ───────────
        stmt_task_orgs = (
            select(Organization)
            .join(task_organizations, task_organizations.c.organization_id == Organization.id)
            .where(task_organizations.c.task_id == task.id)
        )
        task_orgs = list((await self.session.execute(stmt_task_orgs)).scalars().all())

        stmt_existing_leads = select(Lead).where(Lead.task_id == task.id)
        existing_leads = list((await self.session.execute(stmt_existing_leads)).scalars().all())
        existing_lead_org_ids = {l.organization_id for l in existing_leads}

        new_leads_created = False
        for org in task_orgs:
            if org.id not in existing_lead_org_ids:
                new_lead = Lead(
                    task_id=task.id,
                    organization_id=org.id,
                    status="ACTIVE",
                    verification_status="PENDING",
                )
                self.session.add(new_lead)
                new_leads_created = True

        if new_leads_created:
            await self.session.flush()

        # ── 3. Query Leads with Eager Loaded Relationships ────────────────────
        stmt_leads = (
            select(Lead)
            .where(Lead.task_id == task.id)
            .options(
                selectinload(Lead.organization).selectinload(Organization.websites),
                selectinload(Lead.organization).selectinload(Organization.phone_numbers),
                selectinload(Lead.organization).selectinload(Organization.email_addresses),
                selectinload(Lead.organization).selectinload(Organization.social_links),
                selectinload(Lead.organization).selectinload(Organization.contacts),
                selectinload(Lead.organization).selectinload(Organization.source_pages),
                selectinload(Lead.verification),
            )
        )
        task_leads = list((await self.session.execute(stmt_leads)).scalars().all())

        # ── 4. Query Extracted Fields for Task Organizations ──────────────────
        org_ids = [l.organization_id for l in task_leads if l.organization_id is not None]
        ef_by_org: dict[uuid.UUID, list[ExtractedField]] = {}
        if org_ids:
            stmt_ef = select(ExtractedField).where(ExtractedField.organization_id.in_(org_ids))
            ef_list = list((await self.session.execute(stmt_ef)).scalars().all())
            for ef in ef_list:
                ef_by_org.setdefault(ef.organization_id, []).append(ef)

        # ── 5. Evaluate Leads with Failure Isolation ──────────────────────────
        leads_processed = 0
        high_confidence_count = 0
        medium_confidence_count = 0
        low_confidence_count = 0
        pending_count = 0

        total_completeness = 0.0
        total_source_quality = 0.0
        total_consistency = 0.0

        for lead in task_leads:
            try:
                org = lead.organization
                if org is None:
                    continue

                # 5a. Field Completeness
                completeness = calculate_field_completeness(
                    org=org,
                    selected_fields=task.selected_fields,
                )

                # 5b. Source Quality
                org_efs = ef_by_org.get(org.id, [])
                org_pages = getattr(org, "source_pages", [])
                source_quality = assess_source_quality(
                    org=org,
                    field_availability=completeness.field_availability,
                    extracted_fields=org_efs,
                    source_pages=org_pages,
                )

                # 5c. Consistency & Cross-Field Coherence
                consistency = check_consistency(org)

                # 5d. Deterministic Confidence Score & Tier
                result: VerificationResult = ConfidenceScorer.compute(
                    task_id=task.task_id,
                    organization_id=org.id,
                    lead_id=lead.id,
                    completeness=completeness,
                    source_quality=source_quality,
                    consistency=consistency,
                )

                # 5e. Idempotent Upsert into LeadVerification
                verification = lead.verification
                if verification is None:
                    stmt_v = select(LeadVerification).where(LeadVerification.lead_id == lead.id)
                    verification = (await self.session.execute(stmt_v)).scalar_one_or_none()

                if verification is None:
                    verification = LeadVerification(
                        organization_id=org.id,
                        lead_id=lead.id,
                    )
                    self.session.add(verification)

                verification.status = result.status
                verification.score = result.score
                verification.fields_found = result.fields_found
                verification.total_fields = result.total_fields
                verification.completeness_percentage = result.completeness_percentage
                verification.source_quality_score = result.source_quality_score
                verification.consistency_score = result.consistency_score
                verification.verification_reasons = result.reasons
                verification.source_quality_details = result.source_quality_details.model_dump()
                verification.verified_at = datetime.now(timezone.utc)

                # 5f. Update Lead Status
                lead.verification_status = result.status

                # 5g. Update Accumulators
                leads_processed += 1
                if result.status == "HIGH":
                    high_confidence_count += 1
                elif result.status == "MEDIUM":
                    medium_confidence_count += 1
                else:
                    low_confidence_count += 1

                total_completeness += result.completeness_percentage
                total_source_quality += result.source_quality_score
                total_consistency += result.consistency_score

            except Exception as exc:
                logger.error(
                    "Error verifying lead %s (task %s): %s",
                    lead.id,
                    task.task_id,
                    exc,
                    exc_info=True,
                )
                self.session.add(
                    ScrapingLog(
                        task_id=task.id,
                        organization_id=lead.organization_id,
                        level="ERROR",
                        event_type="VERIFICATION_FAILED",
                        message=f"Verification failed for lead {lead.id}: {exc}",
                    )
                )
                lead.verification_status = "PENDING"
                pending_count += 1

        await self.session.flush()

        # ── 6. Update Task Metrics and Advance Stage ───────────────────────────
        task.verified_count = leads_processed
        task.high_confidence_count = high_confidence_count
        task.medium_confidence_count = medium_confidence_count
        task.low_confidence_count = low_confidence_count
        task.current_stage = "SAVING"
        task.progress = 95
        if task.status != "CANCELLED":
            task.status = "RUNNING"

        duration = time.monotonic() - start_time
        avg_comp = round(total_completeness / leads_processed, 2) if leads_processed > 0 else 0.0
        avg_source = round(total_source_quality / leads_processed, 2) if leads_processed > 0 else 0.0
        avg_cons = round(total_consistency / leads_processed, 2) if leads_processed > 0 else 0.0

        self.session.add(
            ScrapingLog(
                task_id=task.id,
                level="INFO",
                event_type="VERIFICATION_COMPLETED",
                message=(
                    f"Lead data verification completed in {duration:.2f}s. "
                    f"Processed {leads_processed} leads: {high_confidence_count} HIGH, "
                    f"{medium_confidence_count} MEDIUM, {low_confidence_count} LOW, "
                    f"{pending_count} PENDING. Advanced to SAVING."
                ),
            )
        )
        await self.session.commit()

        logger.info(
            "Task %s verification completed in %.2fs. Stage advanced to SAVING (progress 95%%)",
            task.task_id,
            duration,
        )

        return TaskVerificationSummary(
            task_id=task.task_id,
            leads_processed=leads_processed,
            high_confidence_count=high_confidence_count,
            medium_confidence_count=medium_confidence_count,
            low_confidence_count=low_confidence_count,
            pending_count=pending_count,
            average_completeness=avg_comp,
            average_source_quality=avg_source,
            average_consistency=avg_cons,
            duration_seconds=round(duration, 3),
            status="Verification completed",
            next_stage="SAVING",
        )
