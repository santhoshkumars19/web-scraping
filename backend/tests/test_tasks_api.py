"""
tests/test_tasks_api.py

Integration tests for the Scraping Task API and Task Creation Workflow:
  • POST /api/scrape
  • GET /api/tasks
  • GET /api/tasks/{task_id}
  • Validation rules
  • Pagination, filtering, sorting
  • Concurrency and ID uniqueness
"""

from __future__ import annotations

import asyncio
import re
import pytest
from httpx import AsyncClient


VALID_PAYLOAD = {
    "location": "Puducherry",
    "keyword": "CBSE Schools",
    "search_radius": 25,
    "max_results": 100,
    "max_pages_per_site": 20,
    "selected_fields": [
        "name",
        "phone",
        "email",
        "website",
        "address",
        "whatsapp",
        "social_links",
    ],
    "crawl_depth": 3,
    "follow_internal_links": True,
    "prioritize_contact": True,
    "prioritize_about": True,
    "prioritize_admissions": True,
    "prioritize_staff_management": True,
}


# ── 1. Task Creation ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_task_success(test_app_client: AsyncClient) -> None:
    """POST /api/scrape creates a task in PENDING state and returns HTTP 201."""
    response = await test_app_client.post("/api/scrape", json=VALID_PAYLOAD)
    assert response.status_code == 201

    body = response.json()
    assert body["success"] is True
    data = body["data"]

    # Verify task ID format: TASK-XXXXXX
    assert re.match(r"^TASK-\d{6}$", data["task_id"])
    assert data["status"] == "PENDING"
    assert data["progress"] == 0
    assert data["location"] == "Puducherry"
    assert data["keyword"] == "CBSE Schools"
    assert data["max_results"] == 100
    assert data["max_pages_per_site"] == 20
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_task_normalizes_inputs(test_app_client: AsyncClient) -> None:
    """Whitespace should be stripped and selected fields deduplicated."""
    payload = dict(VALID_PAYLOAD)
    payload["location"] = "   Chennai, Tamil Nadu   "
    payload["keyword"] = "  Hospitals  "
    payload["selected_fields"] = ["phone", "EMAIL", "phone", "email", "  website  "]

    response = await test_app_client.post("/api/scrape", json=payload)
    assert response.status_code == 201

    data = response.json()["data"]
    assert data["location"] == "Chennai, Tamil Nadu"
    assert data["keyword"] == "Hospitals"

    # Verify via detail view that fields were normalized & deduplicated
    detail_res = await test_app_client.get(f"/api/tasks/{data['task_id']}")
    detail_data = detail_res.json()["data"]
    assert detail_data["selected_fields"] == ["phone", "email", "website"]


@pytest.mark.asyncio
async def test_create_task_with_social_fields(test_app_client: AsyncClient) -> None:
    """Fields like instagram, facebook, linkedin, youtube, twitter should be valid."""
    payload = dict(VALID_PAYLOAD)
    payload["selected_fields"] = [
        "name",
        "instagram",
        "facebook",
        "linkedin",
        "youtube",
        "twitter",
        "other_social_links",
    ]

    response = await test_app_client.post("/api/scrape", json=payload)
    assert response.status_code == 201

    detail_res = await test_app_client.get(f"/api/tasks/{response.json()['data']['task_id']}")
    detail_data = detail_res.json()["data"]
    assert "instagram" in detail_data["selected_fields"]
    assert "facebook" in detail_data["selected_fields"]



