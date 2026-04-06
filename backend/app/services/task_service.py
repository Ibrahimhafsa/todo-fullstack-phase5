"""Task CRUD service layer with ownership enforcement."""
import asyncio
from datetime import datetime
from typing import Optional, Literal

from sqlmodel import Session, select, and_, or_, func

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


def create_task(session: Session, user_id: str, data: TaskCreate) -> Task:
    """
    Create a new task for the authenticated user.

    FR-007: Create tasks with title and optional description
    FR-009: Automatically assign authenticated user's ID as owner
    FR-010: Set is_complete to false by default
    FR-011: Generate timestamps automatically

    Phase 5 Extensions (Spec-006):
    - priority: Low/Medium/High (default: Medium)
    - tags: JSON array of strings (default: [])
    - due_date: optional deadline
    - reminder_time: optional reminder time
    - is_recurring: auto-repeat flag (default: False)
    - recurring_pattern: Daily/Weekly/Monthly (optional)

    Args:
        session: Database session
        user_id: Authenticated user's ID from JWT (NOT from request!)
        data: Task creation data

    Returns:
        Created Task instance
    """
    import json

    # Convert tags list to JSON string if provided
    tags_json = "[]"
    if data.tags:
        tags_json = json.dumps(data.tags)

    task = Task(
        user_id=user_id,
        title=data.title,
        description=data.description,
        # Phase 5 Fields
        priority=data.priority or "Medium",
        tags=tags_json,
        due_date=data.due_date,
        reminder_time=data.reminder_time,
        is_recurring=data.is_recurring or False,
        recurring_pattern=data.recurring_pattern,
        # is_complete defaults to False in model
        # timestamps default to utcnow() in model
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    # Phase 5: Schedule reminder if reminder_time provided
    if task.reminder_time:
        from app.services.reminder_service import schedule_reminder
        schedule_reminder(
            task_id=task.id,
            user_id=user_id,
            reminder_time=task.reminder_time,
            title=task.title
        )

    # Phase 2.6: Publish TaskCreated event (async, non-blocking)
    from app.services.event_service import publish_task_created
    asyncio.create_task(publish_task_created(task))

    return task


def list_tasks(
    session: Session,
    user_id: str,
    search_query: Optional[str] = None,
    priority_filter: Optional[str] = None,
    tags_filter: Optional[list[str]] = None,
    due_date_start: Optional[datetime] = None,
    due_date_end: Optional[datetime] = None,
    sort_by: Optional[Literal["created_at", "due_date", "priority"]] = None,
    sort_order: Optional[Literal["asc", "desc"]] = "asc"
) -> list[Task]:
    """
    List tasks with search, filter, and sort support.

    Phase 5 Extensions (Spec-006):
    - Search: case-insensitive title/description search
    - Filter: by priority, tags, due_date range
    - Sort: by created_at, due_date, priority

    FR-012: List all own tasks
    FR-004: Filter by authenticated user's ID (Constitution VII)
    Performance: < 200ms for 50K tasks (with indexes)

    Args:
        session: Database session
        user_id: Authenticated user's ID from JWT
        search_query: Search in title/description (case-insensitive, optional)
        priority_filter: Filter by single priority value (optional)
        tags_filter: Filter by tags (any tag match, optional)
        due_date_start: Filter tasks due on or after this date (optional)
        due_date_end: Filter tasks due on or before this date (optional)
        sort_by: Sort by 'created_at', 'due_date', or 'priority' (optional)
        sort_order: Sort order 'asc' or 'desc' (default: 'asc')

    Returns:
        List of tasks matching criteria, sorted as requested
    """
    import json

    # Start with user_id filter (Constitution VII)
    conditions = [Task.user_id == user_id]

    # Add search filter (title or description contains search_query)
    if search_query and search_query.strip():
        search_pattern = f"%{search_query.strip()}%"
        conditions.append(
            or_(
                Task.title.ilike(search_pattern),
                Task.description.ilike(search_pattern)
            )
        )

    # Add priority filter
    if priority_filter:
        conditions.append(Task.priority == priority_filter)

    # Add tags filter (checks if any tag in filter list exists in task's tags)
    if tags_filter:
        # For JSON array filtering: check if tags overlap with filter
        # Note: This uses JSONB operators available in PostgreSQL
        tag_conditions = []
        for tag in tags_filter:
            # Check if tag appears in JSON array
            tag_conditions.append(Task.tags.like(f'%{tag}%'))
        conditions.append(or_(*tag_conditions))

    # Add due_date range filter
    if due_date_start:
        conditions.append(Task.due_date >= due_date_start)
    if due_date_end:
        conditions.append(Task.due_date <= due_date_end)

    # Build statement with all conditions
    statement = select(Task).where(and_(*conditions))

    # Apply sorting
    if sort_by == "due_date":
        if sort_order == "desc":
            statement = statement.order_by(Task.due_date.desc())
        else:
            statement = statement.order_by(Task.due_date.asc())
    elif sort_by == "priority":
        # Priority custom sort: Low < Medium < High
        priority_order = {"Low": 0, "Medium": 1, "High": 2}
        if sort_order == "desc":
            statement = statement.order_by(
                func.case(
                    (Task.priority == "Low", 2),
                    (Task.priority == "Medium", 1),
                    (Task.priority == "High", 0),
                    else_=3
                )
            )
        else:
            statement = statement.order_by(
                func.case(
                    (Task.priority == "Low", 0),
                    (Task.priority == "Medium", 1),
                    (Task.priority == "High", 2),
                    else_=3
                )
            )
    else:
        # Default: sort by created_at
        if sort_order == "desc":
            statement = statement.order_by(Task.created_at.desc())
        else:
            statement = statement.order_by(Task.created_at.asc())

    return list(session.exec(statement).all())


def get_task(session: Session, user_id: str, task_id: int) -> Optional[Task]:
    """
    Get a single task by ID if owned by the user.
    
    FR-013: Retrieve single task by ID
    FR-004, FR-005: Filter by user_id, return None for non-owned
    
    Args:
        session: Database session
        user_id: Authenticated user's ID from JWT
        task_id: Task ID to retrieve
        
    Returns:
        Task if found and owned, None otherwise
    """
    statement = select(Task).where(
        Task.id == task_id,
        Task.user_id == user_id
    )
    return session.exec(statement).first()


def update_task(
    session: Session,
    user_id: str,
    task_id: int,
    data: TaskUpdate
) -> Optional[Task]:
    """
    Update task title and/or description and Phase 5 fields.

    FR-015: Update title/description of owned tasks
    FR-016: Update updated_at timestamp
    FR-006: Cannot modify user_id (not in TaskUpdate schema)

    Phase 5 Extensions (Spec-006):
    - priority: Low/Medium/High
    - tags: JSON array of strings
    - due_date: optional deadline
    - reminder_time: optional reminder time
    - is_recurring: auto-repeat flag
    - recurring_pattern: Daily/Weekly/Monthly

    Args:
        session: Database session
        user_id: Authenticated user's ID from JWT
        task_id: Task ID to update
        data: Update data

    Returns:
        Updated Task if found and owned, None otherwise
    """
    import json

    task = get_task(session, user_id, task_id)
    if not task:
        return None

    if data.title is not None:
        task.title = data.title
    if data.description is not None:
        task.description = data.description

    # Phase 5 Fields
    reminder_changed = False
    if data.priority is not None:
        task.priority = data.priority
    if data.tags is not None:
        task.tags = json.dumps(data.tags)
    if data.due_date is not None:
        task.due_date = data.due_date
    if data.reminder_time is not None:
        task.reminder_time = data.reminder_time
        reminder_changed = True
    if data.is_recurring is not None:
        task.is_recurring = data.is_recurring
    if data.recurring_pattern is not None:
        task.recurring_pattern = data.recurring_pattern

    task.updated_at = datetime.utcnow()
    session.add(task)
    session.commit()
    session.refresh(task)

    # Phase 5: Reschedule reminder if reminder_time was changed
    if reminder_changed:
        from app.services.reminder_service import schedule_reminder, cancel_reminder

        if task.reminder_time:
            # Reschedule reminder
            schedule_reminder(
                task_id=task.id,
                user_id=user_id,
                reminder_time=task.reminder_time,
                title=task.title
            )
        else:
            # Cancel reminder if reminder_time set to null
            cancel_reminder(task.id, user_id)

    # Phase 2.6: Publish TaskUpdated event (async, non-blocking)
    from app.services.event_service import publish_task_updated
    asyncio.create_task(publish_task_updated(task))

    return task


def delete_task(session: Session, user_id: str, task_id: int) -> bool:
    """
    Delete a task if owned by the user.

    FR-018: Delete owned tasks
    FR-019: Permanently remove from database

    Phase 5 Extensions (Spec-006):
    - Cancel any scheduled reminders for the task

    Phase 2.6 Extensions:
    - Publish TaskDeleted event (async, non-blocking)

    Args:
        session: Database session
        user_id: Authenticated user's ID from JWT
        task_id: Task ID to delete

    Returns:
        True if deleted, False if not found or not owned
    """
    task = get_task(session, user_id, task_id)
    if not task:
        return False

    # Phase 5: Cancel reminder before deleting task
    if task.reminder_time:
        from app.services.reminder_service import cancel_reminder
        cancel_reminder(task_id, user_id)

    # Phase 2.6: Publish TaskDeleted event BEFORE deletion (async, non-blocking)
    # Publish first so event contains task data
    from app.services.event_service import publish_task_deleted
    asyncio.create_task(publish_task_deleted(task))

    session.delete(task)
    session.commit()
    return True


def toggle_complete(session: Session, user_id: str, task_id: int) -> Optional[Task]:
    """
    Toggle task completion status.

    FR-017: Toggle is_complete status
    FR-016: Update updated_at timestamp

    Phase 5 Extension (Spec-006):
    - Detect is_recurring flag when marking task complete
    - Generate next instance automatically
    - Schedule reminder for next instance (if reminder_time set)

    Phase 2.6 Extension:
    - Publish TaskCompleted event when marked complete (async, non-blocking)

    Args:
        session: Database session
        user_id: Authenticated user's ID from JWT
        task_id: Task ID to toggle

    Returns:
        Updated Task if found and owned, None otherwise
    """
    task = get_task(session, user_id, task_id)
    if not task:
        return None

    task.is_complete = not task.is_complete
    task.updated_at = datetime.utcnow()
    session.add(task)
    session.commit()
    session.refresh(task)

    # Phase 5: Generate next instance if task is being marked complete and is recurring
    if task.is_complete and task.is_recurring and task.recurring_pattern:
        from app.services.recurring_service import generate_next_instance
        generate_next_instance(session, task, user_id)

    # Phase 2.6: Publish TaskCompleted event if task marked complete (async, non-blocking)
    if task.is_complete:
        from app.services.event_service import publish_task_completed
        asyncio.create_task(publish_task_completed(task))

    return task
