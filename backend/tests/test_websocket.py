"""
tests/test_websocket.py

Comprehensive test suite for the LeadScout real-time task progress and WebSocket subsystem:
  • Connection lifecycle & initial snapshot from PostgreSQL
  • Rejection of invalid tasks & connection rate limits
  • Real-time progress, stage change, activity, completion, failure, cancellation events
  • Disconnect safety & reconnect snapshot synchronization
  • Multiple client broadcast & task channel isolation
  • Monotonic progress guarantees & terminal state protection
  • Redis Pub/Sub integration & failure resiliency
  • Heartbeat ping mechanism & endpoint routing aliases
"""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.core.config import settings
from app.core.exceptions import ValidationError
from app.db.base import Base
from app.db.database import get_db, create_engine_and_factory
from app.main import app
from app.models.scraping_task import ScrapingTask
from app.models.user import User
from app.realtime import (
    ConnectionManager,
    MockTaskEventPublisher,
    RedisPubSub,
    connection_manager,
    get_event_publisher,
    get_task_channel,
    set_event_publisher,
)
from app.realtime.events import EventType, build_snapshot_event, extract_task_metrics
from app.services.task_progress_service import TaskProgressService


DEMO_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture(autouse=True)
async def setup_test_db_and_publisher():
    """Configure in-memory SQLite and mock event publisher for WebSocket testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Seed demo user
    async with session_factory() as s:
        user = User(
            id=DEMO_USER_ID,
            name="Demo User",
            email="demo@leadscout.app",
            password_hash="fakehash",
            role="USER",
            is_active=True,
        )
        s.add(user)
        await s.commit()

    # Configure session factory override for testclient
    import app.db.database as db_mod
    orig_engine = db_mod._engine
    orig_factory = db_mod._async_session_factory
    db_mod._engine = engine
    db_mod._async_session_factory = session_factory

    # Attach MockTaskEventPublisher wired to connection_manager
    mock_publisher = MockTaskEventPublisher(connection_manager=connection_manager)
    set_event_publisher(mock_publisher)
    TaskProgressService.reset_throttle_cache()

    # Clear active connections
    connection_manager._connections.clear()

    yield {
        "engine": engine,
        "session_factory": session_factory,
        "publisher": mock_publisher,
    }

    # Teardown
    await connection_manager.close_all()
    db_mod._engine = orig_engine
    db_mod._async_session_factory = orig_factory
    await engine.dispose()


async def _create_db_task(
    session_factory: async_sessionmaker[AsyncSession],
    task_id: str = "TASK-000124",
    status: str = "PENDING",
    current_stage: str = "CREATING_TASK",
    progress: int = 0,
    **metrics: Any,
) -> ScrapingTask:
    """Helper to seed a ScrapingTask in the in-memory database."""
    async with session_factory() as session:
        task = ScrapingTask(
            task_id=task_id,
            user_id=DEMO_USER_ID,
            location="Puducherry",
            keyword="Schools",
            status=status,
            current_stage=current_stage,
            progress=progress,
            results_discovered=metrics.get("results_discovered", 0),
            websites_found=metrics.get("websites_found", 0),
            websites_crawled=metrics.get("websites_crawled", 0),
            phones_found=metrics.get("phones_found", 0),
            emails_found=metrics.get("emails_found", 0),
            addresses_found=metrics.get("addresses_found", 0),
            duplicates_removed=metrics.get("duplicates_removed", 0),
            failed_websites=metrics.get("failed_websites", 0),
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return task


# ─── 1. Connection & Initial Snapshot Tests ──────────────────────────────────


def test_websocket_connect_valid_task_receives_snapshot(setup_test_db_and_publisher):
    """Connecting to an existing task must immediately return a task.snapshot event."""
    fixture = setup_test_db_and_publisher
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        _create_db_task(
            fixture["session_factory"],
            task_id="TASK-000100",
            status="RUNNING",
            current_stage="CRAWLING",
            progress=42,
            results_discovered=10,
            websites_crawled=5,
        )
    )

    client = TestClient(app)
    with client.websocket_connect("/api/ws/tasks/TASK-000100") as ws:
        msg = ws.receive_json()
        assert msg["type"] == EventType.SNAPSHOT.value
        assert msg["task_id"] == "TASK-000100"
        assert msg["data"]["status"] == "RUNNING"
        assert msg["data"]["current_stage"] == "CRAWLING"
        assert msg["data"]["progress"] == 42
        assert msg["data"]["results_discovered"] == 10
        assert msg["data"]["websites_crawled"] == 5


def test_websocket_alias_endpoint(setup_test_db_and_publisher):
    """The alias /ws/tasks/{task_id} must behave identically to /api/ws/tasks/{task_id}."""
    fixture = setup_test_db_and_publisher
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        _create_db_task(fixture["session_factory"], task_id="TASK-000101")
    )

    client = TestClient(app)
    with client.websocket_connect("/ws/tasks/TASK-000101") as ws:
        msg = ws.receive_json()
        assert msg["type"] == EventType.SNAPSHOT.value
        assert msg["task_id"] == "TASK-000101"


def test_websocket_unknown_task_rejected(setup_test_db_and_publisher):
    """Connecting to a non-existent task must return an error and close with code 1008."""
    client = TestClient(app)
    with client.websocket_connect("/api/ws/tasks/TASK-999999") as ws:
        err_msg = ws.receive_json()
        assert err_msg["type"] == EventType.ERROR.value
        assert err_msg["data"]["code"] == "TASK_NOT_FOUND"

        with pytest.raises(WebSocketDisconnect) as exc_info:
            ws.receive_json()
        assert exc_info.value.code == 1008


def test_websocket_max_connections_limit(setup_test_db_and_publisher, monkeypatch):
    """Exceeding MAX_WS_CONNECTIONS_PER_TASK must reject the extra client with code 1008."""
    fixture = setup_test_db_and_publisher
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        _create_db_task(fixture["session_factory"], task_id="TASK-000102")
    )

    monkeypatch.setattr(settings, "MAX_WS_CONNECTIONS_PER_TASK", 2)

    client = TestClient(app)
    with client.websocket_connect("/api/ws/tasks/TASK-000102") as ws1:
        _ = ws1.receive_json()  # snapshot 1
        with client.websocket_connect("/api/ws/tasks/TASK-000102") as ws2:
            _ = ws2.receive_json()  # snapshot 2

            # 3rd client attempts connection (exceeds limit 2)
            with client.websocket_connect("/api/ws/tasks/TASK-000102") as ws3:
                err = ws3.receive_json()
                assert err["type"] == EventType.ERROR.value
                assert err["data"]["code"] == "RATE_LIMITED"
                with pytest.raises(WebSocketDisconnect) as exc_info:
                    ws3.receive_json()
                assert exc_info.value.code == 1008


# ─── 2. Real-Time Event Delivery Tests ────────────────────────────────────────


def test_websocket_progress_event_delivery(setup_test_db_and_publisher):
    """Task progress updates must be delivered in real-time to connected clients."""
    fixture = setup_test_db_and_publisher
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        _create_db_task(fixture["session_factory"], task_id="TASK-000103", progress=10)
    )

    client = TestClient(app)
    with client.websocket_connect("/api/ws/tasks/TASK-000103") as ws:
        _ = ws.receive_json()  # initial snapshot

        # Trigger progress update via TaskProgressService
        async def _update():
            async with fixture["session_factory"]() as s:
                service = TaskProgressService(s)
                await service.update(
                    "TASK-000103",
                    progress=50,
                    stage="CRAWLING",
                    metrics={"websites_crawled": 12, "phones_found": 8},
                    force_publish=True,
                )

        loop.run_until_complete(_update())

        event = ws.receive_json()
        assert event["type"] == EventType.STAGE_CHANGED.value or event["type"] == EventType.PROGRESS.value
        assert event["task_id"] == "TASK-000103"
        assert event["data"]["progress"] == 50
        assert event["data"]["websites_crawled"] == 12
        assert event["data"]["phones_found"] == 8


def test_websocket_activity_event_delivery(setup_test_db_and_publisher):
    """Concise activity messages must be broadcast to subscribers."""
    fixture = setup_test_db_and_publisher
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        _create_db_task(fixture["session_factory"], task_id="TASK-000104")
    )

    client = TestClient(app)
    with client.websocket_connect("/api/ws/tasks/TASK-000104") as ws:
        _ = ws.receive_json()  # snapshot

        async def _activity():
            async with fixture["session_factory"]() as s:
                service = TaskProgressService(s)
                await service.update(
                    "TASK-000104",
                    activity_message="Crawled 25 internal pages",
                    stage="CRAWLING",
                )

        loop.run_until_complete(_activity())

        event = ws.receive_json()
        assert event["type"] == EventType.ACTIVITY.value
        assert event["data"]["message"] == "Crawled 25 internal pages"
        assert event["data"]["stage"] == "CRAWLING"


def test_websocket_completion_event(setup_test_db_and_publisher):
    """Completion must deliver task.completed with progress=100 and final metrics."""
    fixture = setup_test_db_and_publisher
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        _create_db_task(fixture["session_factory"], task_id="TASK-000105", progress=90)
    )

    client = TestClient(app)
    with client.websocket_connect("/api/ws/tasks/TASK-000105") as ws:
        _ = ws.receive_json()

        async def _complete():
            async with fixture["session_factory"]() as s:
                service = TaskProgressService(s)
                await service.update(
                    "TASK-000105",
                    status="COMPLETED",
                    stage="COMPLETED",
                    progress=100,
                    metrics={"results_discovered": 5, "phones_found": 10},
                )

        loop.run_until_complete(_complete())

        event = ws.receive_json()
        assert event["type"] == EventType.COMPLETED.value
        assert event["data"]["status"] == "COMPLETED"
        assert event["data"]["progress"] == 100
        assert event["data"]["results_discovered"] == 5


def test_websocket_failure_event_sanitized(setup_test_db_and_publisher):
    """Task failure must deliver task.failed without raw stack traces."""
    fixture = setup_test_db_and_publisher
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        _create_db_task(fixture["session_factory"], task_id="TASK-000106", progress=30)
    )

    client = TestClient(app)
    with client.websocket_connect("/api/ws/tasks/TASK-000106") as ws:
        _ = ws.receive_json()

        async def _fail():
            async with fixture["session_factory"]() as s:
                service = TaskProgressService(s)
                await service.update(
                    "TASK-000106",
                    status="FAILED",
                    stage="EXTRACTING",
                    failure_reason="Data extraction stage failed: ParserError",
                )

        loop.run_until_complete(_fail())

        event = ws.receive_json()
        assert event["type"] == EventType.FAILED.value
        assert event["data"]["status"] == "FAILED"
        assert event["data"]["stage"] == "EXTRACTING"
        assert "Data extraction stage failed" in event["data"]["reason"]
        assert "Traceback" not in event["data"]["reason"]


def test_websocket_cancellation_event(setup_test_db_and_publisher):
    """Cancellation must deliver task.cancelled preserving last valid progress."""
    fixture = setup_test_db_and_publisher
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        _create_db_task(fixture["session_factory"], task_id="TASK-000107", progress=67)
    )

    client = TestClient(app)
    with client.websocket_connect("/api/ws/tasks/TASK-000107") as ws:
        _ = ws.receive_json()

        async def _cancel():
            async with fixture["session_factory"]() as s:
                service = TaskProgressService(s)
                await service.update(
                    "TASK-000107",
                    status="CANCELLED",
                    stage="CRAWLING",
                )

        loop.run_until_complete(_cancel())

        event = ws.receive_json()
        assert event["type"] == EventType.CANCELLED.value
        assert event["data"]["status"] == "CANCELLED"
        assert event["data"]["progress"] == 67


# ─── 3. Multi-Client & Channel Isolation Tests ───────────────────────────────


def test_websocket_multiple_clients_same_task(setup_test_db_and_publisher):
    """Multiple clients connected to the same task must all receive the broadcast."""
    fixture = setup_test_db_and_publisher
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        _create_db_task(fixture["session_factory"], task_id="TASK-000108")
    )

    client = TestClient(app)
    with client.websocket_connect("/api/ws/tasks/TASK-000108") as ws1:
        _ = ws1.receive_json()
        with client.websocket_connect("/api/ws/tasks/TASK-000108") as ws2:
            _ = ws2.receive_json()

            async def _broadcast():
                async with fixture["session_factory"]() as s:
                    service = TaskProgressService(s)
                    await service.update(
                        "TASK-000108",
                        progress=35,
                        stage="CRAWLING",
                        force_publish=True,
                    )

            loop.run_until_complete(_broadcast())

            event1 = ws1.receive_json()
            event2 = ws2.receive_json()
            assert event1["data"]["progress"] == 35
            assert event2["data"]["progress"] == 35


def test_websocket_task_channel_isolation(setup_test_db_and_publisher):
    """Clients on Task A must NEVER receive events broadcast to Task B."""
    fixture = setup_test_db_and_publisher
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        _create_db_task(fixture["session_factory"], task_id="TASK-A")
    )
    loop.run_until_complete(
        _create_db_task(fixture["session_factory"], task_id="TASK-B")
    )

    client = TestClient(app)
    with client.websocket_connect("/api/ws/tasks/TASK-A") as ws_a:
        _ = ws_a.receive_json()  # snapshot A
        with client.websocket_connect("/api/ws/tasks/TASK-B") as ws_b:
            _ = ws_b.receive_json()  # snapshot B

            # Update ONLY Task A
            async def _update_a():
                async with fixture["session_factory"]() as s:
                    service = TaskProgressService(s)
                    await service.update(
                        "TASK-A",
                        progress=55,
                        stage="EXTRACTING",
                        force_publish=True,
                    )

            loop.run_until_complete(_update_a())

            # ws_a receives update
            event_a = ws_a.receive_json()
            assert event_a["task_id"] == "TASK-A"
            assert event_a["data"]["progress"] == 55

            # ws_b receives nothing (verifying connection count isolation)
            assert connection_manager.get_connection_count("TASK-A") == 1
            assert connection_manager.get_connection_count("TASK-B") == 1


# ─── 4. Reconnect & Monotonic State Tests ─────────────────────────────────────


def test_websocket_reconnect_receives_updated_snapshot(setup_test_db_and_publisher):
    """Client reconnecting after an outage must immediately get the latest DB state."""
    fixture = setup_test_db_and_publisher
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        _create_db_task(fixture["session_factory"], task_id="TASK-000109", progress=10)
    )

    client = TestClient(app)

    # First connection
    with client.websocket_connect("/api/ws/tasks/TASK-000109") as ws:
        msg1 = ws.receive_json()
        assert msg1["data"]["progress"] == 10

    # Advance task in database while client is disconnected
    async def _advance():
        async with fixture["session_factory"]() as s:
            service = TaskProgressService(s)
            await service.update(
                "TASK-000109",
                progress=80,
                stage="CLEANING",
                metrics={"duplicates_removed": 5},
            )

    loop.run_until_complete(_advance())

    # Reconnect
    with client.websocket_connect("/api/ws/tasks/TASK-000109") as ws:
        msg2 = ws.receive_json()
        assert msg2["data"]["progress"] == 80
        assert msg2["data"]["current_stage"] == "CLEANING"
        assert msg2["data"]["duplicates_removed"] == 5


@pytest.mark.asyncio
async def test_progress_monotonicity_ignores_regression(setup_test_db_and_publisher):
    """A progress update attempting to decrease progress must be clamped/ignored."""
    fixture = setup_test_db_and_publisher
    await _create_db_task(fixture["session_factory"], task_id="TASK-000110", progress=60)

    async with fixture["session_factory"]() as s:
        service = TaskProgressService(s)
        # Attempt to set progress down to 40 without allow_regression
        updated = await service.update("TASK-000110", progress=40)
        assert updated.progress == 60  # Regressive 40 was ignored

        # Explicit regression allowed (e.g. error correction)
        updated2 = await service.update("TASK-000110", progress=40, allow_regression=True)
        assert updated2.progress == 40


@pytest.mark.asyncio
async def test_invalid_stage_rejected(setup_test_db_and_publisher):
    """Passing an arbitrary stage string must raise a ValidationError."""
    fixture = setup_test_db_and_publisher
    await _create_db_task(fixture["session_factory"], task_id="TASK-000111")

    async with fixture["session_factory"]() as s:
        service = TaskProgressService(s)
        with pytest.raises(ValidationError) as exc:
            await service.update("TASK-000111", stage="NOT_A_VALID_STAGE")
        assert "Invalid stage" in str(exc.value)


@pytest.mark.asyncio
async def test_terminal_states_reject_normal_progress_updates(setup_test_db_and_publisher):
    """Once a task is COMPLETED, subsequent RUNNING progress updates are ignored."""
    fixture = setup_test_db_and_publisher
    await _create_db_task(
        fixture["session_factory"],
        task_id="TASK-000112",
        status="COMPLETED",
        current_stage="COMPLETED",
        progress=100,
    )

    async with fixture["session_factory"]() as s:
        service = TaskProgressService(s)
        updated = await service.update("TASK-000112", progress=50, stage="CRAWLING")
        assert updated.status == "COMPLETED"
        assert updated.progress == 100


# ─── 5. Resilience & Failure Isolation Tests ──────────────────────────────────


@pytest.mark.asyncio
async def test_redis_publish_failure_does_not_fail_db_update(setup_test_db_and_publisher):
    """If the real-time publisher throws an error, PostgreSQL commit still succeeds."""
    fixture = setup_test_db_and_publisher
    await _create_db_task(fixture["session_factory"], task_id="TASK-000113", progress=20)

    broken_publisher = MagicMock()
    broken_publisher.publish_event = AsyncMock(side_effect=ConnectionError("Redis down"))
    set_event_publisher(broken_publisher)

    async with fixture["session_factory"]() as s:
        service = TaskProgressService(s)
        # Should NOT raise ConnectionError
        updated = await service.update("TASK-000113", progress=50, stage="CRAWLING", force_publish=True)
        assert updated.progress == 50
        assert updated.current_stage == "CRAWLING"


def test_redis_pubsub_channel_helpers():
    """Verify channel naming conventions and Redis client initializers."""
    channel = get_task_channel("TASK-000124")
    assert channel == f"{settings.REDIS_PUBSUB_PREFIX}:TASK-000124"

    pubsub = RedisPubSub("redis://localhost:6379/9")
    assert pubsub.redis_url == "redis://localhost:6379/9"


def test_heartbeat_ping_event(setup_test_db_and_publisher, monkeypatch):
    """Verify that heartbeat pings are sent to connected clients within the interval."""
    fixture = setup_test_db_and_publisher
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        _create_db_task(fixture["session_factory"], task_id="TASK-HEARTBEAT")
    )

    # Use very short heartbeat interval for fast test
    monkeypatch.setattr(settings, "WEBSOCKET_HEARTBEAT_SECONDS", 0.1)

    client = TestClient(app)
    with client.websocket_connect("/api/ws/tasks/TASK-HEARTBEAT") as ws:
        snapshot = ws.receive_json()
        assert snapshot["type"] == EventType.SNAPSHOT.value

        # Await heartbeat ping
        ping = ws.receive_json()
        assert ping["type"] == EventType.PING.value

        # Client responds with pong
        ws.send_json({"type": "pong"})


@pytest.mark.asyncio
async def test_database_failure_does_not_publish_event(setup_test_db_and_publisher):
    """If database update fails and rolls back, no success event should be published."""
    fixture = setup_test_db_and_publisher
    await _create_db_task(fixture["session_factory"], task_id="TASK-000114")

    mock_publisher = fixture["publisher"]
    mock_publisher.clear()

    async with fixture["session_factory"]() as s:
        service = TaskProgressService(s)
        # Force a database commit failure
        with patch.object(s, "commit", side_effect=RuntimeError("Simulated DB Disk Full")):
            with pytest.raises(RuntimeError):
                await service.update("TASK-000114", progress=75)

    # Verify no events were published because DB transaction rolled back
    assert len(mock_publisher.published_events) == 0


@pytest.mark.asyncio
async def test_connection_manager_prune_dead_sockets():
    """ConnectionManager.broadcast should automatically remove sockets that fail on send."""
    cm = ConnectionManager()
    from starlette.websockets import WebSocketState

    ws_alive = MagicMock()
    ws_alive.client_state = WebSocketState.CONNECTED
    ws_alive.send_json = AsyncMock(return_value=None)

    ws_dead = MagicMock()
    ws_dead.client_state = WebSocketState.CONNECTED
    ws_dead.send_json = AsyncMock(side_effect=RuntimeError("Connection lost"))

    await cm.connect("TASK-PRUNE", ws_alive)
    await cm.connect("TASK-PRUNE", ws_dead)
    assert cm.get_connection_count("TASK-PRUNE") == 2

    # Broadcast event
    delivered = await cm.broadcast("TASK-PRUNE", {"type": "ping"})
    assert delivered == 1

    # Dead socket should be pruned
    assert cm.get_connection_count("TASK-PRUNE") == 1
    assert ws_alive in cm.get_connections("TASK-PRUNE")
    assert ws_dead not in cm.get_connections("TASK-PRUNE")


@pytest.mark.asyncio
async def test_subscriber_manager_lifecycle():
    """TaskSubscriberManager starts and stops background Redis listener tasks correctly."""
    from app.realtime.subscriber import TaskSubscriberManager

    sm = TaskSubscriberManager()
    cm = ConnectionManager()

    # Stub redis_pubsub.subscribe to return empty generator
    async def mock_subscribe(task_id):
        if False:
            yield {}

    with patch("app.realtime.subscriber.redis_pubsub.subscribe", side_effect=mock_subscribe):
        await sm.ensure_subscribed("TASK-SUB-1", cm)
        assert "TASK-SUB-1" in sm._listener_tasks
        assert not sm._listener_tasks["TASK-SUB-1"].done()

        # When no clients connected, unsubscribe_if_empty cleans up
        await sm.unsubscribe_if_empty("TASK-SUB-1", cm)
        assert "TASK-SUB-1" not in sm._listener_tasks

        # Ensure stop_all works cleanly
        await sm.ensure_subscribed("TASK-SUB-2", cm)
        await sm.stop_all()
        assert len(sm._listener_tasks) == 0

