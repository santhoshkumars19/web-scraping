"""
app/api/routes/tasks.py

FastAPI routes for Scraping Task lifecycle:
  • POST /api/scrape           — Submit and initialize a new scraping task (201)
  • GET  /api/tasks            — List task history with pagination, filters, and sorting
  • GET  /api/tasks/{task_id}  — Fetch complete task status and metrics
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.core.rate_limiter import check_scrape_task_rate_limit
from app.db.database import get_db
from app.models.user import User
from app.schemas.base import SuccessResponse, success
from app.schemas.task import (
    ScrapingTaskCreate,
    ScrapingTaskDetail,
    ScrapingTaskListItem,
    ScrapingTaskListResponse,
    ScrapingTaskResponse,
    TaskPagination,
)
from app.services.task_service import TaskService

logger = get_logger(__name__)
router = APIRouter()

# In-memory idempotency cache for duplicate request suppression: key -> (task_dict, timestamp)
_IDEMPOTENCY_CACHE: dict[str, dict] = {}


@router.post(
    "/scrape",
    status_code=status.HTTP_201_CREATED,
    summary="Create a scraping task",
    description=(
        "Validate configuration, generate a sequential human-readable Task ID (TASK-XXXXXX), "
        "persist the task in PENDING status, and enqueue the background scraping pipeline via Celery. "
        "Does not run scraping synchronously."
    ),
    response_model=SuccessResponse[ScrapingTaskResponse],
)
async def create_scraping_task(
    payload: ScrapingTaskCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    _rate_limit: Annotated[None, Depends(check_scrape_task_rate_limit)] = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict:
    # Check idempotency
    if idempotency_key:
        cache_k = f"{current_user.id}:{idempotency_key}"
        if cache_k in _IDEMPOTENCY_CACHE:
            logger.info("Idempotency match for key %s (user %s)", idempotency_key, current_user.id)
            return _IDEMPOTENCY_CACHE[cache_k]

    service = TaskService(db)
    task = await service.create_task(payload, user_id=current_user.id)

    # Publish task.queued event
    try:
        from app.realtime.publisher import get_event_publisher
        await get_event_publisher().publish_queued(task.task_id)
    except Exception as pe:
        logger.debug("Realtime publish failed for task %s queued event: %s", task.task_id, pe)

    # ── Enqueue Background Scraping Pipeline via Celery ───────────────────────
    try:
        from app.workers.pipeline import run_scraping_pipeline
        async_result = run_scraping_pipeline.delay(task.task_id)
        celery_id = getattr(async_result, "id", None)
    except Exception as exc:
        logger.error(
            "Failed to enqueue Celery pipeline for task %s: %s",
            task.task_id,
            exc,
            exc_info=True,
        )
        task.status = "FAILED"
        task.failure_reason = "Unable to queue background scraping job."
        await db.commit()
        raise AppException(
            message="Unable to queue background scraping job.",
            status_code=503,
            code="QUEUE_ERROR",
        )

    res = success(
        ScrapingTaskResponse(
            task_id=task.task_id,
            status=task.status,
            location=task.location,
            keyword=task.keyword,
            max_results=task.max_results,
            max_pages_per_site=task.max_pages_per_site,
            progress=task.progress,
            queued=True,
            celery_task_id=celery_id,
            created_at=task.created_at,
        ).model_dump()
    )

    if idempotency_key:
        _IDEMPOTENCY_CACHE[f"{current_user.id}:{idempotency_key}"] = res

    return res



@router.get(
    "/tasks",
    summary="List scraping tasks",
    description="Retrieve paginated history of scraping tasks with optional filtering and sorting.",
    response_model=ScrapingTaskListResponse,
)
async def list_scraping_tasks(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    limit: Annotated[int, Query(ge=1, le=100, description="Items per page (1–100)")] = 20,
    status: Annotated[str | None, Query(description="Filter by task status")] = None,
    location: Annotated[str | None, Query(description="Case-insensitive location search")] = None,
    keyword: Annotated[str | None, Query(description="Case-insensitive keyword search")] = None,
    sort_by: Annotated[
        str,
        Query(description="Sort field: created_at, keyword, location, status, progress"),
    ] = "created_at",
    sort_order: Annotated[
        str,
        Query(pattern="^(asc|desc)$", description="Sort order: asc or desc"),
    ] = "desc",
) -> dict:
    service = TaskService(db)
    tasks, total, total_pages = await service.list_tasks(
        user_id=current_user.id,
        page=page,
        limit=limit,
        status=status,
        location=location,
        keyword=keyword,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    items: list[dict] = []
    for t in tasks:
        # Calculate duration in seconds if task ran to completion
        duration = None
        if t.started_at and t.completed_at:
            duration = round((t.completed_at - t.started_at).total_seconds(), 2)

        items.append(
            ScrapingTaskListItem(
                task_id=t.task_id,
                keyword=t.keyword,
                location=t.location,
                status=t.status,
                progress=t.progress,
                results_count=t.results_discovered,
                verified_count=0,
                created_at=t.created_at,
                started_at=t.started_at,
                completed_at=t.completed_at,
                duration=duration,
            ).model_dump()
        )

    return {
        "success": True,
        "data": items,
        "pagination": TaskPagination(
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages,
        ).model_dump(),
    }


@router.get(
    "/tasks/{task_id}",
    summary="Get task details",
    description="Fetch real-time metrics, status, configuration, and failure reason for a specific scraping task.",
    response_model=SuccessResponse[ScrapingTaskDetail],
)
async def get_scraping_task(
    task_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    service = TaskService(db)
    task = await service.get_task(task_id, user_id=current_user.id)

    return success(
        ScrapingTaskDetail(
            task_id=task.task_id,
            status=task.status,
            current_stage=task.current_stage,
            progress=task.progress,
            location=task.location,
            keyword=task.keyword,
            search_radius=task.search_radius,
            max_results=task.max_results,
            max_pages_per_site=task.max_pages_per_site,
            crawl_depth=task.crawl_depth,
            selected_fields=task.selected_fields or [],
            follow_internal_links=task.follow_internal_links,
            prioritize_contact=task.prioritize_contact,
            prioritize_about=task.prioritize_about,
            prioritize_admissions=task.prioritize_admissions,
            prioritize_staff_management=task.prioritize_staff_management,
            results_discovered=task.results_discovered,
            websites_found=task.websites_found,
            websites_crawled=task.websites_crawled,
            phones_found=task.phones_found,
            emails_found=task.emails_found,
            addresses_found=task.addresses_found,
            duplicates_removed=task.duplicates_removed,
            failed_websites=task.failed_websites,
            started_at=task.started_at,
            completed_at=task.completed_at,
            created_at=task.created_at,
            updated_at=task.updated_at,
            failure_reason=task.failure_reason,
        ).model_dump()
    )
