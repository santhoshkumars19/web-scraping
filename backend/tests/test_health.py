"""
tests/test_health.py

Tests for the health check endpoint.

These tests run entirely in-process using HTTPX's ASGITransport — no real
HTTP server or database connection is required.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_200(client: AsyncClient) -> None:
    """GET /api/health must return HTTP 200."""
    response = await client.get("/api/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_response_envelope(client: AsyncClient) -> None:
    """Response must be wrapped in a success envelope."""
    response = await client.get("/api/health")
    body = response.json()

    assert body["success"] is True
    assert "data" in body


@pytest.mark.asyncio
async def test_health_data_payload(client: AsyncClient) -> None:
    """The data payload must contain status=ok and the correct service name."""
    response = await client.get("/api/health")
    data = response.json()["data"]

    assert data["status"] == "ok"
    assert data["service"] == "leadscout-api"


@pytest.mark.asyncio
async def test_health_content_type(client: AsyncClient) -> None:
    """Response Content-Type must be application/json."""
    response = await client.get("/api/health")
    assert "application/json" in response.headers.get("content-type", "")
