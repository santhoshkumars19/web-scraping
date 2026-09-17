"""
tests/test_real_celery_pipeline_e2e.py

Real end-to-end integration test executing the complete 7-stage Celery scraping pipeline.
Verifies real database persistence, stage transitions, and 100% completion.
"""

from __future__ import annotations

import os
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead
from app.models.lead_verification import LeadVerification
from app.models.organization import Organization
from app.models.scraping_task import ScrapingTask
from app.models.user import User
from app.schemas.task import ScrapingTaskCreate
from app.services.task_service import TaskService
from app.workers.celery_app import celery_app
from app.workers.pipeline import build_pipeline_chain


class _TestSessionContext:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def __aenter__(self) -> AsyncSession:
        return self.session

    async def __aexit__(self, *args: list) -> None:
        pass


@pytest.mark.asyncio
async def test_real_celery_pipeline_e2e(db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch) -> None:
    """Execute complete 7-stage Celery chain end-to-end and verify lead persistence."""

    # 1. Patch session factory to direct all worker background stages to the test DB session
    context = _TestSessionContext(db_session)
    factory_fn = lambda: lambda: context
    monkeypatch.setattr("app.workers.task_context.get_session_factory", factory_fn)
    monkeypatch.setattr("app.jobs.official_website_job.get_session_factory", factory_fn)
    monkeypatch.setattr("app.db.database.get_session_factory", factory_fn)

    # Enable eager execution so Celery chain executes synchronously in-process
    original_eager = celery_app.conf.task_always_eager
    celery_app.conf.task_always_eager = True
    os.environ["DISCOVERY_ENABLE_FIXTURES"] = "true"

    try:
        # Create authenticated test user
        test_user = User(name="E2E User", email="e2e_pipeline@example.com", password_hash="hash")
        db_session.add(test_user)
        await db_session.commit()

        # 2. Create ScrapingTask in database
        service = TaskService(db_session)
        payload = ScrapingTaskCreate(
            location="Ooty",
            keyword="Restaurants",
            search_radius=25,
            max_results=25,
            max_pages_per_site=5,
            selected_fields=["NAME", "PHONE", "EMAIL", "ADDRESS", "WEBSITE"],
        )
        task = await service.create_task(payload, user_id=test_user.id)
        task_id = task.task_id

        assert task.status == "PENDING"
        assert task.progress == 0

        # 3. Build and execute real Celery pipeline chain
        chain_workflow = build_pipeline_chain(task_id)
        chain_result = chain_workflow.apply()

        # 4. Verify PostgreSQL/Test DB task state post-execution
        repo_task = (await db_session.execute(
            select(ScrapingTask).where(ScrapingTask.task_id == task_id)
        )).scalar_one_or_none()

        assert repo_task is not None
        assert repo_task.status == "COMPLETED"
        assert repo_task.progress == 100
        assert repo_task.current_stage == "COMPLETED"
        assert repo_task.results_discovered >= 1
        assert repo_task.started_at is not None
        assert repo_task.completed_at is not None

        # 5. Verify persisted leads and organizations
        res_leads = await db_session.execute(select(Lead))
        leads = list(res_leads.scalars().all())

        res_orgs = await db_session.execute(select(Organization))
        orgs = list(res_orgs.scalars().all())

        assert len(orgs) >= 1
        assert len(leads) >= 1

        for lead in leads:
            assert lead.task_id == repo_task.id
            assert lead.organization_id is not None
            assert lead.status == "ACTIVE"

        # 6. Verify lead verification records
        res_ver = await db_session.execute(select(LeadVerification))
        verifications = list(res_ver.scalars().all())
        assert len(verifications) >= 1
        for ver in verifications:
            assert ver.score >= 0

    finally:
        celery_app.conf.task_always_eager = original_eager
        os.environ.pop("DISCOVERY_ENABLE_FIXTURES", None)
