"""Task SQLModel for database persistence."""
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Task(SQLModel, table=True):
    """
    Task entity for user todo items.

    Ownership: Each task belongs to exactly one user, identified by user_id
    from JWT claims. All queries MUST filter by user_id (Constitution VII).

    Phase 5 Extensions (Spec-006):
    - priority: Low/Medium/High priority levels (default: Medium)
    - tags: JSON array of user-defined tags for categorization
    - due_date: Optional deadline for task completion
    - reminder_time: Optional time to send reminder before due_date
    - is_recurring: Whether this task repeats automatically
    - recurring_pattern: Daily/Weekly/Monthly recurrence pattern (if is_recurring=true)

    All new fields are optional (nullable) for backward compatibility.
    """
    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True, nullable=False)
    title: str = Field(max_length=255, nullable=False)
    description: Optional[str] = Field(default=None)
    is_complete: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Phase 5 Extensions (Spec-006: Advanced Features)
    priority: str = Field(default="Medium", max_length=20)  # Low, Medium, High
    tags: Optional[str] = Field(default="[]")  # JSON array stored as string
    due_date: Optional[datetime] = Field(default=None)
    reminder_time: Optional[datetime] = Field(default=None)
    is_recurring: bool = Field(default=False)
    recurring_pattern: Optional[str] = Field(default=None, max_length=20)  # Daily, Weekly, Monthly
