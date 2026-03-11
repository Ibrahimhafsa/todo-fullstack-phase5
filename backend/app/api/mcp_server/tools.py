"""MCP Tools for AI Chatbot (Spec-4).

Each tool wraps an existing Phase-2 task_service method.
CRITICAL: NO code duplication. Tools call task_service methods directly.
Principle XX (MCP Tool Governance): Only these 6 tools allowed.
"""
from typing import Any, Dict, Optional

from sqlmodel import Session

from app.models.task import Task
from app.services import task_service
from app.schemas.task import TaskCreate, TaskUpdate


def list_tasks(user_id: str, session: Session) -> list[Dict[str, Any]]:
    """
    List all tasks for authenticated user.

    MCP Tool: list_tasks
    Wraps: task_service.list_tasks(session, user_id)
    Returns: List of task dictionaries
    """
    tasks = task_service.list_tasks(session, user_id)
    return [
        {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "is_complete": task.is_complete,
            "created_at": task.created_at.isoformat(),
        }
        for task in tasks
    ]


def get_task(user_id: str, task_id: int, session: Session) -> Optional[Dict[str, Any]]:
    """
    Get single task by ID.

    MCP Tool: get_task
    Wraps: task_service.get_task(session, user_id, task_id)
    Returns: Task dictionary or None if not found/not owned
    """
    task = task_service.get_task(session, user_id, task_id)
    if not task:
        return None

    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "is_complete": task.is_complete,
        "created_at": task.created_at.isoformat(),
    }


def create_task(
    user_id: str,
    title: str,
    session: Session,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create new task.

    MCP Tool: create_task
    Wraps: task_service.create_task(session, user_id, TaskCreate(...))
    Returns: Created task dictionary
    """
    task_create = TaskCreate(title=title, description=description)
    task = task_service.create_task(session, user_id, task_create)

    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "is_complete": task.is_complete,
        "created_at": task.created_at.isoformat(),
    }


def update_task(
    user_id: str,
    task_id: int,
    session: Session,
    title: Optional[str] = None,
    description: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Update task.

    MCP Tool: update_task
    Wraps: task_service.update_task(session, user_id, task_id, TaskUpdate(...))
    Returns: Updated task dictionary or None if not found/not owned
    """
    task_update = TaskUpdate(title=title, description=description)
    task = task_service.update_task(session, user_id, task_id, task_update)

    if not task:
        return None

    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "is_complete": task.is_complete,
        "updated_at": task.updated_at.isoformat(),
    }


def delete_task(user_id: str, task_id: int, session: Session) -> bool:
    """
    Delete task.

    MCP Tool: delete_task
    Wraps: task_service.delete_task(session, user_id, task_id)
    Returns: True if deleted, False if not found/not owned
    """
    return task_service.delete_task(session, user_id, task_id)


def complete_task(
    user_id: str,
    task_id: int,
    session: Session,
) -> Optional[Dict[str, Any]]:
    """
    Toggle task completion status.

    MCP Tool: complete_task
    Wraps: task_service.toggle_complete(session, user_id, task_id)
    Returns: Updated task dictionary or None if not found/not owned
    """
    task = task_service.toggle_complete(session, user_id, task_id)

    if not task:
        return None

    return {
        "id": task.id,
        "title": task.title,
        "is_complete": task.is_complete,
        "updated_at": task.updated_at.isoformat(),
    }


# Tool registry for MCP Server
# Each tool definition for the MCP protocol
TOOLS = {
    "list_tasks": {
        "name": "list_tasks",
        "description": "List all tasks for the authenticated user",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "Authenticated user ID"}
            },
            "required": ["user_id"],
        },
    },
    "get_task": {
        "name": "get_task",
        "description": "Get a single task by ID",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "Authenticated user ID"},
                "task_id": {"type": "integer", "description": "Task ID"},
            },
            "required": ["user_id", "task_id"],
        },
    },
    "create_task": {
        "name": "create_task",
        "description": "Create a new task",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "Authenticated user ID"},
                "title": {"type": "string", "description": "Task title"},
                "description": {
                    "type": "string",
                    "description": "Task description (optional)",
                },
            },
            "required": ["user_id", "title"],
        },
    },
    "update_task": {
        "name": "update_task",
        "description": "Update an existing task",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "Authenticated user ID"},
                "task_id": {"type": "integer", "description": "Task ID"},
                "title": {"type": "string", "description": "New title (optional)"},
                "description": {
                    "type": "string",
                    "description": "New description (optional)",
                },
            },
            "required": ["user_id", "task_id"],
        },
    },
    "delete_task": {
        "name": "delete_task",
        "description": "Delete a task",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "Authenticated user ID"},
                "task_id": {"type": "integer", "description": "Task ID"},
            },
            "required": ["user_id", "task_id"],
        },
    },
    "complete_task": {
        "name": "complete_task",
        "description": "Toggle task completion status",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "Authenticated user ID"},
                "task_id": {"type": "integer", "description": "Task ID"},
            },
            "required": ["user_id", "task_id"],
        },
    },
}
