"""Recurring task automation service for Phase 2.5."""
from datetime import datetime, timedelta
from typing import Optional

from sqlmodel import Session

from app.models.task import Task


def calculate_next_due_date(
    current_due_date: Optional[datetime],
    pattern: str
) -> Optional[datetime]:
    """
    Calculate next due date based on recurring pattern.

    Phase 5 Extension (Spec-006):
    - Supports Daily (next day), Weekly (next 7 days), Monthly (next month)
    - Handles edge cases (e.g., month-end dates)
    - Returns None if no due_date provided

    Args:
        current_due_date: Current task's due_date
        pattern: Recurrence pattern ('Daily', 'Weekly', 'Monthly')

    Returns:
        Calculated next due_date, or None if input is None
    """
    if not current_due_date:
        return None

    if pattern == "Daily":
        return current_due_date + timedelta(days=1)
    elif pattern == "Weekly":
        return current_due_date + timedelta(days=7)
    elif pattern == "Monthly":
        # Handle month-end edge case (e.g., Jan 31 -> Feb 28/29)
        try:
            return current_due_date.replace(month=current_due_date.month + 1)
        except ValueError:
            # Day doesn't exist in next month (e.g., Jan 31 -> Feb 31)
            # Use last day of next month
            if current_due_date.month == 12:
                next_month = current_due_date.replace(year=current_due_date.year + 1, month=1, day=1)
            else:
                next_month = current_due_date.replace(month=current_due_date.month + 1, day=1)
            # Subtract 1 day to get last day of previous month
            return next_month - timedelta(days=1)
    else:
        # Unknown pattern, return None
        return None


def generate_next_instance(
    session: Session,
    parent_task: Task,
    user_id: str
) -> Optional[Task]:
    """
    Generate next instance of a recurring task.

    Phase 5 Extension (Spec-006):
    When a recurring task is marked complete, create a new instance with:
    - Same title, description, priority, tags
    - Calculated next due_date based on recurring_pattern
    - Inherited reminder_time (if any)
    - New instance starts as not complete
    - is_recurring and recurring_pattern preserved

    After creation:
    - Schedule reminder (if reminder_time provided)
    - Return new task instance

    Args:
        session: Database session
        parent_task: Completed parent task with is_recurring=True
        user_id: Authenticated user's ID from JWT

    Returns:
        Newly created Task, or None if generation failed

    Raises:
        Implicit: ValueError if pattern invalid (handled by calculate_next_due_date)
    """
    if not parent_task.is_recurring or not parent_task.recurring_pattern:
        return None

    # Calculate next due date
    next_due_date = calculate_next_due_date(
        parent_task.due_date,
        parent_task.recurring_pattern
    )

    # Create new task from parent template
    next_task = Task(
        user_id=user_id,
        title=parent_task.title,
        description=parent_task.description,
        priority=parent_task.priority,
        tags=parent_task.tags,  # JSON string, copied as-is
        due_date=next_due_date,
        reminder_time=parent_task.reminder_time,  # Inherited reminder time
        is_recurring=parent_task.is_recurring,
        recurring_pattern=parent_task.recurring_pattern,
        # is_complete defaults to False in model
        # timestamps default to utcnow() in model
    )

    session.add(next_task)
    session.commit()
    session.refresh(next_task)

    # Phase 2.5: Schedule reminder if reminder_time provided
    if next_task.reminder_time:
        from app.services.reminder_service import schedule_reminder
        schedule_reminder(
            task_id=next_task.id,
            user_id=user_id,
            reminder_time=next_task.reminder_time,
            title=next_task.title
        )

    return next_task


def get_recurring_info(task: Task) -> dict:
    """
    Get human-readable information about recurring task.

    Phase 5 Debug utility:
    Returns a dictionary describing the task's recurrence pattern.

    Args:
        task: Task to analyze

    Returns:
        Dict with recurrence info or empty dict if not recurring
    """
    if not task.is_recurring or not task.recurring_pattern:
        return {}

    next_date = calculate_next_due_date(task.due_date, task.recurring_pattern)
    return {
        "is_recurring": True,
        "pattern": task.recurring_pattern,
        "current_due_date": task.due_date.isoformat() if task.due_date else None,
        "next_due_date": next_date.isoformat() if next_date else None,
    }
