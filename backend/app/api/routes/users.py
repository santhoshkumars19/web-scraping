"""
app/api/routes/users.py

FastAPI routes for user profile and account management:
  • GET   /api/users/me          — Retrieve authenticated user profile
  • PATCH /api/users/me          — Update editable profile fields (name, company, avatar)
  • PATCH /api/users/me/password — Change account password
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import (
    AuthMessageResponse,
    ChangePasswordRequest,
    UpdateUserRequest,
    UserResponse,
)
from app.schemas.base import SuccessResponse, success
from app.services.auth_service import AuthService

router = APIRouter()


@router.get(
    "/users/me",
    status_code=status.HTTP_200_OK,
    summary="Get User Profile",
    description="Retrieve the current authenticated user's profile details.",
    response_model=SuccessResponse[UserResponse],
)
async def get_profile(
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return success(UserResponse.model_validate(current_user))


@router.patch(
    "/users/me",
    status_code=status.HTTP_200_OK,
    summary="Update User Profile",
    description="Update allowable profile attributes (name, company, avatar_url). Role, email, and ID cannot be altered.",
    response_model=SuccessResponse[UserResponse],
)
async def update_profile(
    payload: UpdateUserRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    service = AuthService(db)
    updated_user = await service.update_profile(current_user, payload)
    return success(UserResponse.model_validate(updated_user))


@router.patch(
    "/users/me/password",
    status_code=status.HTTP_200_OK,
    summary="Change Password",
    description="Change account password after validating current password.",
    response_model=SuccessResponse[AuthMessageResponse],
)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    service = AuthService(db)
    await service.change_password(current_user, payload)
    return success(AuthMessageResponse(message="Password changed successfully."))
