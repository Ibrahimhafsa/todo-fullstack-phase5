"""Reminder scheduling service using APScheduler.

Phase 5 Extensions (Spec-006): Reminder scheduling and notifications.

This service manages task reminders using APScheduler for in-process scheduling.
Reminders are stored in memory and triggered at the scheduled reminder_time.

For MVP (single-instance): APScheduler in-process is sufficient.
Future (multi-instance): Move to distributed scheduler (Celery, etc).
"""
from datetime import datetime
from typing import Optional
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler: Optional[AsyncIOScheduler] = None


def get_scheduler() -> Optional[AsyncIOScheduler]:
    """Get the global APScheduler instance."""
    return _scheduler


def set_scheduler(scheduler: AsyncIOScheduler) -> None:
    """Set the global APScheduler instance (called during app startup)."""
    global _scheduler
    _scheduler = scheduler


def schedule_reminder(
    task_id: int,
    user_id: str,
    reminder_time: datetime,
    title: str
) -> bool:
    """
    Schedule a reminder for a task.

    Phase 5 Extensions (Spec-006):
    - Schedules reminder to trigger at reminder_time
    - Reminder event triggers notification (Phase 7)
    - Handles rescheduling if task updated

    Args:
        task_id: Task ID to remind about
        user_id: User ID for context
        reminder_time: When to trigger reminder (datetime)
        title: Task title for logging/notification

    Returns:
        True if scheduled successfully, False if scheduler unavailable
    """
    if not _scheduler:
        logger.warning(f"Scheduler not available; cannot schedule reminder for task {task_id}")
        return False

    try:
        job_id = f"reminder_{user_id}_{task_id}"

        # Remove existing job if present (reschedule case)
        try:
            _scheduler.remove_job(job_id)
        except Exception:
            pass  # Job doesn't exist, that's fine

        # Schedule new job
        _scheduler.add_job(
            _trigger_reminder,
            trigger=DateTrigger(run_date=reminder_time),
            args=[task_id, user_id, title],
            id=job_id,
            name=f"Reminder for task {task_id}",
            replace_existing=True
        )

        logger.info(
            f"Scheduled reminder for task {task_id} (user {user_id}) "
            f"at {reminder_time}: {title}"
        )
        return True

    except Exception as e:
        logger.error(f"Failed to schedule reminder for task {task_id}: {str(e)}")
        return False


def cancel_reminder(task_id: int, user_id: str) -> bool:
    """
    Cancel a scheduled reminder for a task.

    Called when:
    - reminder_time is cleared (set to null)
    - task is deleted
    - reminder_time is updated

    Args:
        task_id: Task ID to cancel reminder for
        user_id: User ID for context

    Returns:
        True if canceled or didn't exist, False if error
    """
    if not _scheduler:
        logger.warning(f"Scheduler not available; cannot cancel reminder for task {task_id}")
        return False

    try:
        job_id = f"reminder_{user_id}_{task_id}"
        try:
            _scheduler.remove_job(job_id)
            logger.info(f"Canceled reminder for task {task_id} (user {user_id})")
        except Exception:
            # Job doesn't exist, that's fine
            logger.debug(f"No reminder scheduled for task {task_id}")

        return True

    except Exception as e:
        logger.error(f"Failed to cancel reminder for task {task_id}: {str(e)}")
        return False


async def _trigger_reminder(task_id: int, user_id: str, title: str) -> None:
    """
    Internal callback triggered when reminder time arrives.

    This is called by APScheduler at the scheduled time.
    In Phase 5, we log the reminder and emit an event.
    In Phase 7, notifications are sent to user.

    Phase 5 MVP: Log reminder
    Phase 7+: Send notification (in-app, email, push, etc)
    Phase 2.7: Emit event to reminders topic (Kafka/Dapr)

    Args:
        task_id: Task ID being reminded
        user_id: User ID to notify
        title: Task title
    """
    logger.info(f"🔔 REMINDER: Task {task_id} (user {user_id}): {title}")

    # Phase 5: Just log the reminder
    # Phase 7+: Send notification here
    # Phase 2.7: Publish to reminders topic

    # TODO: Emit reminder event to Kafka reminders topic (Phase 2.7)
    # from app.services.event_service import publish_event
    # await publish_event({
    #     "event_type": "ReminderTriggered",
    #     "task_id": task_id,
    #     "user_id": user_id,
    #     "title": title,
    #     "timestamp": datetime.utcnow().isoformat()
    # })


def get_scheduled_reminders() -> dict:
    """
    Get all currently scheduled reminders (for debugging/monitoring).

    Returns:
        Dict mapping job_id to job details
    """
    if not _scheduler:
        return {}

    try:
        reminders = {}
        for job in _scheduler.get_jobs():
            if "reminder_" in job.id:
                reminders[job.id] = {
                    "job_id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                }
        return reminders
    except Exception as e:
        logger.error(f"Failed to get scheduled reminders: {str(e)}")
        return {}
