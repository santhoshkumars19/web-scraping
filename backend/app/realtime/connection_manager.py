"""
app/realtime/connection_manager.py

WebSocket connection manager for tracking active client connections per task.
Handles connection registration, graceful disconnection, dead socket pruning,
and concurrent event broadcasting to task subscribers.
"""

from __future__ import annotations

import asyncio
from typing import Any
from starlette.websockets import WebSocket, WebSocketState

from app.core.logging import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections mapped per human-readable task_id."""

    def __init__(self) -> None:
        # task_id -> set of active WebSocket instances
        self._connections: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, task_id: str, websocket: WebSocket) -> None:
        """Register an accepted WebSocket connection for a specific task."""
        async with self._lock:
            if task_id not in self._connections:
                self._connections[task_id] = set()
            self._connections[task_id].add(websocket)

        logger.info(
            "WEBSOCKET_CONNECTED: client connected to task %s (total clients for task: %d)",
            task_id,
            self.get_connection_count(task_id),
        )

    async def disconnect(self, task_id: str, websocket: WebSocket) -> None:
        """Remove a WebSocket connection from the task's active subscriber set."""
        async with self._lock:
            if task_id in self._connections:
                self._connections[task_id].discard(websocket)
                if not self._connections[task_id]:
                    del self._connections[task_id]

        logger.info(
            "WEBSOCKET_DISCONNECTED: client disconnected from task %s (remaining clients for task: %d)",
            task_id,
            self.get_connection_count(task_id),
        )

    def get_connections(self, task_id: str) -> set[WebSocket]:
        """Return a copy of the active WebSocket set for a task."""
        return set(self._connections.get(task_id, set()))

    def get_connection_count(self, task_id: str) -> int:
        """Return the number of connected clients for a given task."""
        return len(self._connections.get(task_id, set()))

    async def send_personal(self, websocket: WebSocket, event: dict[str, Any]) -> bool:
        """Send a JSON event to a specific client. Returns True if successful."""
        if websocket.client_state != WebSocketState.CONNECTED:
            return False
        try:
            await websocket.send_json(event)
            return True
        except Exception as exc:
            logger.debug("Failed to send personal message to websocket: %s", exc)
            return False

    async def broadcast(self, task_id: str, event: dict[str, Any]) -> int:
        """Broadcast an event to all connected clients for a specific task.

        Dead or closed connections are caught and pruned safely.
        Returns the count of successfully delivered messages.
        """
        connections = self.get_connections(task_id)
        if not connections:
            return 0

        dead_sockets: list[WebSocket] = []
        success_count = 0

        async def _send(ws: WebSocket) -> bool:
            if ws.client_state != WebSocketState.CONNECTED:
                dead_sockets.append(ws)
                return False
            try:
                await ws.send_json(event)
                return True
            except Exception as exc:
                logger.debug("Broadcast send failed for a client on task %s: %s", task_id, exc)
                dead_sockets.append(ws)
                return False

        results = await asyncio.gather(*[_send(ws) for ws in connections], return_exceptions=True)
        for res in results:
            if res is True:
                success_count += 1

        # Prune any sockets that encountered send failures
        if dead_sockets:
            async with self._lock:
                for dead_ws in dead_sockets:
                    if task_id in self._connections:
                        self._connections[task_id].discard(dead_ws)
                if task_id in self._connections and not self._connections[task_id]:
                    del self._connections[task_id]

        if success_count > 0:
            logger.debug(
                "REALTIME_EVENT_DELIVERED: event '%s' delivered to %d clients on task %s",
                event.get("type"),
                success_count,
                task_id,
            )

        return success_count

    async def close_all(self, code: int = 1001, reason: str = "Server shutdown") -> None:
        """Gracefully close all open WebSocket connections across all tasks."""
        async with self._lock:
            all_sockets: list[WebSocket] = [
                ws for sockets in self._connections.values() for ws in sockets
            ]
            self._connections.clear()

        for ws in all_sockets:
            try:
                if ws.client_state == WebSocketState.CONNECTED:
                    await ws.close(code=code, reason=reason)
            except Exception as exc:
                logger.debug("Error closing websocket during close_all: %s", exc)


# Module-level singleton instance
connection_manager = ConnectionManager()
