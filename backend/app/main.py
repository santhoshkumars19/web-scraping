"""
app/main.py

FastAPI application factory.

Responsibilities:
  • Initialise logging early (before any other imports that log).
  • Create the FastAPI application with metadata and security configurations.
  • Register SecurityHeaders, RequestID, CORS, and optional TrustedHost middlewares.
  • Attach global exception handlers for safe, standardized error envelopes.
  • Mount the versioned API router.
  • Manage database and realtime lifecycle via lifespan context manager.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestIDMiddleware, SecurityHeadersMiddleware
from app.db.database import create_engine_and_factory, dispose_engine

# ── Configure logging before any other module logs ────────────────────────────
configure_logging(settings)

logger = get_logger(__name__)


# ─── Lifespan ─────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown resources."""
    # ── Startup ──────────────────────────────────────────────────────────────
    logger.info(
        "Starting %s v%s [env=%s]",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.ENVIRONMENT,
    )
    engine = create_engine_and_factory()
    logger.info("Database engine initialised.")

    # Automatically create missing database tables on fresh deployments
    try:
        import app.models  # noqa: F401 - register models with Base
        from app.db.base import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema verified / created successfully.")
    except Exception as dbe:
        logger.warning("Database schema creation notice: %s", dbe)

    yield  # Application runs here

    # ── Shutdown ─────────────────────────────────────────────────────────────
    logger.info("Shutting down %s …", settings.APP_NAME)
    from app.realtime import connection_manager, subscriber_manager, redis_pubsub

    try:
        await connection_manager.close_all(code=1001, reason="Server shutting down")
        await subscriber_manager.stop_all()
        await redis_pubsub.close()
    except Exception as exc:
        logger.debug("Error during realtime shutdown: %s", exc)

    await dispose_engine()
    logger.info("Shutdown complete.")


# ─── Application factory ──────────────────────────────────────────────────────


def create_application() -> FastAPI:
    """Construct and configure the FastAPI application."""
    docs_url = "/docs" if settings.DOCS_ENABLED else None
    redoc_url = "/redoc" if settings.DOCS_ENABLED else None
    openapi_url = "/openapi.json" if settings.DOCS_ENABLED else None

    app = FastAPI(
        title="LeadScout API",
        description="Backend API for the LeadScout Web Scraping & Lead Discovery Platform.",
        version=settings.APP_VERSION,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
        lifespan=lifespan,
    )

    # ── Security & Request ID Middlewares ─────────────────────────────────────
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # ── Trusted Host (Production only) ────────────────────────────────────────
    if settings.is_production:
        allowed_hosts = [h.strip() for h in settings.ALLOWED_HOSTS.split(",") if h.strip()]
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_origin_regex=r"https://.*\.railway\.app|https://.*\.up\.railway\.app|https://.*\.vercel\.app|https://.*\.onrender\.com|http://localhost:\d+",
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # ── Exception handlers ────────────────────────────────────────────────────
    _register_exception_handlers(app)

    # ── Root endpoint for platform health probes ──────────────────────────────
    @app.get("/", tags=["Health"])
    async def root_ping() -> dict[str, str]:
        return {
            "status": "ok",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs" if settings.DOCS_ENABLED else "disabled",
        }

    # ── API router ────────────────────────────────────────────────────────────
    from app.api.routes import api_router  # noqa: PLC0415
    from app.api.routes.websocket import router as websocket_router  # noqa: PLC0415

    app.include_router(api_router, prefix=settings.API_PREFIX)
    app.include_router(websocket_router)

    return app


# ─── Exception handlers ───────────────────────────────────────────────────────


def _register_exception_handlers(app: FastAPI) -> None:
    """Attach global exception handlers to produce consistent, safe error envelopes."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        """Handle all application-level exceptions."""
        req_id = getattr(request.state, "request_id", None)
        logger.warning(
            "AppException [%s] %s — %s %s (req_id=%s)",
            exc.code,
            exc.status_code,
            request.method,
            request.url.path,
            req_id,
        )
        error_body: dict = {
            "code": exc.code,
            "message": exc.message,
        }
        if exc.details is not None:
            error_body["details"] = exc.details

        headers = {"X-Request-ID": req_id} if req_id else None
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": error_body,
            },
            headers=headers,
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Translate FastAPI HTTPException into the standard error envelope."""
        req_id = getattr(request.state, "request_id", None)
        logger.warning(
            "HTTPException %s — %s %s (req_id=%s)",
            exc.status_code,
            request.method,
            request.url.path,
            req_id,
        )
        code_map = {
            401: "UNAUTHENTICATED",
            403: "FORBIDDEN",
            404: "RESOURCE_NOT_FOUND",
            422: "VALIDATION_ERROR",
            429: "RATE_LIMITED",
        }
        code = code_map.get(exc.status_code, "HTTP_ERROR")
        headers = {"X-Request-ID": req_id} if req_id else None
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": code,
                    "message": exc.detail or "An HTTP error occurred.",
                },
            },
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    @app.exception_handler(PydanticValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError | PydanticValidationError
    ) -> JSONResponse:
        """Handle schema / request validation errors safely with structured field details."""
        req_id = getattr(request.state, "request_id", None)
        logger.debug(
            "Validation error on %s %s (req_id=%s)", request.method, request.url.path, req_id
        )
        details: dict[str, str] = {}
        for err in exc.errors():
            loc = ".".join(str(l) for l in err.get("loc", []) if l != "body")
            field_name = loc or "request"
            details[field_name] = err.get("msg", "Invalid value.")

        headers = {"X-Request-ID": req_id} if req_id else None
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed.",
                    "details": details,
                },
            },
            headers=headers,
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(
        request: Request, exc: SQLAlchemyError
    ) -> JSONResponse:
        """Catch database failures safely without exposing SQL statements or connection details."""
        req_id = getattr(request.state, "request_id", None)
        logger.exception(
            "Database error on %s %s (req_id=%s)", request.method, request.url.path, req_id
        )
        headers = {"X-Request-ID": req_id} if req_id else None
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "DATABASE_ERROR",
                    "message": "A database error occurred. Please try again later.",
                },
            },
            headers=headers,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Catch-all for unexpected exceptions. Stack traces are never exposed to clients."""
        req_id = getattr(request.state, "request_id", None)
        logger.exception(
            "Unhandled exception on %s %s (req_id=%s)",
            request.method,
            request.url.path,
            req_id,
        )
        headers = {"X-Request-ID": req_id} if req_id else None
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred. Please try again later.",
                },
            },
            headers=headers,
        )


app = create_application()

if __name__ == "__main__":
    import os
    import uvicorn

    raw_port = os.getenv("PORT", "8000")
    port = int(raw_port) if raw_port.isdigit() else 8000
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, log_level="info")

