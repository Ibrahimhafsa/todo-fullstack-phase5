"""Event schemas for Dapr Pub/Sub publishing (Phase 2.6)."""
from datetime import datetime
from typing import Optional, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class TaskEventData(BaseModel):
    """
    Task data payload for events.

    Phase 5 Extension (Spec-006):
    Contains complete task state at event time.
    """
    id: int
    user_id: str
    title: str
    description: Optional[str] = None
    priority: str = "Medium"
    tags: Optional[list[str]] = None
    due_date: Optional[datetime] = None
    reminder_time: Optional[datetime] = None
    is_complete: bool = False
    is_recurring: bool = False
    recurring_pattern: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TaskEvent(BaseModel):
    """
    Task event for Dapr Pub/Sub (via Kafka topics).

    Phase 5 Extension (Spec-006):
    Event-driven architecture event published to Kafka topics:
    - task-events: TaskCreated, TaskUpdated, TaskCompleted, TaskDeleted
    - reminders: Reminder scheduling (Phase 2.7)
    - task-updates: Real-time updates (Phase 7+)

    Constitution XXX: Message versioning with version field
    """
    event_type: Literal[
        "TaskCreated",
        "TaskUpdated",
        "TaskCompleted",
        "TaskDeleted"
    ] = Field(
        description="Event type: Create/Update/Complete/Delete"
    )
    event_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique event identifier (UUID)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Event timestamp (ISO-8601 UTC)"
    )
    version: str = Field(
        default="1.0",
        description="Event schema version (Constitution XXX)"
    )
    user_id: str = Field(
        description="Authenticated user ID from JWT (Constitution VII)"
    )
    task_id: int = Field(
        description="Task ID from database"
    )
    data: TaskEventData = Field(
        description="Complete task state at event time"
    )

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "event_type": "TaskCreated",
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2026-03-15T03:00:00Z",
                "version": "1.0",
                "user_id": "user123",
                "task_id": 42,
                "data": {
                    "id": 42,
                    "user_id": "user123",
                    "title": "Daily standup",
                    "description": "Team meeting",
                    "priority": "High",
                    "tags": ["meeting", "sync"],
                    "due_date": "2026-03-20T10:00:00Z",
                    "reminder_time": "2026-03-20T09:55:00Z",
                    "is_complete": False,
                    "is_recurring": True,
                    "recurring_pattern": "Daily",
                    "created_at": "2026-03-15T03:00:00Z",
                    "updated_at": "2026-03-15T03:00:00Z"
                }
            }
        }

    def dict(self, **kwargs):
        """Override dict to include all required fields."""
        d = super().dict(**kwargs)
        # Ensure nested data is properly serialized
        if isinstance(self.data, dict):
            d["data"] = self.data
        else:
            d["data"] = self.data.dict(**kwargs)
        return d

    def json(self, **kwargs):
        """Override json to ensure proper serialization."""
        import json as json_lib
        return json_lib.dumps(self.dict(), default=str)


class ReminderEvent(BaseModel):
    """
    Reminder event for Dapr Pub/Sub (via reminders topic).

    Phase 2.7+: Published when reminder time arrives.
    Consumed by notification service.
    """
    event_type: Literal["ReminderTriggered"] = "ReminderTriggered"
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0"
    user_id: str
    task_id: int
    task_title: str
    reminder_time: datetime

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "event_type": "ReminderTriggered",
                "event_id": "550e8400-e29b-41d4-a716-446655440001",
                "timestamp": "2026-03-20T09:55:00Z",
                "version": "1.0",
                "user_id": "user123",
                "task_id": 42,
                "task_title": "Daily standup",
                "reminder_time": "2026-03-20T09:55:00Z"
            }
        }


class EventPublishRequest(BaseModel):
    """Internal request to publish an event (for service layer)."""
    event_type: Literal[
        "TaskCreated",
        "TaskUpdated",
        "TaskCompleted",
        "TaskDeleted"
    ]
    user_id: str
    task_id: int
    task_data: dict
