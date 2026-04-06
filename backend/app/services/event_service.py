"""
Event publishing service using Dapr Pub/Sub abstraction (Phase 2.6).

Constitution XXVIII: Dapr Pub/Sub instead of direct Kafka clients
Ensures vendor abstraction and flexible pub/sub implementation.

This service handles:
- Publishing task events to Kafka topics (via Dapr)
- Async/non-blocking event publishing
- Event serialization and validation
- Topic routing (task-events, reminders, task-updates)
"""
import asyncio
import logging
from typing import Optional, Literal

from app.schemas.event import TaskEvent, TaskEventData, ReminderEvent
from app.models.task import Task

logger = logging.getLogger(__name__)

# Dapr pub/sub component name (set via environment or Dapr config)
DAPR_PUBSUB_NAME = "kafka"  # Will be defined in Dapr configuration

# Kafka topic definitions (via Dapr abstraction)
TOPICS = {
    "task_events": "task-events",        # TaskCreated, Updated, Completed, Deleted
    "reminders": "reminders",            # ReminderTriggered (Phase 2.7)
    "task_updates": "task-updates"       # Real-time updates (Phase 7+)
}


class EventPublisher:
    """
    Publish task events to Kafka via Dapr Pub/Sub.

    Phase 2.6 Extension (Spec-006):
    - Asynchronous event publishing (non-blocking)
    - Uses Dapr sidecar for Kafka abstraction
    - Automatic retry/error handling via Dapr
    - Event versioning and schema validation

    Constitution XXVIII: All pub/sub via Dapr (not direct Kafka)
    """

    @staticmethod
    async def publish_task_event(
        task: Task,
        event_type: Literal[
            "TaskCreated",
            "TaskUpdated",
            "TaskCompleted",
            "TaskDeleted"
        ]
    ) -> bool:
        """
        Publish a task event to task-events topic.

        Phase 2.6: Asynchronous, non-blocking event publishing
        Events are published AFTER database commit (eventual consistency).

        Args:
            task: Task model instance
            event_type: Event type (Create/Update/Complete/Delete)

        Returns:
            True if published successfully, False if failed
        """
        try:
            # Create event payload
            task_data = TaskEventData(
                id=task.id,
                user_id=task.user_id,
                title=task.title,
                description=task.description,
                priority=task.priority,
                tags=_parse_tags(task.tags),
                due_date=task.due_date,
                reminder_time=task.reminder_time,
                is_complete=task.is_complete,
                is_recurring=task.is_recurring,
                recurring_pattern=task.recurring_pattern,
                created_at=task.created_at,
                updated_at=task.updated_at
            )

            event = TaskEvent(
                event_type=event_type,
                user_id=task.user_id,
                task_id=task.id,
                data=task_data
            )

            # Convert to dict for Dapr pub/sub
            event_payload = event.dict(by_alias=False)

            # Publish asynchronously (fire-and-forget)
            # In production, this should use Dapr sidecar HTTP API
            asyncio.create_task(
                _publish_to_dapr(
                    pubsub_name=DAPR_PUBSUB_NAME,
                    topic=TOPICS["task_events"],
                    data=event_payload
                )
            )

            logger.info(
                f"Event published (async): {event_type} task {task.id} "
                f"for user {task.user_id} (event_id: {event.event_id})"
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to publish event {event_type} for task {task.id}: {e}",
                exc_info=True
            )
            # Don't raise - event publishing failure should not block API
            return False

    @staticmethod
    async def publish_reminder_event(
        user_id: str,
        task_id: int,
        task_title: str,
        reminder_time: str
    ) -> bool:
        """
        Publish a reminder event to reminders topic.

        Phase 2.7+: Consumed by notification service
        Triggers in-app, email, push, or SMS notifications.

        Args:
            user_id: Authenticated user ID
            task_id: Task ID
            task_title: Task title (for notification)
            reminder_time: ISO-8601 reminder time

        Returns:
            True if published successfully, False if failed
        """
        try:
            from datetime import datetime

            event = ReminderEvent(
                user_id=user_id,
                task_id=task_id,
                task_title=task_title,
                reminder_time=datetime.fromisoformat(
                    reminder_time.replace("Z", "+00:00")
                )
            )

            event_payload = event.dict(by_alias=False)

            asyncio.create_task(
                _publish_to_dapr(
                    pubsub_name=DAPR_PUBSUB_NAME,
                    topic=TOPICS["reminders"],
                    data=event_payload
                )
            )

            logger.info(
                f"Reminder event published (async): task {task_id} "
                f"for user {user_id} (event_id: {event.event_id})"
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to publish reminder event for task {task_id}: {e}",
                exc_info=True
            )
            return False


async def _publish_to_dapr(
    pubsub_name: str,
    topic: str,
    data: dict
) -> bool:
    """
    Publish to Dapr pub/sub sidecar.

    Phase 2.6: Non-blocking async HTTP POST to Dapr sidecar.
    Dapr handles Kafka publishing, retries, and delivery guarantees.

    In production with Dapr:
    POST http://localhost:3500/v1.0/publish/{pubsub_name}/{topic}
    Body: JSON event payload

    For MVP (without Dapr sidecar):
    Logs to console (can be replaced with direct Kafka client).

    Args:
        pubsub_name: Dapr pub/sub component name
        topic: Kafka topic name
        data: Event payload dict

    Returns:
        True if published, False if failed
    """
    try:
        import httpx
        import os

        # Get Dapr HTTP port from environment or default to 3500
        dapr_http_port = os.getenv("DAPR_HTTP_PORT", "3500")
        dapr_url = f"http://localhost:{dapr_http_port}/v1.0/publish/{pubsub_name}/{topic}"

        logger.info(
            f"[Dapr Pub/Sub] Publishing {data.get('event_type', 'unknown')} "
            f"to {pubsub_name}/{topic} "
            f"(event_id: {data.get('event_id', 'unknown')})"
        )

        # Publish to Dapr sidecar (production mode)
        async with httpx.AsyncClient() as client:
            response = await client.post(
                dapr_url,
                json=data,
                timeout=5.0
            )

            if response.status_code == 204:
                logger.info(
                    f"Event published successfully: {data.get('event_type')} "
                    f"(event_id: {data.get('event_id')})"
                )
                return True
            else:
                logger.warning(
                    f"Dapr returned {response.status_code}: {response.text}"
                )
                return False

    except Exception as e:
        logger.error(
            f"Failed to publish to Dapr {pubsub_name}/{topic}: {e}",
            exc_info=True
        )
        return False


def _parse_tags(tags_json: Optional[str]) -> Optional[list[str]]:
    """
    Parse tags from JSON string to list.

    Args:
        tags_json: JSON string like '["tag1", "tag2"]'

    Returns:
        List of tags or None
    """
    if not tags_json:
        return None

    try:
        import json
        tags = json.loads(tags_json)
        return tags if isinstance(tags, list) else None
    except Exception:
        return None


# Singleton publisher instance
publisher = EventPublisher()


async def publish_task_created(task: Task) -> bool:
    """Publish TaskCreated event."""
    return await publisher.publish_task_event(task, "TaskCreated")


async def publish_task_updated(task: Task) -> bool:
    """Publish TaskUpdated event."""
    return await publisher.publish_task_event(task, "TaskUpdated")


async def publish_task_completed(task: Task) -> bool:
    """Publish TaskCompleted event."""
    return await publisher.publish_task_event(task, "TaskCompleted")


async def publish_task_deleted(task: Task) -> bool:
    """Publish TaskDeleted event."""
    return await publisher.publish_task_event(task, "TaskDeleted")
