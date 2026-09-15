"""
app/api/dependencies/auth.py

Authentication and authorization FastAPI dependencies:
  • get_current_user: resolves JWT Bearer token or HttpOnly cookie into active User
  • require_admin: role authorization check for administrator APIs
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AccountDisabledError,
    InvalidTokenError,
    PermissionDeniedError,
    UnauthenticatedError,
)
from app.core.security import decode_access_token
from app.db.database import get_db
from app.models.user import User


async def get_current_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Extract, decode, and authenticate current user from Authorization header or cookie.

    Supports:
      1. Header: Authorization: Bearer <token>
      2. Cookie: leadscout_access_token=<token>
    """
    token: str | None = None

    # 1. Check Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header:
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1].strip()
        else:
            raise InvalidTokenError("Invalid authorization header format. Expected 'Bearer <token>'.")

    # 2. Check HttpOnly cookie
    if not token:
        token = request.cookies.get(settings.AUTH_COOKIE_NAME)

    # 3. Reject if no token provided
    if not token:
        raise UnauthenticatedError("Authentication required.")

    # 4. Decode JWT
    payload = decode_access_token(token)
    sub = payload.get("sub")
    if not sub:
        raise InvalidTokenError("Authentication token payload missing subject.")

    try:
        user_uuid = uuid.UUID(sub)
    except (ValueError, TypeError) as exc:
        raise InvalidTokenError("Authentication token subject is not a valid UUID.") from exc

    # 5. Load user from DB
    stmt = select(User).where(User.id == user_uuid)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthenticatedError("User account not found.")

    # 6. Verify account active
    if not user.is_active:
        raise AccountDisabledError("Account is disabled.")

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Convenience alias guaranteeing active status."""
    return current_user


async def require_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Dependency verifying that the current authenticated user has the ADMIN role."""
    if current_user.role != "ADMIN":
        raise PermissionDeniedError("Administrator privileges required.")
    return current_user
