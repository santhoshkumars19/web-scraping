"""
app/api/routes/auth.py

FastAPI routes for authentication and session lifecycle:
  • POST /api/auth/signup          — Register a new user account (201)
  • POST /api/auth/login           — Authenticate and issue JWT access token (200)
  • GET  /api/auth/me              — Get current authenticated user profile (200)
  • POST /api/auth/logout          — Invalidate client session and clear cookies (200)
  • POST /api/auth/forgot-password — Request password reset link/instructions (200)
  • POST /api/auth/reset-password  — Reset account password using token (200)
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.core.config import settings
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import (
    AuthMessageResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    TokenData,
    UserLoginRequest,
    UserResponse,
    UserSignupRequest,
)
from app.schemas.base import SuccessResponse, success
from app.services.auth_service import AuthService

router = APIRouter()


def _set_auth_cookie(response: Response, token: str) -> None:
    """Set secure HttpOnly authentication cookie."""
    max_age = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    response.set_cookie(
        key=settings.AUTH_COOKIE_NAME,
        value=token,
        max_age=max_age,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        path="/",
    )


def _clear_auth_cookie(response: Response) -> None:
    """Clear authentication cookie upon logout."""
    response.delete_cookie(
        key=settings.AUTH_COOKIE_NAME,
        path="/",
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )


@router.post(
    "/auth/signup",
    status_code=status.HTTP_201_CREATED,
    summary="User Registration",
    description="Create a new user account with normalized email, password hashing, and return JWT.",
    response_model=SuccessResponse[TokenData],
)
async def signup(
    payload: UserSignupRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    service = AuthService(db)
    user = await service.signup(payload)
    token_data = service.build_token_response(user)
    _set_auth_cookie(response, token_data.access_token)
    return success(token_data)


@router.post(
    "/auth/login",
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Authenticate credentials, check rate limits, and issue a signed JWT access token.",
    response_model=SuccessResponse[TokenData],
)
async def login(
    payload: UserLoginRequest,
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    client_ip = request.client.host if request.client else "127.0.0.1"
    # Forwarded header support if behind proxy
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()

    service = AuthService(db)
    user = await service.authenticate(payload, ip_address=client_ip)
    token_data = service.build_token_response(user)
    _set_auth_cookie(response, token_data.access_token)
    return success(token_data)


@router.get(
    "/auth/me",
    status_code=status.HTTP_200_OK,
    summary="Current User Profile",
    description="Return the authenticated user profile information.",
    response_model=SuccessResponse[UserResponse],
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return success(UserResponse.model_validate(current_user))


@router.post(
    "/auth/logout",
    status_code=status.HTTP_200_OK,
    summary="User Logout",
    description="Clear authentication session cookie and confirm logout.",
    response_model=SuccessResponse[AuthMessageResponse],
)
async def logout(response: Response) -> dict:
    _clear_auth_cookie(response)
    return success(AuthMessageResponse(message="Logged out successfully."))


@router.post(
    "/auth/forgot-password",
    status_code=status.HTTP_200_OK,
    summary="Forgot Password",
    description="Request password reset instructions. Always returns generic response to prevent account enumeration.",
    response_model=SuccessResponse[AuthMessageResponse],
)
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    service = AuthService(db)
    msg = await service.request_password_reset(payload.email)
    return success(AuthMessageResponse(message=msg))


@router.post(
    "/auth/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Reset Password",
    description="Reset account password using valid reset token.",
    response_model=SuccessResponse[AuthMessageResponse],
)
async def reset_password(
    payload: ResetPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    service = AuthService(db)
    await service.reset_password(payload.token, payload.new_password)
    return success(AuthMessageResponse(message="Password has been reset successfully."))
