"""
app/schemas/base.py

Reusable Pydantic v2 base configuration and response envelope schemas.

Every API response follows one of two shapes:

  Success  →  {"success": true,  "data": <payload>}
  Error    →  {"success": false, "error": {"code": "...", "message": "..."}}

Future business schemas (tasks, leads, exports, auth) will import from here.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict

# ─── Base config ─────────────────────────────────────────────────────────────


class AppBaseModel(BaseModel):
    """Shared Pydantic config for all LeadScout schemas.

    Key choices:
    • `from_attributes=True`  — allows constructing schema instances directly
                                from SQLAlchemy ORM objects (replaces v1 orm_mode).
    • `populate_by_name=True` — allows both alias and field name during parsing.
    """

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )


# ─── Response envelopes ──────────────────────────────────────────────────────

DataT = TypeVar("DataT")


class SuccessResponse(AppBaseModel, Generic[DataT]):
    """Standard success response envelope.

    Example::

        {
            "success": true,
            "data": { ... }
        }
    """

    success: bool = True
    data: DataT


class ErrorDetail(AppBaseModel):
    """Error detail block nested inside an error response."""

    code: str
    message: str


class ErrorResponse(AppBaseModel):
    """Standard error response envelope.

    Example::

        {
            "success": false,
            "error": {
                "code": "NOT_FOUND",
                "message": "Resource not found."
            }
        }
    """

    success: bool = False
    error: ErrorDetail


# ─── Convenience factory ─────────────────────────────────────────────────────


def success(data: Any) -> dict[str, Any]:
    """Return a serialisable success envelope dict.

    Usage in a route handler::

        return success({"id": task.id, "status": task.status})
    """
    return {"success": True, "data": data}


def error(code: str, message: str) -> dict[str, Any]:
    """Return a serialisable error envelope dict (for internal use only).

    Prefer raising an AppException so the global handler builds the envelope.
    This helper is kept for edge cases where a plain dict is more convenient.
    """
    return {"success": False, "error": {"code": code, "message": message}}
