"""
app/core/config.py

Application configuration loaded from environment variables via Pydantic Settings.
All secrets and environment-specific values must come from .env — nothing is hard-coded.
"""

from __future__ import annotations

import json
from typing import Any, Union

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralised application settings.

    Values are read (in order of precedence) from:
      1. Environment variables
      2. .env file in the working directory
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────────────
    APP_NAME: str = "LeadScout"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development | staging | production

    # ── API ────────────────────────────────────────────────────────
    API_PREFIX: str = "/api"

    # ── Database ───────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./leadscout.db"

    # ── CORS ───────────────────────────────────────────────────────
    # Accepts JSON array, comma-separated URLs, or a single URL string
    CORS_ORIGINS: Union[list[str], str] = ["http://localhost:3000"]

    # ── Logging ────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"

    # ── Crawler Configuration (Step 5) ─────────────────────────────
    HTTP_TIMEOUT_SECONDS: float = 8.0
    PLAYWRIGHT_TIMEOUT_SECONDS: float = 15.0
    CRAWL_DELAY_SECONDS: float = 0.5
    MAX_RETRIES: int = 1
    MAX_REDIRECTS: int = 5
    MAX_RESPONSE_SIZE_MB: int = 10
    CRAWLER_USER_AGENT: str = "LeadScoutBot/1.0 (+https://leadscout.example/bot)"
    ALLOW_SUBDOMAINS: bool = False
    PLAYWRIGHT_ENABLED: bool = False
    WEBSITE_CRAWL_TIMEOUT_SECONDS: float = 30.0
    CRAWLER_CONCURRENCY: int = 3

    # ── Redis & Celery (Step 9) ────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    CELERY_MAX_RETRIES: int = 3
    CELERY_TASK_TIME_LIMIT: int = 1800
    CELERY_SOFT_TIME_LIMIT: int = 1500
    CELERY_RESULT_EXPIRES: int = 3600
    CELERY_WORKER_CONCURRENCY: int = 4
    CELERY_TASK_ALWAYS_EAGER: bool = False

    # ── Discovery Settings (Step 16A) ──────────────────────────────
    # When False, mock/fixture providers are completely disabled from normal scraping flows.
    # Only automated test runs should set this to True.
    DISCOVERY_ENABLE_FIXTURES: bool = False
    PUBLIC_SEARCH_TIMEOUT_SECONDS: float = 12.0
    PUBLIC_SEARCH_MAX_RETRIES: int = 2

    # ── WebSocket & Realtime (Step 10) ──────────────────────────────
    WEBSOCKET_HEARTBEAT_SECONDS: int = 30
    MAX_WS_CONNECTIONS_PER_TASK: int = 5
    REALTIME_EVENT_THROTTLE_MS: int = 250
    REDIS_PUBSUB_PREFIX: str = "leadscout:task"

    # ── Export Engine (Step 12) ────────────────────────────────────
    MAX_EXPORT_ROWS: int = 10000

    # ── Authentication & Security (Step 13) ─────────────────────────────────────
    JWT_SECRET_KEY: str = "leadscout-insecure-dev-secret-key-change-in-production-min-32-chars-long"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    PASSWORD_MIN_LENGTH: int = 8
    AUTH_LOGIN_MAX_ATTEMPTS: int = 5
    AUTH_LOGIN_WINDOW_SECONDS: int = 300
    AUTH_LOCKOUT_SECONDS: int = 900
    AUTH_COOKIE_NAME: str = "leadscout_access_token"
    AUTH_COOKIE_SECURE: bool = False
    AUTH_COOKIE_SAMESITE: str = "lax"

    # ── Step 14: Hardening & Safety ─────────────────────────────────────────────

    # Stale task detection
    TASK_STALE_AFTER_MINUTES: int = 60

    # Crawler frontier
    MAX_FRONTIER_URLS: int = 5000

    # robots.txt cache & fail-closed policy
    ROBOTS_CACHE_TTL_SECONDS: int = 3600
    # True = treat robots fetch failure as Disallow:/  False = treat as Allow:/
    ROBOTS_FAIL_CLOSED: bool = True

    # Domain circuit breaker
    DOMAIN_FAILURE_THRESHOLD: int = 5
    DOMAIN_COOLDOWN_SECONDS: int = 300

    # API-level rate limiting (per authenticated user)
    SCRAPE_TASK_RATE_LIMIT: int = 10          # max task creations
    SCRAPE_TASK_RATE_WINDOW_SECONDS: int = 3600  # per hour
    API_RATE_LIMIT: int = 100                  # max general API calls
    API_RATE_LIMIT_WINDOW_SECONDS: int = 60   # per minute

    # Request ID tracking
    REQUEST_ID_ENABLED: bool = True

    # Trusted hosts (comma-separated, used in production)
    ALLOWED_HOSTS: str = "*"

    # Docs availability (set to false in production to hide /docs /redoc)
    DOCS_ENABLED: bool = True

    # ── Validators ─────────────────────────────────────────────────

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, v: Any) -> str:
        """Normalize database URL for async drivers (e.g. Render / Heroku postgres://)."""
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+asyncpg://", 1)
            elif v.startswith("postgresql://") and "+asyncpg" not in v:
                return v.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif v.startswith("sqlite://") and "+aiosqlite" not in v:
                return v.replace("sqlite://", "sqlite+aiosqlite://", 1)
        return v

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        """Allow CORS_ORIGINS to be provided as a JSON string, comma-separated string, or plain URL."""
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return ["http://localhost:3000"]
            if v.startswith("[") and v.endswith("]"):
                try:
                    loaded = json.loads(v)
                    if isinstance(loaded, list):
                        return [str(item).strip() for item in loaded if str(item).strip()]
                except Exception:
                    pass
            parts = [part.strip().strip("'\"") for part in v.split(",") if part.strip()]
            return parts if parts else ["http://localhost:3000"]
        if isinstance(v, (list, tuple)):
            return [str(item).strip() for item in v if str(item).strip()]
        return ["http://localhost:3000"]

    @model_validator(mode="after")
    def validate_environment(self) -> "Settings":
        valid_envs = {"development", "staging", "production"}
        if self.ENVIRONMENT not in valid_envs:
            raise ValueError(
                f"ENVIRONMENT must be one of {valid_envs}, got: {self.ENVIRONMENT!r}"
            )

        # Automatically inherit cloud Redis URL for Celery if Celery is on default localhost
        if self.REDIS_URL and "localhost:6379" not in self.REDIS_URL:
            if "localhost:6379" in self.CELERY_BROKER_URL:
                self.CELERY_BROKER_URL = self.REDIS_URL
            if "localhost:6379" in self.CELERY_RESULT_BACKEND:
                base = self.REDIS_URL.rstrip("/0").rstrip("/")
                self.CELERY_RESULT_BACKEND = f"{base}/1" if not base.endswith("/1") else base

        return self

    # ── Convenience helpers ────────────────────────────────────────

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


# Module-level singleton — import this everywhere.
settings = Settings()