# ── 2. Input Validation (HTTP 422) ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_validation_missing_location(test_app_client: AsyncClient) -> None:
    payload = dict(VALID_PAYLOAD)
    del payload["location"]
    res = await test_app_client.post("/api/scrape", json=payload)
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_validation_short_location(test_app_client: AsyncClient) -> None:
    payload = dict(VALID_PAYLOAD)
    payload["location"] = " A "  # Only 1 char after stripping
    res = await test_app_client.post("/api/scrape", json=payload)
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_validation_missing_keyword(test_app_client: AsyncClient) -> None:
    payload = dict(VALID_PAYLOAD)
    del payload["keyword"]
    res = await test_app_client.post("/api/scrape", json=payload)
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_validation_empty_selected_fields(test_app_client: AsyncClient) -> None:
    payload = dict(VALID_PAYLOAD)
    payload["selected_fields"] = []
    res = await test_app_client.post("/api/scrape", json=payload)
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_validation_invalid_selected_field(test_app_client: AsyncClient) -> None:
    payload = dict(VALID_PAYLOAD)
    payload["selected_fields"] = ["name", "unsupported_field_xyz"]
    res = await test_app_client.post("/api/scrape", json=payload)
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_validation_max_results_bounds(test_app_client: AsyncClient) -> None:
    # Under minimum (0)
    p1 = dict(VALID_PAYLOAD)
    p1["max_results"] = 0
    res1 = await test_app_client.post("/api/scrape", json=p1)
    assert res1.status_code == 422

    # Over maximum (5001)
    p2 = dict(VALID_PAYLOAD)
    p2["max_results"] = 5001
    res2 = await test_app_client.post("/api/scrape", json=p2)
    assert res2.status_code == 422


@pytest.mark.asyncio
async def test_validation_max_pages_per_site_bounds(test_app_client: AsyncClient) -> None:
    p1 = dict(VALID_PAYLOAD)
    p1["max_pages_per_site"] = 0
    assert (await test_app_client.post("/api/scrape", json=p1)).status_code == 422

    p2 = dict(VALID_PAYLOAD)
    p2["max_pages_per_site"] = 101
    assert (await test_app_client.post("/api/scrape", json=p2)).status_code == 422


@pytest.mark.asyncio
async def test_validation_crawl_depth_bounds(test_app_client: AsyncClient) -> None:
    p1 = dict(VALID_PAYLOAD)
    p1["crawl_depth"] = 0
    assert (await test_app_client.post("/api/scrape", json=p1)).status_code == 422

    p2 = dict(VALID_PAYLOAD)
    p2["crawl_depth"] = 11
    assert (await test_app_client.post("/api/scrape", json=p2)).status_code == 422


# ── 3. Single Task Retrieval & 404 ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_task_by_id(test_app_client: AsyncClient) -> None:
    create_res = await test_app_client.post("/api/scrape", json=VALID_PAYLOAD)
    task_id = create_res.json()["data"]["task_id"]

    res = await test_app_client.get(f"/api/tasks/{task_id}")
    assert res.status_code == 200

    data = res.json()["data"]
    assert data["task_id"] == task_id
    assert data["status"] == "PENDING"
    assert data["current_stage"] == "CREATING_TASK"
    assert data["progress"] == 0
    assert data["location"] == "Puducherry"
    assert data["keyword"] == "CBSE Schools"
    assert data["search_radius"] == 25
    assert data["max_results"] == 100
    assert data["max_pages_per_site"] == 20
    assert data["crawl_depth"] == 3
    assert data["follow_internal_links"] is True
    assert data["prioritize_contact"] is True
    assert data["results_discovered"] == 0
    assert data["started_at"] is None
    assert data["completed_at"] is None
    assert data["failure_reason"] is None


@pytest.mark.asyncio
async def test_get_task_not_found(test_app_client: AsyncClient) -> None:
    res = await test_app_client.get("/api/tasks/TASK-999999")
    assert res.status_code == 404

    body = res.json()
    assert body["success"] is False
    assert body["error"]["code"] == "TASK_NOT_FOUND"
    assert "not found" in body["error"]["message"].lower()


# ── 4. Task History / List, Pagination, Filtering, Sorting ────────────────────

@pytest.mark.asyncio
async def test_list_tasks_pagination(test_app_client: AsyncClient) -> None:
    # Create 3 tasks
    for i in range(3):
        payload = dict(VALID_PAYLOAD)
        payload["keyword"] = f"Test Query {i}"
        await test_app_client.post("/api/scrape", json=payload)

    # Page 1, limit 2
    res = await test_app_client.get("/api/tasks?page=1&limit=2")
    assert res.status_code == 200

    body = res.json()
    assert body["success"] is True
    assert len(body["data"]) == 2
    assert body["pagination"]["page"] == 1
    assert body["pagination"]["limit"] == 2
    assert body["pagination"]["total"] >= 3
    assert body["pagination"]["total_pages"] >= 2


