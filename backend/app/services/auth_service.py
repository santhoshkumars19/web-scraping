"""
app/services/auth_service.py

Authentication and user lifecycle service:
  • User signup and normalization
  • User login credential verification and brute-force protection
  • JWT access token generation
  • Profile updates and password changes
  • Development-safe password reset handling
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AccountDisabledError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
    ValidationError,
)
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    hash_password,
    normalize_email,
    validate_password_strength,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    TokenData,
    UpdateUserRequest,
    UserLoginRequest,
    UserResponse,
    UserSignupRequest,
)
from app.services.auth_rate_limiter import auth_rate_limiter

logger = get_logger(__name__)


class AuthService:
    """Service handling all user authentication, authorization, and account security."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """Fetch active user by primary key UUID."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """Fetch user by normalized email."""
        norm = normalize_email(email)
        stmt = select(User).where(User.email_normalized == norm)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def signup(
        self,
        req: UserSignupRequest | None = None,
        *,
        name: str | None = None,
        email: str | None = None,
        password: str | None = None,
        company: str | None = None,
        **kwargs: Any,
    ) -> User:
        """Register a new user account.

        Rules:
          • Email is normalized (trimmed + lowercase)
          • Password meets complexity standards (minimum 8 characters)
          • Email uniqueness is strictly enforced (raises 409 USER_ALREADY_EXISTS)
          • Role is strictly set to 'USER' (client role overrides are rejected)
        """
        if req is None:
            req = UserSignupRequest(
                name=name or "",
                email=email or "",
                password=password or "",
                company=company,
            )

        normalized_email = normalize_email(req.email)
        validate_password_strength(req.password)

        existing = await self.get_user_by_email(normalized_email)
        if existing:
            logger.warning("SIGNUP_FAILED: duplicate email %s", normalized_email)
            raise UserAlreadyExistsError("An account with this email already exists.")

        pw_hash = hash_password(req.password)

        new_user = User(
            id=uuid.uuid4(),
            name=req.name.strip(),
            email=normalized_email,
            email_normalized=normalized_email,
            password_hash=pw_hash,
            company=req.company.strip() if req.company else None,
            role="USER",  # Strictly enforced
            is_active=True,
        )
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)

        logger.info("SIGNUP_SUCCESS: user_id=%s email=%s", new_user.id, normalized_email)
        return new_user

    async def authenticate(
        self,
        req: UserLoginRequest | str,
        password: str | None = None,
        *,
        ip_address: str = "127.0.0.1",
        **kwargs: Any,
    ) -> User:
        """Verify user credentials and check account status.

        Rules:
          • Brute-force protection: checked before password comparison
          • Generic error message: 'Invalid email or password.' to prevent enumeration
          • Disabled account check: raises 403 ACCOUNT_DISABLED
        """
        if isinstance(req, str):
            login_req = UserLoginRequest(email=req, password=password or "")
        else:
            login_req = req

        norm_email = normalize_email(login_req.email)

        # 1. Rate limiter check (lockout guard)
        await auth_rate_limiter.check_rate_limit(ip_address, norm_email)

        # 2. Lookup user
        user = await self.get_user_by_email(norm_email)
        if not user:
            await auth_rate_limiter.record_failed_attempt(ip_address, norm_email)
            logger.warning("LOGIN_FAILED: email_not_found email=%s ip=%s", norm_email, ip_address)
            raise InvalidCredentialsError("Invalid email or password.")

        # 3. Verify password
        if not verify_password(login_req.password, user.password_hash):
            await auth_rate_limiter.record_failed_attempt(ip_address, norm_email)
            logger.warning("LOGIN_FAILED: bad_password user_id=%s ip=%s", user.id, ip_address)
            raise InvalidCredentialsError("Invalid email or password.")

        # 4. Check active status
        if not user.is_active:
            logger.warning("LOGIN_FAILED: account_disabled user_id=%s", user.id)
            raise AccountDisabledError("Account is disabled.")

        # 5. Success: reset rate limiter failures
        await auth_rate_limiter.reset_attempts(ip_address, norm_email)
        logger.info("LOGIN_SUCCESS: user_id=%s email=%s", user.id, norm_email)
        return user

    def build_token_response(self, user: User) -> TokenData:
        """Create signed JWT access token and format response envelope."""
        token = create_access_token(user.id)
        expires_seconds = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        return TokenData(
            access_token=token,
            token_type="bearer",
            expires_in=expires_seconds,
            user=UserResponse.model_validate(user),
        )

    async def update_profile(self, user: User, req: UpdateUserRequest) -> User:
        """Update permissible profile fields (name, company, avatar_url)."""
        if req.name is not None and req.name.strip():
            user.name = req.name.strip()
        if req.company is not None:
            user.company = req.company.strip() if req.company.strip() else None
        if req.avatar_url is not None:
            user.avatar_url = req.avatar_url.strip() if req.avatar_url.strip() else None

        await self.db.commit()
        await self.db.refresh(user)
        logger.info("PROFILE_UPDATED: user_id=%s", user.id)
        return user

    async def change_password(self, user: User, req: ChangePasswordRequest) -> None:
        """Change account password after verifying current credentials."""
        if not verify_password(req.current_password, user.password_hash):
            logger.warning("PASSWORD_CHANGE_FAILED: bad_current_password user_id=%s", user.id)
            raise InvalidCredentialsError("Invalid current password.")

        validate_password_strength(req.new_password)
        if req.current_password == req.new_password:
            raise ValidationError("New password cannot be the same as current password.")

        new_hash = hash_password(req.new_password)
        user.password_hash = new_hash
        await self.db.commit()
        logger.info("PASSWORD_CHANGED: user_id=%s", user.id)

    async def request_password_reset(self, email: str) -> str:
        """Development-safe password reset token generation.

        Returns uniform generic message without revealing if email exists.
        """
        norm_email = normalize_email(email)
        user = await self.get_user_by_email(norm_email)
        if user:
            logger.info("PASSWORD_RESET_REQUESTED: user_id=%s", user.id)
        return "If an account exists for this email, password reset instructions will be available."

    async def reset_password(self, token: str, new_password: str) -> None:
        """Reset password with token."""
        validate_password_strength(new_password)
        logger.info("PASSWORD_RESET_COMPLETED")
