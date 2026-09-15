"""
app/realtime/events.py

Structured real-time event schemas, event type constants, and helper factory functions.
Used by the WebSocket endpoint, Redis Pub/Sub, and TaskProgressService.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.models.scraping_task import ScrapingTask


class EventType(str, Enum):
    """Supported real-time WebSocket event types."""

    SNAPSHOT = "task.snapshot"
    QUEUED = "task.queued"
    STARTED = "task.started"
    PROGRESS = "task.progress"
    STAGE_CHANGED = "task.stage_changed"
    ACTIVITY = "task.activity"
    COMPLETED = "task.completed"
    FAILED = "task.failed"
    CANCELLED = "task.cancelled"
    ERROR = "task.error"
    PING = "ping"
    PONG = "pong"


class TaskEvent(BaseModel):
    """Generic envelope for WebSocket and Redis Pub/Sub task events."""

    type: str = Field(..., description="Event type identifier, e.g. task.progress")
    task_id: str = Field(..., description="Human-readable Task ID (e.g. TASK-000124)")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    data: dict[str, Any] = Field(default_factory=dict, description="Event payload data")


def _current_timestamp() -> str:
    """Return the current UTC timestamp formatted as ISO 8601 with Z suffix."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _format_datetime_utc(dt: datetime | None) -> str | None:
    """Safely format naive or aware datetime to ISO 8601 UTC string with Z suffix."""
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def extract_task_metrics(task: ScrapingTask) -> dict[str, int]:
    """Extract populated metrics from a ScrapingTask instance."""
    metrics: dict[str, int] = {
        "results_discovered": task.results_discovered,
        "websites_found": task.websites_found,
        "websites_crawled": task.websites_crawled,
        "phones_found": task.phones_found,
        "emails_found": task.emails_found,
        "addresses_found": task.addresses_found,
        "duplicates_removed": task.duplicates_removed,
        "failed_websites": task.failed_websites,
    }
    if task.verified_count or task.high_confidence_count or task.medium_confidence_count or task.low_confidence_count:
        metrics.update(
            {
                "verified_count": task.verified_count,
                "high_confidence_count": task.high_confidence_count,
                "medium_confidence_count": task.medium_confidence_count,
                "low_confidence_count": task.low_confidence_count,
            }
        )
    return metrics


def build_snapshot_event(task: ScrapingTask) -> dict[str, Any]:
    """Build the initial task snapshot event directly from PostgreSQL state."""
    data: dict[str, Any] = {
        "status": task.status,
        "current_stage": task.current_stage,
        "progress": task.progress,
        "location": task.location,
        "keyword": task.keyword,
        "created_at": _format_datetime_utc(task.created_at),
        "started_at": _format_datetime_utc(task.started_at),
        "completed_at": _format_datetime_utc(task.completed_at),
        "failure_reason": task.failure_reason,
        **extract_task_metrics(task),
    }
    return {
        "type": EventType.SNAPSHOT.value,
        "task_id": task.task_id,
        "timestamp": _current_timestamp(),
        "data": data,
    }


def build_queued_event(task_id: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build task.queued event."""
    return {
        "type": EventType.QUEUED.value,
        "task_id": task_id,
        "timestamp": _current_timestamp(),
        "data": data or {"status": "PENDING", "current_stage": "CREATING_TASK", "progress": 0},
    }


def build_started_event(
    task_id: str,
    *,
    stage: str = "DISCOVERING",
    progress: int = 10,
    metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build task.started event."""
    payload: dict[str, Any] = {
        "status": "RUNNING",
        "current_stage": stage,
        "progress": progress,
    }
    if metrics:
        payload.update(metrics)
    return {
        "type": EventType.STARTED.value,
        "task_id": task_id,
        "timestamp": _current_timestamp(),
        "data": payload,
    }


def build_progress_event(
    task_id: str,
    *,
    progress: int,
    stage: str,
    status: str = "RUNNING",
    metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build task.progress event."""
    payload: dict[str, Any] = {
        "status": status,
        "current_stage": stage,
        "progress": progress,
    }
    if metrics:
        payload.update(metrics)
    return {
        "type": EventType.PROGRESS.value,
        "task_id": task_id,
        "timestamp": _current_timestamp(),
        "data": payload,
    }


def build_stage_changed_event(
    task_id: str,
    *,
    stage: str,
    progress: int,
    status: str = "RUNNING",
    metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build task.stage_changed event."""
    payload: dict[str, Any] = {
        "status": status,
        "current_stage": stage,
        "progress": progress,
    }
    if metrics:
        payload.update(metrics)
    return {
        "type": EventType.STAGE_CHANGED.value,
        "task_id": task_id,
        "timestamp": _current_timestamp(),
        "data": payload,
    }


def build_activity_event(
    task_id: str,
    *,
    message: str,
    stage: str,
) -> dict[str, Any]:
    """Build task.activity event for concise progress milestones or non-fatal alerts."""
    return {
        "type": EventType.ACTIVITY.value,
        "task_id": task_id,
        "timestamp": _current_timestamp(),
        "data": {
            "message": message,
            "stage": stage,
        },
    }


def build_completed_event(
    task_id: str,
    *,
    metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build task.completed event."""
    payload: dict[str, Any] = {
        "status": "COMPLETED",
        "current_stage": "COMPLETED",
        "progress": 100,
    }
    if metrics:
        payload.update(metrics)
    return {
        "type": EventType.COMPLETED.value,
        "task_id": task_id,
        "timestamp": _current_timestamp(),
        "data": payload,
    }


def build_failed_event(
    task_id: str,
    *,
    stage: str,
    reason: str,
) -> dict[str, Any]:
    """Build task.failed event."""
    return {
        "type": EventType.FAILED.value,
        "task_id": task_id,
        "timestamp": _current_timestamp(),
        "data": {
            "status": "FAILED",
            "stage": stage,
            "reason": reason,
        },
    }


def build_cancelled_event(
    task_id: str,
    *,
    stage: str,
    progress: int,
) -> dict[str, Any]:
    """Build task.cancelled event preserving last valid progress."""
    return {
        "type": EventType.CANCELLED.value,
        "task_id": task_id,
        "timestamp": _current_timestamp(),
        "data": {
            "status": "CANCELLED",
            "current_stage": stage,
            "progress": progress,
        },
    }


def build_error_event(task_id: str, *, message: str, code: str = "TASK_ERROR") -> dict[str, Any]:
    """Build task.error event."""
    return {
        "type": EventType.ERROR.value,
        "task_id": task_id,
        "timestamp": _current_timestamp(),
        "data": {
            "code": code,
            "message": message,
        },
    }


def build_ping_event() -> dict[str, Any]:
    """Build heartbeat ping event."""
    return {"type": EventType.PING.value}


def build_pong_event() -> dict[str, Any]:
    """Build heartbeat pong response."""
    return {"type": EventType.PONG.value}
