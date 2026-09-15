"""
app/realtime/__init__.py

Package exports for the LeadScout real-time notification subsystem.
"""

from app.realtime.connection_manager import ConnectionManager, connection_manager
from app.realtime.events import (
    EventType,
    TaskEvent,
    build_activity_event,
    build_cancelled_event,
    build_completed_event,
    build_error_event,
    build_failed_event,
    build_ping_event,
    build_pong_event,
    build_progress_event,
    build_queued_event,
    build_snapshot_event,
    build_stage_changed_event,
    build_started_event,
    extract_task_metrics,
)
from app.realtime.publisher import (
    MockTaskEventPublisher,
    RedisTaskEventPublisher,
    TaskEventPublisher,
    get_event_publisher,
    set_event_publisher,
)
from app.realtime.redis_pubsub import RedisPubSub, get_task_channel, redis_pubsub
from app.realtime.subscriber import TaskSubscriberManager, subscriber_manager

__all__ = [
    "ConnectionManager",
    "connection_manager",
    "EventType",
    "TaskEvent",
    "build_activity_event",
    "build_cancelled_event",
    "build_completed_event",
    "build_error_event",
    "build_failed_event",
    "build_ping_event",
    "build_pong_event",
    "build_progress_event",
    "build_queued_event",
    "build_snapshot_event",
    "build_stage_changed_event",
    "build_started_event",
    "extract_task_metrics",
    "TaskEventPublisher",
    "RedisTaskEventPublisher",
    "MockTaskEventPublisher",
    "get_event_publisher",
    "set_event_publisher",
    "RedisPubSub",
    "get_task_channel",
    "redis_pubsub",
    "TaskSubscriberManager",
    "subscriber_manager",
]