@pytest.mark.asyncio
async def test_list_tasks_filtering(test_app_client: AsyncClient) -> None:
    p1 = dict(VALID_PAYLOAD)
    p1["location"] = "Kochi, Kerala"
    p1["keyword"] = "Ayurvedic Clinics"
    await test_app_client.post("/api/scrape", json=p1)

    p2 = dict(VALID_PAYLOAD)
    p2["location"] = "Jaipur, Rajasthan"
    p2["keyword"] = "Heritage Hotels"
    await test_app_client.post("/api/scrape", json=p2)

    # Filter by location (partial, case-insensitive)
    res_loc = await test_app_client.get("/api/tasks?location=kochi")
    assert res_loc.status_code == 200
    items_loc = res_loc.json()["data"]
    assert any(item["location"] == "Kochi, Kerala" for item in items_loc)
    assert not any(item["location"] == "Jaipur, Rajasthan" for item in items_loc)

    # Filter by keyword
    res_kw = await test_app_client.get("/api/tasks?keyword=hotels")
    assert res_kw.status_code == 200
    items_kw = res_kw.json()["data"]
    assert any(item["keyword"] == "Heritage Hotels" for item in items_kw)
    assert not any(item["keyword"] == "Ayurvedic Clinics" for item in items_kw)


@pytest.mark.asyncio
async def test_list_tasks_sorting(test_app_client: AsyncClient) -> None:
    res = await test_app_client.get("/api/tasks?sort_by=created_at&sort_order=asc")
    assert res.status_code == 200

    res_desc = await test_app_client.get("/api/tasks?sort_by=created_at&sort_order=desc")
    assert res_desc.status_code == 200


@pytest.mark.asyncio
async def test_list_tasks_invalid_sort(test_app_client: AsyncClient) -> None:
    res = await test_app_client.get("/api/tasks?sort_by=illegal_column;DROP TABLE--")
    # Custom validation error translates to 422
    assert res.status_code == 422


# ── 5. Concurrency & ID Uniqueness ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_concurrent_task_id_generation(test_app_client: AsyncClient) -> None:
    """Concurrent requests must generate unique, distinct task IDs without collisions."""
    async def make_task(idx: int):
        p = dict(VALID_PAYLOAD)
        p["keyword"] = f"Concurrent Test {idx}"
        return await test_app_client.post("/api/scrape", json=p)

    responses = await asyncio.gather(*[make_task(i) for i in range(5)])

    task_ids = []
    for r in responses:
        assert r.status_code == 201
        tid = r.json()["data"]["task_id"]
        assert re.match(r"^TASK-\d{6}$", tid)
        task_ids.append(tid)

    # Ensure zero duplicates
    assert len(task_ids) == len(set(task_ids))


# ── 6. Internal Service Status Update Methods ─────────────────────────────────

@pytest.mark.asyncio
async def test_internal_status_update_methods(db_session) -> None:
    """Verify internal worker lifecycle methods on TaskService."""
    from app.schemas.task import ScrapingTaskCreate
    from app.services.task_service import TaskService

    service = TaskService(db_session)
    task_in = ScrapingTaskCreate(**VALID_PAYLOAD)
    task = await service.create_task(task_in)
    tid = task.task_id

    # Start task
    started = await service.start_task(tid)
    assert started.status == "RUNNING"
    assert started.current_stage == "DISCOVERING"
    assert started.started_at is not None

    # Update stage & progress
    staged = await service.update_stage(tid, "CRAWLING")
    assert staged.current_stage == "CRAWLING"

    progressed = await service.update_progress(tid, 50)
    assert progressed.progress == 50

    # Complete task
    completed = await service.complete_task(tid)
    assert completed.status == "COMPLETED"
    assert completed.current_stage == "COMPLETED"
    assert completed.progress == 100
    assert completed.completed_at is not None

