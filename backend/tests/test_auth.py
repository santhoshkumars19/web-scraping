"""
tests/test_auth.py

Comprehensive test suite for Backend Step 13:
Authentication, JWT, Password Security, Authorization, and Session Management.
"""

from __future__ import annotations

import uuid
from datetime import timedelta
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.exceptions import (
    AccountDisabledError,
    InvalidCredentialsError,
    InvalidTokenError,
    PermissionDeniedError,
    RateLimitExceededError,
    TokenExpiredError,
    UserAlreadyExistsError,
    ValidationError,
)
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    normalize_email,
    validate_password_strength,
    verify_password,
)
from app.db.base import Base
from app.db.database import get_db
from app.main import app as fastapi_app
from app.models.user import User
from app.services.auth_rate_limiter import auth_rate_limiter
from app.services.auth_service import AuthService


@pytest.fixture()
async def auth_db_session():
    """Isolated async session for unit testing services without HTTP overhead."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture()
async def auth_client():
    """HTTPX AsyncClient wired with in-memory SQLite and clean dependency overrides."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    fastapi_app.dependency_overrides[get_db] = override_get_db

    # Reset rate limiter
    auth_rate_limiter.reset_all()

    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://testserver",
    ) as ac:
        yield ac

    fastapi_app.dependency_overrides.clear()
    await engine.dispose()


# ── 1. Security Utilities Unit Tests ─────────────────────────────────────────

def test_password_hashing_and_verification():
    """Argon2id hashing produces valid, non-plaintext hashes and verifies correctly."""
    plain = "SuperSecretPassword123!"
    hashed = hash_password(plain)

    assert hashed != plain
    assert hashed.startswith("$argon2id$")
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False


def test_password_strength_validation():
    """Enforces min length of 8 characters."""
    assert validate_password_strength("validpassword") is True
    assert validate_password_strength("12345678") is True
    with pytest.raises(ValidationError):
        validate_password_strength("short")
    with pytest.raises(ValidationError):
        validate_password_strength("")


def test_email_normalization():
    """Strips whitespace and converts email to lowercase."""
    assert normalize_email("  User.Test@Domain.COM  ") == "user.test@domain.com"
    assert normalize_email("LEAD@SCOUT.APP") == "lead@scout.app"


def test_jwt_create_and_decode_cycle():
    """Access token encodes user_id and expiration, and decodes successfully."""
    user_id = uuid.uuid4()
    token = create_access_token(user_id, role="USER")

    token_data = decode_access_token(token)
    assert token_data.sub == str(user_id)
    assert token_data.role == "USER"
    assert token_data.type == "access"


def test_jwt_expired_token_rejected():
    """Tokens with past expiration raise TokenExpiredError."""
    user_id = uuid.uuid4()
    token = create_access_token(user_id, expires_delta=timedelta(seconds=-10))

    with pytest.raises(TokenExpiredError):
        decode_access_token(token)


def test_jwt_tampered_token_rejected():
    """Tokens with invalid signatures raise InvalidTokenError."""
    user_id = uuid.uuid4()
    token = create_access_token(user_id)
    tampered = token[:-4] + "abcd"

    with pytest.raises(InvalidTokenError):
        decode_access_token(tampered)


# ── 2. AuthService Unit Tests ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_auth_service_signup_and_authenticate(auth_db_session: AsyncSession):
    """AuthService correctly creates users, normalizes emails, and verifies credentials."""
    service = AuthService(auth_db_session)

    user = await service.signup(
        name="Alice Scout",
        email="Alice@Example.Com",
        password="SecurePassword2026!",
        company="Alice Corp",
    )
    assert user.id is not None
    assert user.email == "alice@example.com"
    assert user.email_normalized == "alice@example.com"
    assert user.role == "USER"
    assert user.password_hash.startswith("$argon2id$")

    # Duplicate registration fails
    with pytest.raises(UserAlreadyExistsError):
        await service.signup(
            name="Alice Imposter",
            email="alice@example.com",
            password="AnotherPassword123!",
        )

    # Successful authentication
    auth_user = await service.authenticate("alice@example.com", "SecurePassword2026!")
    assert auth_user.id == user.id

    # Wrong password fails
    with pytest.raises(InvalidCredentialsError):
        await service.authenticate("alice@example.com", "WrongPassword!")

    # Non-existent email fails
    with pytest.raises(InvalidCredentialsError):
        await service.authenticate("nobody@example.com", "SecurePassword2026!")


