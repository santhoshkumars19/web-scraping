"""
app/core/middleware.py

Production-grade middleware for LeadScout:
  1. RequestIDMiddleware: Correlates every incoming HTTP request with a unique ID (X-Request-ID).
  2. SecurityHeadersMiddleware: Sets security headers (nosniff, referrer, frame options, HSTS).
"""

from __future__ import annotations

import re
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

_REQUEST_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-]{8,64}$")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Assigns or propagates an X-Request-ID header on all requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        incoming_id = request.headers.get("X-Request-ID")

        if incoming_id and _REQUEST_ID_REGEX.match(incoming_id):
            request_id = incoming_id
        else:
            request_id = str(uuid.uuid4())

        request.state.request_id = request_id

        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attaches standard security headers to all responses.

    HSTS is strictly conditional on settings.AUTH_COOKIE_SECURE or HTTPS scheme
    to avoid breaking local HTTP development.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response: Response = await call_next(request)

        # Baseline security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # HSTS only when running in HTTPS / secure mode
        is_https = request.url.scheme == "https" or settings.AUTH_COOKIE_SECURE
        if is_https:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response
