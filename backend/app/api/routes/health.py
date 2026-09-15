"""
app/api/routes/health.py

Health, readiness, and liveness endpoints:
  • GET /api/health — Diagnostic overview (reports service, database & redis status)
  • GET /api/ready  — Kubernetes / load-balancer readiness probe (returns 200 if DB is ready, 503 if not)
  • GET /api/live   — Kubernetes liveness probe (200 as long as FastAPI process is running)
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
import redis.asyncio as aioredis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.db.database import get_db, get_session_factory
from app.schemas.base import success

logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "/health",
    summary="Health check",
    description="Diagnostic health probe verifying application, database, and cache availability.",
    response_description="API health status",
)
async def health_check() -> dict:
    """Return overall health status, checking DB and Redis dependencies safely."""
    db_status = "ok"
    redis_status = "ok"

    # Check Database if engine exists
    try:
        factory = get_session_factory()
        async with factory() as session:
            await session.execute(text("SELECT 1"))
    except Exception as e:
        logger.debug("Health check DB probe: %s", e)
        db_status = "unavailable"

    # Check Redis
    try:
        r = aioredis.from_url(
            settings.REDIS_URL,
            socket_connect_timeout=0.5,
            socket_timeout=0.5,
        )
        await r.ping()
        await r.aclose()
    except Exception as e:
        logger.debug("Health check Redis probe: %s", e)
        redis_status = "unavailable"

    return success(
        {
            "status": "ok",
            "service": "leadscout-api",
            "database": db_status,
            "redis": redis_status,
        }
    )


@router.get(
    "/live",
    summary="Liveness probe",
    description="Confirms that the FastAPI process is alive and responsive without touching dependencies.",
)
async def liveness_check() -> dict:
    """Always returns 200 as long as the web server process is responsive."""
    return success({"status": "ok", "service": "leadscout-api"})


@router.get(
    "/ready",
    summary="Readiness probe",
    description="Returns 200 if the application can accept traffic (PostgreSQL accessible), 503 otherwise.",
)
async def readiness_check(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Readiness check. Fails with 503 if primary database is not reachable."""
    try:
        await db.execute(text("SELECT 1"))
        return success({"ready": True, "service": "leadscout-api"})
    except Exception as exc:
        logger.error("Readiness check failed: %s", exc)
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "success": False,
            "error": {
                "code": "SERVICE_UNAVAILABLE",
                "message": "Service is not ready to accept traffic.",
            },
        }
