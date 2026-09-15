"""
app/schemas/auth.py

Pydantic schemas for authentication, authorization, token lifecycle,
and user profile management.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserSignupRequest(BaseModel):
    """Payload for POST /api/auth/signup."""

    name: str = Field(..., min_length=2, max_length=255, description="Full name of user")
    email: EmailStr = Field(..., max_length=320, description="Valid email address")
    password: str = Field(..., min_length=8, description="Account password (min 8 chars)")
    company: str | None = Field(None, max_length=255, description="Company or organization name")

    model_config = ConfigDict(extra="ignore")


class UserLoginRequest(BaseModel):
    """Payload for POST /api/auth/login."""

    email: EmailStr = Field(..., description="Registered email address")
    password: str = Field(..., min_length=1, description="Account password")

    model_config = ConfigDict(extra="ignore")


class UserResponse(BaseModel):
    """User profile data returned to client (never exposes password_hash)."""

    id: str = Field(..., description="Unique user UUID string")
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    company: str | None = Field(None, description="Company or organization name")
    role: str = Field(..., description="Role: USER or ADMIN")
    avatar_url: str | None = Field(None, description="Profile avatar URL")
    created_at: datetime = Field(..., description="Timestamp of account creation")

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def serialize_uuid(cls, v: Any) -> str:
        return str(v)


class TokenData(BaseModel):
    """Authentication token response envelope."""

    access_token: str = Field(..., description="Signed JWT Bearer access token")
    token_type: Literal["bearer"] = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token lifetime in seconds")
    user: UserResponse = Field(..., description="User profile details")


class UpdateUserRequest(BaseModel):
    """Payload for PATCH /api/users/me."""

    name: str | None = Field(None, min_length=2, max_length=255)
    company: str | None = Field(None, max_length=255)
    avatar_url: str | None = Field(None, max_length=1024)

    model_config = ConfigDict(extra="ignore")


class ChangePasswordRequest(BaseModel):
    """Payload for PATCH /api/users/me/password."""

    current_password: str = Field(..., min_length=1, description="Current account password")
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")

    model_config = ConfigDict(extra="ignore")


class ForgotPasswordRequest(BaseModel):
    """Payload for POST /api/auth/forgot-password."""

    email: EmailStr = Field(..., description="Account email to request password reset")

    model_config = ConfigDict(extra="ignore")


class ResetPasswordRequest(BaseModel):
    """Payload for POST /api/auth/reset-password."""

    token: str = Field(..., min_length=1, description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")

    model_config = ConfigDict(extra="ignore")


class AuthMessageResponse(BaseModel):
    """Simple message response."""

    message: str = Field(..., description="Status or confirmation message")
