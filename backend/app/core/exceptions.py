"""
app/core/exceptions.py

Centralised exception hierarchy for the LeadScout API.

All application-level errors should derive from AppException so that
the global exception handler can return a consistent JSON envelope.
"""

from __future__ import annotations

from typing import Any


# ─── Application base exception ─────────────────────────────────────────────


class AppException(Exception):
    """Base class for all LeadScout application exceptions.

    Attributes:
        status_code: HTTP status code to return.
        code:        Machine-readable error code string (e.g. "NOT_FOUND").
        message:     Human-readable description suitable for API consumers.
        details:     Optional extra context (not shown in production).
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 500,
        code: str = "INTERNAL_ERROR",
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


# ─── Derived typed exceptions ────────────────────────────────────────────────


class NotFoundError(AppException):
    """Raised when a requested resource cannot be found."""

    def __init__(self, message: str = "Resource not found.", details: Any = None) -> None:
        super().__init__(
            message,
            status_code=404,
            code="NOT_FOUND",
            details=details,
        )


class ValidationError(AppException):
    """Raised when business-rule validation fails (distinct from Pydantic schema errors)."""

    def __init__(self, message: str = "Invalid request.", details: Any = None) -> None:
        super().__init__(
            message,
            status_code=422,
            code="VALIDATION_ERROR",
            details=details,
        )


class ConflictError(AppException):
    """Raised when an operation conflicts with the current resource state."""

    def __init__(self, message: str = "Resource conflict.", details: Any = None) -> None:
        super().__init__(
            message,
            status_code=409,
            code="CONFLICT",
            details=details,
        )


class ServiceUnavailableError(AppException):
    """Raised when a downstream service (e.g. DB) is temporarily unavailable."""

    def __init__(
        self, message: str = "Service temporarily unavailable.", details: Any = None
    ) -> None:
        super().__init__(
            message,
            status_code=503,
            code="SERVICE_UNAVAILABLE",
            details=details,
        )


# ─── Authentication & Authorization Exceptions (Step 13) ─────────────────────


class UnauthenticatedError(AppException):
    """Raised when request lacks valid authentication."""

    def __init__(
        self, message: str = "Authentication required.", details: Any = None
    ) -> None:
        super().__init__(
            message,
            status_code=401,
            code="UNAUTHENTICATED",
            details=details,
        )


class InvalidCredentialsError(AppException):
    """Raised on bad email or password during login."""

    def __init__(
        self, message: str = "Invalid email or password.", details: Any = None
    ) -> None:
        super().__init__(
            message,
            status_code=401,
            code="INVALID_CREDENTIALS",
            details=details,
        )


class UserAlreadyExistsError(AppException):
    """Raised when signup email is already registered."""

    def __init__(
        self,
        message: str = "An account with this email already exists.",
        details: Any = None,
    ) -> None:
        super().__init__(
            message,
            status_code=409,
            code="USER_ALREADY_EXISTS",
            details=details,
        )


class AccountDisabledError(AppException):
    """Raised when account is deactivated/disabled."""

    def __init__(
        self, message: str = "Account is disabled.", details: Any = None
    ) -> None:
        super().__init__(
            message,
            status_code=403,
            code="ACCOUNT_DISABLED",
            details=details,
        )


class PermissionDeniedError(AppException):
    """Raised when authenticated user lacks authorization/role."""

    def __init__(
        self, message: str = "Permission denied.", details: Any = None
    ) -> None:
        super().__init__(
            message,
            status_code=403,
            code="PERMISSION_DENIED",
            details=details,
        )


class TokenExpiredError(AppException):
    """Raised when JWT token has expired."""

    def __init__(
        self, message: str = "Authentication token has expired.", details: Any = None
    ) -> None:
        super().__init__(
            message,
            status_code=401,
            code="TOKEN_EXPIRED",
            details=details,
        )


class InvalidTokenError(AppException):
    """Raised when JWT token is invalid or malformed."""

    def __init__(
        self, message: str = "Invalid or expired authentication token.", details: Any = None
    ) -> None:
        super().__init__(
            message,
            status_code=401,
            code="INVALID_TOKEN",
            details=details,
        )


class RateLimitExceededError(AppException):
    """Raised when login attempt rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Too many login attempts. Please try again later.",
        details: Any = None,
    ) -> None:
        super().__init__(
            message,
            status_code=429,
            code="TOO_MANY_REQUESTS",
            details=details,
        )


# ─── Standardized Domain & System Exceptions (Step 14) ───────────────────────


class RateLimitedError(AppException):
    """Raised when API or crawler request exceeds allowed rate."""

    def __init__(
        self,
        message: str = "Too many requests. Please try again later.",
        details: Any = None,
    ) -> None:
        super().__init__(
            message,
            status_code=429,
            code="RATE_LIMITED",
            details=details,
        )


class ForbiddenError(AppException):
    """Raised when access to a resource is forbidden."""

    def __init__(self, message: str = "Access forbidden.", details: Any = None) -> None:
        super().__init__(
            message,
            status_code=403,
            code="FORBIDDEN",
            details=details,
        )


class TaskNotFoundError(AppException):
    """Raised when a scraping task does not exist or is not accessible."""

    def __init__(self, message: str = "Scraping task not found.", details: Any = None) -> None:
        super().__init__(
            message,
            status_code=404,
            code="TASK_NOT_FOUND",
            details=details,
        )


class TaskFailedError(AppException):
    """Raised when a scraping task encounters an irrecoverable failure."""

    def __init__(self, message: str = "Scraping task failed.", details: Any = None) -> None:
        super().__init__(
            message,
            status_code=500,
            code="TASK_FAILED",
            details=details,
        )


class TaskCancelledError(AppException):
    """Raised when attempting an operation on a cancelled task."""

    def __init__(self, message: str = "Scraping task has been cancelled.", details: Any = None) -> None:
        super().__init__(
            message,
            status_code=400,
            code="TASK_CANCELLED",
            details=details,
        )


class LeadNotFoundError(AppException):
    """Raised when a lead record does not exist or is not accessible."""

    def __init__(self, message: str = "Lead not found.", details: Any = None) -> None:
        super().__init__(
            message,
            status_code=404,
            code="LEAD_NOT_FOUND",
            details=details,
        )


class DatabaseError(AppException):
    """Raised when a safe database error is returned to client."""

    def __init__(self, message: str = "A database error occurred.", details: Any = None) -> None:
        super().__init__(
            message,
            status_code=500,
            code="DATABASE_ERROR",
            details=details,
        )


class RedisServiceError(AppException):
    """Raised when a Redis service dependency is unavailable."""

    def __init__(self, message: str = "Cache service is temporarily unavailable.", details: Any = None) -> None:
        super().__init__(
            message,
            status_code=503,
            code="REDIS_ERROR",
            details=details,
        )


class SsrfBlockedError(AppException):
    """Raised when an outbound URL is blocked by SSRF protection."""

    def __init__(self, message: str = "The destination URL is not permitted.", details: Any = None) -> None:
        super().__init__(
            message,
            status_code=400,
            code="SSRF_BLOCKED",
            details=details,
        )


