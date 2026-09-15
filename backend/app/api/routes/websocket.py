"""
app/api/routes/websocket.py

FastAPI WebSocket endpoint for task-specific real-time progress updates.
Endpoint: WS /api/ws/tasks/{task_id}

Connection lifecycle:
  1. Validate that the task exists in PostgreSQL.
  2. Enforce MAX_WS_CONNECTIONS_PER_TASK limit.
  3. Accept WebSocket connection and register with ConnectionManager.
  4. Ensure Redis Pub/Sub subscriber is active for this task.
  5. Fetch authoritative database state and send initial 'task.snapshot' event.
  6. Run periodic heartbeat ping task.
  7. Handle client messages (e.g. 'pong') until disconnect.
  8. Clean up connection and subscriber on disconnect.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from fastapi import APIRouter
from starlette.websockets import WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import decode_access_token
from app.db.database import create_engine_and_factory, get_session_factory
from app.realtime.connection_manager import connection_manager
from app.realtime.events import (
    build_error_event,
    build_ping_event,
    build_snapshot_event,
)
from app.realtime.subscriber import subscriber_manager
from app.repositories.task_repository import TaskRepository

logger = get_logger(__name__)

router = APIRouter()


async def _handle_task_websocket(websocket: WebSocket, task_id: str) -> None:
    """Internal task-specific WebSocket lifecycle handler."""
    # ── 0. Authenticate WebSocket Connection ─────────────────────────────────
    token: str | None = None
    auth_header = websocket.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip()
    if not token:
        token = websocket.cookies.get(settings.AUTH_COOKIE_NAME)
    if not token:
        token = websocket.query_params.get("token")

    current_user_id: uuid.UUID | None = None
    if token:
        try:
            payload = decode_access_token(token)
            current_user_id = uuid.UUID(payload.sub)
        except Exception:
            logger.warning("WebSocket rejected: invalid token for task '%s'.", task_id)
            await websocket.accept()
            await websocket.send_json(
                build_error_event(
                    task_id,
                    message="Invalid or expired authentication token.",
                    code="UNAUTHENTICATED",
                )
            )
            await websocket.close(code=1008, reason="Unauthorized")
            return
    elif settings.ENVIRONMENT in ("development", "test"):
        # Development / test fallback for legacy test client backward compatibility
        demo_user_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        current_user_id = demo_user_id
    else:
        logger.warning("WebSocket rejected: no token provided for task '%s'.", task_id)
        await websocket.accept()
        await websocket.send_json(
            build_error_event(
                task_id,
                message="Authentication required.",
                code="UNAUTHENTICATED",
            )
        )
        await websocket.close(code=1008, reason="Unauthorized")
        return

    # ── 1. Validate Task Existence & Ownership ───────────────────────────────
    try:
        factory = get_session_factory()
    except RuntimeError:
        create_engine_and_factory()
        factory = get_session_factory()

    async with factory() as session:
        repo = TaskRepository(session)
        task = await repo.get_by_task_id(task_id)

    if not task or (current_user_id is not None and task.user_id != current_user_id):
        logger.warning("WebSocket rejected: task '%s' not found or unowned.", task_id)
        await websocket.accept()
        await websocket.send_json(
            build_error_event(
                task_id,
                message=f"Scraping task '{task_id}' not found.",
                code="TASK_NOT_FOUND",
            )
        )
        await websocket.close(code=1008, reason="Task not found")
        return

    # ── 2. Enforce Connection Limits ─────────────────────────────────────────
    current_count = connection_manager.get_connection_count(task_id)
    if current_count >= settings.MAX_WS_CONNECTIONS_PER_TASK:
        logger.warning(
            "WebSocket rejected: task '%s' exceeded max connection limit (%d/%d).",
            task_id,
            current_count,
            settings.MAX_WS_CONNECTIONS_PER_TASK,
        )
        await websocket.accept()
        await websocket.send_json(
            build_error_event(
                task_id,
                message=f"Connection limit reached for task '{task_id}'.",
                code="RATE_LIMITED",
            )
        )
        await websocket.close(code=1008, reason="Connection limit reached")
        return

    # ── 3. Accept & Register ─────────────────────────────────────────────────
    await websocket.accept()
    await connection_manager.connect(task_id, websocket)

    # ── 4. Ensure Redis Pub/Sub Subscription is Active ───────────────────────
    await subscriber_manager.ensure_subscribed(task_id, connection_manager)

    # ── 5. Send Authoritative PostgreSQL Initial Snapshot ────────────────────
    snapshot = build_snapshot_event(task)
    await websocket.send_json(snapshot)

    # ── 6. Heartbeat Loop Task ───────────────────────────────────────────────
    heartbeat_task: asyncio.Task[None] | None = None

    async def _heartbeat() -> None:
        try:
            while True:
                await asyncio.sleep(settings.WEBSOCKET_HEARTBEAT_SECONDS)
                await websocket.send_json(build_ping_event())
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.debug("Heartbeat exception on task %s: %s", task_id, exc)

    heartbeat_task = asyncio.create_task(_heartbeat())

    # ── 7. Client Message Loop ───────────────────────────────────────────────
    try:
        while True:
            # Await client responses or pongs
            data = await websocket.receive_json()
            if isinstance(data, dict) and data.get("type") == "pong":
                logger.debug("Heartbeat pong received from client for task %s", task_id)
    except WebSocketDisconnect:
        logger.debug("Client disconnected normally from task %s", task_id)
    except Exception as exc:
        logger.debug("WebSocket connection terminated for task %s: %s", task_id, exc)
    finally:
        # ── 8. Cleanup on Disconnect ─────────────────────────────────────────
        if heartbeat_task and not heartbeat_task.done():
            heartbeat_task.cancel()
        await connection_manager.disconnect(task_id, websocket)
        await subscriber_manager.unsubscribe_if_empty(task_id, connection_manager)


@router.websocket("/api/ws/tasks/{task_id}")
async def task_websocket_endpoint(websocket: WebSocket, task_id: str) -> None:
    """Primary WebSocket endpoint: /api/ws/tasks/{task_id}."""
    await _handle_task_websocket(websocket, task_id)


@router.websocket("/ws/tasks/{task_id}")
async def task_websocket_endpoint_alias(websocket: WebSocket, task_id: str) -> None:
    """Alias WebSocket endpoint: /ws/tasks/{task_id}."""
    await _handle_task_websocket(websocket, task_id)
