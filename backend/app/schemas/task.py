"""Request/Response schemas for Task API."""
from datetime import datetime
from typing import Optional
import json

from pydantic import BaseModel, field_validator, field_serializer


class TaskCreate(BaseModel):
    """Schema for creating a new task."""
    title: str
    description: Optional[str] = None
    # Phase 5 Extensions (Spec-006)
    priority: Optional[str] = "Medium"  # Low, Medium, High
    tags: Optional[list[str]] = None  # User-defined tags
    due_date: Optional[datetime] = None
    reminder_time: Optional[datetime] = None
    is_recurring: Optional[bool] = False
    recurring_pattern: Optional[str] = None  # Daily, Weekly, Monthly

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate title is non-empty and max 255 chars (FR-008)."""
        v = v.strip()
        if not v:
            raise ValueError("Title is required")
        if len(v) > 255:
            raise ValueError("Title must be 255 characters or less")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        """Validate priority is one of: Low, Medium, High."""
        if v is None:
            return "Medium"
        if v not in ("Low", "Medium", "High"):
            raise ValueError("Priority must be 'Low', 'Medium', or 'High'")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        """Validate tags are non-empty strings, max 50 chars each."""
        if v is None:
            return None
        if not isinstance(v, list):
            raise ValueError("Tags must be a list")
        for tag in v:
            if not isinstance(tag, str):
                raise ValueError("Each tag must be a string")
            if not tag.strip():
                raise ValueError("Tags cannot be empty")
            if len(tag) > 50:
                raise ValueError("Each tag must be 50 characters or less")
        return [tag.strip() for tag in v]

    @field_validator("recurring_pattern")
    @classmethod
    def validate_recurring_pattern(cls, v: Optional[str]) -> Optional[str]:
        """Validate recurring pattern if provided."""
        if v is None:
            return None
        if v not in ("Daily", "Weekly", "Monthly"):
            raise ValueError("Recurring pattern must be 'Daily', 'Weekly', or 'Monthly'")
        return v


class TaskUpdate(BaseModel):
    """Schema for updating an existing task."""
    title: Optional[str] = None
    description: Optional[str] = None
    # Phase 5 Extensions (Spec-006)
    priority: Optional[str] = None
    tags: Optional[list[str]] = None
    due_date: Optional[datetime] = None
    reminder_time: Optional[datetime] = None
    is_recurring: Optional[bool] = None
    recurring_pattern: Optional[str] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Validate title if provided."""
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be empty")
        if len(v) > 255:
            raise ValueError("Title must be 255 characters or less")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        """Validate priority if provided."""
        if v is None:
            return v
        if v not in ("Low", "Medium", "High"):
            raise ValueError("Priority must be 'Low', 'Medium', or 'High'")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        """Validate tags if provided."""
        if v is None:
            return v
        if not isinstance(v, list):
            raise ValueError("Tags must be a list")
        for tag in v:
            if not isinstance(tag, str):
                raise ValueError("Each tag must be a string")
            if not tag.strip():
                raise ValueError("Tags cannot be empty")
            if len(tag) > 50:
                raise ValueError("Each tag must be 50 characters or less")
        return [tag.strip() for tag in v]

    @field_validator("recurring_pattern")
    @classmethod
    def validate_recurring_pattern(cls, v: Optional[str]) -> Optional[str]:
        """Validate recurring pattern if provided."""
        if v is None:
            return v
        if v not in ("Daily", "Weekly", "Monthly"):
            raise ValueError("Recurring pattern must be 'Daily', 'Weekly', or 'Monthly'")
        return v


class TaskResponse(BaseModel):
    """Schema for task responses."""
    id: int
    user_id: str
    title: str
    description: Optional[str]
    is_complete: bool
    created_at: datetime
    updated_at: datetime
    # Phase 5 Extensions (Spec-006)
    priority: str = "Medium"
    tags: Optional[list[str]] = None  # Parsed from JSON string
    due_date: Optional[datetime] = None
    reminder_time: Optional[datetime] = None
    is_recurring: bool = False
    recurring_pattern: Optional[str] = None

    class Config:
        from_attributes = True

    @field_serializer("tags")
    def serialize_tags(self, value: Optional[str]) -> Optional[list[str]]:
        """Parse tags JSON string to list for API response."""
        if value is None or value == "[]":
            return None
        try:
            return json.loads(value) if isinstance(value, str) else value
        except (json.JSONDecodeError, TypeError):
            return None


class TaskListResponse(BaseModel):
    """Schema for list of tasks response."""
    tasks: list[TaskResponse]
    count: int