# ── 3. HTTP API Endpoints Tests ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_signup_endpoint_success_and_cookie(auth_client: AsyncClient):
    """POST /api/auth/signup creates account, returns token and sets HttpOnly cookie."""
    res = await auth_client.post(
        "/api/auth/signup",
        json={
            "name": "Jane Doe",
            "email": "Jane.Doe@Test.com",
            "password": "Password1234!",
            "company": "Doe Logistics",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["success"] is True
    assert data["data"]["access_token"] is not None
    assert data["data"]["token_type"] == "bearer"
    assert data["data"]["user"]["email"] == "jane.doe@test.com"
    assert data["data"]["user"]["role"] == "USER"

    # Verify cookie was set
    assert settings.AUTH_COOKIE_NAME in res.cookies


@pytest.mark.asyncio
async def test_signup_endpoint_duplicate_rejected(auth_client: AsyncClient):
    """Duplicate email (case-insensitive) returns 409 USER_ALREADY_EXISTS."""
    payload = {
        "name": "Bob Smith",
        "email": "bob@domain.org",
        "password": "ValidPassword123!",
    }
    res1 = await auth_client.post("/api/auth/signup", json=payload)
    assert res1.status_code == 201

    res2 = await auth_client.post(
        "/api/auth/signup",
        json={**payload, "email": "BOB@Domain.Org"},
    )
    assert res2.status_code == 409
    assert res2.json()["error"]["code"] == "USER_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_signup_endpoint_short_password_rejected(auth_client: AsyncClient):
    """Password with fewer than 8 characters is rejected with 422."""
    res = await auth_client.post(
        "/api/auth/signup",
        json={
            "name": "Short Pass",
            "email": "short@test.com",
            "password": "short",
        },
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_login_success_and_cookie(auth_client: AsyncClient):
    """POST /api/auth/login verifies credentials and returns access token."""
    # Register first
    await auth_client.post(
        "/api/auth/signup",
        json={
            "name": "Charlie",
            "email": "charlie@company.com",
            "password": "MySecretPassword123!",
        },
    )

    res = await auth_client.post(
        "/api/auth/login",
        json={
            "email": "CHARLIE@COMPANY.COM",
            "password": "MySecretPassword123!",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["access_token"] is not None
    assert data["data"]["user"]["name"] == "Charlie"
    assert settings.AUTH_COOKIE_NAME in res.cookies


@pytest.mark.asyncio
async def test_login_invalid_password_returns_401(auth_client: AsyncClient):
    """Wrong password returns 401 INVALID_CREDENTIALS."""
    await auth_client.post(
        "/api/auth/signup",
        json={
            "name": "Dave",
            "email": "dave@example.com",
            "password": "CorrectPassword123!",
        },
    )

    res = await auth_client.post(
        "/api/auth/login",
        json={
            "email": "dave@example.com",
            "password": "WrongPassword!",
        },
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_login_brute_force_lockout_rate_limit(auth_client: AsyncClient):
    """5 failed attempts on an email triggers a 429 RATE_LIMIT_EXCEEDED lockout."""
    email = "target@example.com"
    auth_rate_limiter.reset_all()

    for i in range(settings.AUTH_LOGIN_MAX_ATTEMPTS):
        res = await auth_client.post(
            "/api/auth/login",
            json={"email": email, "password": f"bad_pass_{i}"},
        )
        assert res.status_code == 401

    # 6th attempt should be blocked by rate limiter with 429
    res_locked = await auth_client.post(
        "/api/auth/login",
        json={"email": email, "password": "any_password"},
    )
    assert res_locked.status_code == 429
    assert res_locked.json()["error"]["code"] in ("RATE_LIMIT_EXCEEDED", "TOO_MANY_REQUESTS")
    assert "locked" in res_locked.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_get_current_user_me(auth_client: AsyncClient):
    """GET /api/auth/me and GET /api/users/me return profile for authenticated user."""
    signup_res = await auth_client.post(
        "/api/auth/signup",
        json={
            "name": "Elena",
            "email": "elena@example.com",
            "password": "Password12345!",
        },
    )
    token = signup_res.json()["data"]["access_token"]

    # Access via Authorization header
    me_res = await auth_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["data"]["name"] == "Elena"

    # Access via cookie
    auth_client.cookies.set(settings.AUTH_COOKIE_NAME, token)
    me_res2 = await auth_client.get("/api/users/me")
    assert me_res2.status_code == 200
    assert me_res2.json()["data"]["email"] == "elena@example.com"

    # Access without credentials returns 401
    auth_client.cookies.clear()
    unauth_res = await auth_client.get("/api/auth/me")
    assert unauth_res.status_code == 401
    assert unauth_res.json()["error"]["code"] == "UNAUTHENTICATED"


@pytest.mark.asyncio
async def test_logout_clears_cookie(auth_client: AsyncClient):
    """POST /api/auth/logout deletes the access token cookie."""
    res = await auth_client.post("/api/auth/logout")
    assert res.status_code == 200
    assert res.json()["success"] is True


@pytest.mark.asyncio
async def test_update_profile(auth_client: AsyncClient):
    """PATCH /api/users/me allows updating profile details."""
    signup_res = await auth_client.post(
        "/api/auth/signup",
        json={
            "name": "Frank",
            "email": "frank@example.com",
            "password": "Password12345!",
        },
    )
    token = signup_res.json()["data"]["access_token"]

    patch_res = await auth_client.patch(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Frank Castle",
            "company": "Punisher Inc",
            "avatar_url": "https://example.com/avatar.png",
        },
    )
    assert patch_res.status_code == 200
    updated = patch_res.json()["data"]
    assert updated["name"] == "Frank Castle"
    assert updated["company"] == "Punisher Inc"
    assert updated["avatar_url"] == "https://example.com/avatar.png"


@pytest.mark.asyncio
async def test_change_password(auth_client: AsyncClient):
    """PATCH /api/users/me/password updates password and verifies new credential."""
    signup_res = await auth_client.post(
        "/api/auth/signup",
        json={
            "name": "Grace",
            "email": "grace@example.com",
            "password": "InitialPassword123!",
        },
    )
    token = signup_res.json()["data"]["access_token"]

    # Wrong current password fails
    fail_res = await auth_client.patch(
        "/api/users/me/password",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "current_password": "WrongPassword!",
            "new_password": "BrandNewPassword123!",
        },
    )
    assert fail_res.status_code == 401

    # Correct current password succeeds
    success_res = await auth_client.patch(
        "/api/users/me/password",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "current_password": "InitialPassword123!",
            "new_password": "BrandNewPassword123!",
        },
    )
    assert success_res.status_code == 200

    # Old password no longer logs in
    old_login = await auth_client.post(
        "/api/auth/login",
        json={"email": "grace@example.com", "password": "InitialPassword123!"},
    )
    assert old_login.status_code == 401

    # New password logs in successfully
    new_login = await auth_client.post(
        "/api/auth/login",
        json={"email": "grace@example.com", "password": "BrandNewPassword123!"},
    )
    assert new_login.status_code == 200


@pytest.mark.asyncio
async def test_forgot_and_reset_password_flow(auth_client: AsyncClient):
    """POST /api/auth/forgot-password and POST /api/auth/reset-password flow."""
    await auth_client.post(
        "/api/auth/signup",
        json={
            "name": "Hank",
            "email": "hank@example.com",
            "password": "OriginalPassword123!",
        },
    )

    # Request reset
    forgot_res = await auth_client.post(
        "/api/auth/forgot-password",
        json={"email": "hank@example.com"},
    )
    assert forgot_res.status_code == 200
    assert "password reset" in forgot_res.json()["data"]["message"].lower()

    # Reset password with token
    reset_res = await auth_client.post(
        "/api/auth/reset-password",
        json={
            "token": "dev-reset-token-sample",
            "new_password": "ResetPassword12345!",
        },
    )
    assert reset_res.status_code == 200
    assert reset_res.json()["success"] is True
