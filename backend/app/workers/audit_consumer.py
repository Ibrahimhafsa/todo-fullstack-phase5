"""
Audit Logging Consumer Service (Phase 2.7).

Consumes: task-events topic
Listens for: All task events (TaskCreated, Updated, Completed, Deleted)
Action: Logs all mutations to audit trail for compliance and debugging

This is an independent service that can run as a separate Kubernetes deployment.
Constitution III: Audit trail for all mutations
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

from sqlmodel import Session, create_engine, select
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class AuditLog:
    """
    Audit log entry structure.

    Phase 2.7: Immutable audit trail for all task mutations
    """

    def __init__(
        self,
        event_type: str,
        event_id: str,
        user_id: str,
        task_id: int,
        timestamp: str,
        task_title: str,
        changes: Optional[dict] = None
    ):
        """
        Initialize audit log entry.

        Args:
            event_type: TaskCreated/Updated/Completed/Deleted
            event_id: Unique event ID
            user_id: User who triggered the event
            task_id: Task ID
            timestamp: Event timestamp
            task_title: Task title (for context)
            changes: Changed fields (for Update events)
        """
        self.event_type = event_type
        self.event_id = event_id
        self.user_id = user_id
        self.task_id = task_id
        self.timestamp = timestamp
        self.task_title = task_title
        self.changes = changes or {}

    def to_dict(self) -> dict:
        """Convert to dictionary for logging/storage."""
        return {
            "event_type": self.event_type,
            "event_id": self.event_id,
            "user_id": self.user_id,
            "task_id": self.task_id,
            "timestamp": self.timestamp,
            "task_title": self.task_title,
            "changes": self.changes
        }


class AuditService:
    """
    Audit logging service for task events.

    Phase 2.7 Extension (Spec-006):
    - Logs all task mutations (create, update, complete, delete)
    - Stores immutable audit trail
    - Enables compliance and forensic analysis
    - Non-blocking: Event processing doesn't affect audit
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize audit service.

        Args:
            database_url: PostgreSQL connection (optional, for Phase 7+)
        """
        self.database_url = database_url
        if database_url:
            self.engine = create_engine(database_url, echo=False)
            self.session_factory = sessionmaker(bind=self.engine)
        else:
            self.engine = None
            self.session_factory = None

    async def log_event(self, audit_log: AuditLog) -> bool:
        """
        Log an event to the audit trail.

        Phase 2.7: Logs to console (development)
        Phase 7+: Logs to AuditLog table in database

        Args:
            audit_log: AuditLog instance

        Returns:
            True if logged successfully, False if error
        """
        try:
            log_data = audit_log.to_dict()

            # Log to console (development)
            logger.info(
                f"AUDIT: [{audit_log.event_type}] "
                f"User {audit_log.user_id} / Task {audit_log.task_id} ({audit_log.task_title}) "
                f"at {audit_log.timestamp} (event_id: {audit_log.event_id})"
            )

            # Phase 7+: Store in AuditLog table
            if self.session_factory:
                session = self.session_factory()
                try:
                    # Future: Create AuditLogModel and persist
                    # audit_log_model = AuditLogModel(**log_data)
                    # session.add(audit_log_model)
                    # session.commit()
                    pass
                finally:
                    session.close()

            return True

        except Exception as e:
            logger.error(f"Failed to log audit event: {e}", exc_info=True)
            return False


class AuditConsumer:
    """
    Consumes task-events and logs all mutations to audit trail.

    Phase 2.7 Extension (Spec-006):
    - Listens to task-events topic via Dapr Pub/Sub
    - Processes all event types (Create/Update/Complete/Delete)
    - Logs to audit trail for compliance
    - Handles errors gracefully (doesn't block processing)
    - Idempotent: Safe to re-process same event
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize the audit consumer.

        Args:
            database_url: PostgreSQL connection (optional)
        """
        self.audit_service = AuditService(database_url)
        self.processed_event_ids = set()

    async def start(self):
        """
        Start listening to task-events topic.

        Phase 2.7: Dapr Pub/Sub subscriber pattern
        In production with Dapr:
        - Subscribe to "kafka" pub/sub / "task-events" topic
        - Dapr delivers events via HTTP POST
        - This service exposes /dapr/subscribe endpoint

        For MVP (without Dapr):
        - Simulates event consumption via logging
        """
        logger.info("Audit Consumer started")
        logger.info("Listening to all task events on task-events topic...")

        try:
            await asyncio.sleep(float('inf'))
        except KeyboardInterrupt:
            logger.info("Audit Consumer stopped")

    async def handle_task_event(self, event: dict) -> bool:
        """
        Handle incoming task event from task-events topic.

        Args:
            event: Task event dict with event_type, event_id, user_id, task_id, data

        Returns:
            True if logged successfully, False if error
        """
        try:
            event_type = event.get("event_type")
            event_id = event.get("event_id")
            user_id = event.get("user_id")
            task_id = event.get("task_id")
            timestamp = event.get("timestamp")
            data = event.get("data", {})

            logger.debug(
                f"Audit: Received {event_type} event for task {task_id} "
                f"(event_id: {event_id})"
            )

            # Check idempotency
            if event_id in self.processed_event_ids:
                logger.debug(f"Event {event_id} already audited, skipping")
                return True

            # Create audit log
            audit_log = AuditLog(
                event_type=event_type,
                event_id=event_id,
                user_id=user_id,
                task_id=task_id,
                timestamp=timestamp,
                task_title=data.get("title", "Unknown"),
                changes=self._extract_changes(event_type, data)
            )

            # Log to audit trail
            result = await self.audit_service.log_event(audit_log)

            if result:
                self.processed_event_ids.add(event_id)
                return True
            else:
                logger.warning(f"Failed to audit event {event_id}")
                return False

        except Exception as e:
            logger.error(
                f"Error processing task event for audit: {e}",
                exc_info=True
            )
            return False

    @staticmethod
    def _extract_changes(event_type: str, data: dict) -> dict:
        """
        Extract relevant changes from event data.

        Phase 2.7: Log meaningful changes for audit trail

        Args:
            event_type: Event type
            data: Task data

        Returns:
            Dictionary of changes
        """
        if event_type == "TaskCreated":
            return {
                "title": data.get("title"),
                "priority": data.get("priority"),
                "is_recurring": data.get("is_recurring")
            }
        elif event_type == "TaskUpdated":
            return {
                "title": data.get("title"),
                "priority": data.get("priority"),
                "due_date": data.get("due_date"),
                "reminder_time": data.get("reminder_time")
            }
        elif event_type == "TaskCompleted":
            return {
                "is_complete": data.get("is_complete"),
                "completed_at": data.get("updated_at")
            }
        elif event_type == "TaskDeleted":
            return {
                "title": data.get("title"),
                "deleted_at": data.get("updated_at")
            }
        else:
            return {}


async def main():
    """
    Main entry point for audit consumer.

    In Kubernetes deployment:
    - Consumer service runs independently with Dapr sidecar
    - Receives all task events via HTTP POST
    - Logs to console and/or database
    """
    import os
    from dotenv import load_dotenv

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    load_dotenv()
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/todo_db"
    )

    consumer = AuditConsumer(database_url)
    await consumer.start()


if __name__ == "__main__":
    asyncio.run(main())
