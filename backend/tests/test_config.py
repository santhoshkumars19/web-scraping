"""
tests/test_config.py

Tests for the application configuration layer.
"""

from __future__ import annotations

import os
import pytest


@pytest.mark.asyncio
async def test_settings_loaded() -> None:
    """Settings object should be importable and have the expected defaults."""
    from app.core.config import settings

    assert settings.APP_NAME == "LeadScout-Test"
    assert settings.APP_VERSION == "1.0.0"
    assert settings.API_PREFIX == "/api"


@pytest.mark.asyncio
async def test_cors_origins_is_list() -> None:
    """CORS_ORIGINS must always be a list, even when set as a JSON string."""
    from app.core.config import settings

    assert isinstance(settings.CORS_ORIGINS, list)
    assert len(settings.CORS_ORIGINS) > 0


@pytest.mark.asyncio
async def test_database_url_not_empty() -> None:
    """DATABASE_URL must be present and non-empty."""
    from app.core.config import settings

    assert settings.DATABASE_URL
    assert "postgresql" in settings.DATABASE_URL
