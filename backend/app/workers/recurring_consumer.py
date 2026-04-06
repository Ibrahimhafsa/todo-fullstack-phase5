"""
Recurring Task Consumer Service (Phase 2.7).

Consumes: task-events topic
Listens for: TaskCompleted events
Action: Generates next task instance for recurring tasks

This is an independent service that can run as a separate Kubernetes deployment.
Constitution XXVI: Event-driven task generation
"""
import asyncio
import json
import logging
from typing import Optional

from sqlmodel import Session, create_engine, select
from sqlalchemy.orm import sessionmaker

from app.models.task import Task
from app.services.recurring_service import generate_next_instance
from app.database import engine

logger = logging.getLogger(__name__)


class RecurringTaskConsumer:
    """
    Consumes TaskCompleted events and generates next instances.

    Phase 2.7 Extension (Spec-006):
    - Listens to task-events topic via Dapr Pub/Sub
    - Filters for TaskCompleted events
    - Calls RecurringService to generate next instance
    - Handles errors gracefully (doesn't block processing)
    - Idempotent: Safe to re-process same event
    """

    def __init__(self, database_url: str):
        """
        Initialize the recurring task consumer.

        Args:
            database_url: PostgreSQL connection string
        """
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.session_factory = sessionmaker(bind=self.engine)
        self.processed_event_ids = set()  # For idempotency tracking

    async def start(self):
        """
        Start listening to task-events topic.

        Phase 2.7: Dapr Pub/Sub subscriber pattern
        In production with Dapr:
        - Subscribe to "kafka" pub/sub / "task-events" topic
        - Dapr delivers events via HTTP POST to /dapr/subscribe endpoint
        - This service exposes HTTP endpoints to receive events

        For MVP (without Dapr):
        - Simulates event consumption via logging
        """
        logger.info("Recurring Task Consumer started")
        logger.info(f"Connecting to database: {self.database_url}")
        logger.info("Waiting for TaskCompleted events from task-events topic...")

        # In production with Dapr, this would be an HTTP server
        # receiving events from Dapr sidecar
        # For MVP, we just wait for manual event injection or testing
        try:
            await asyncio.sleep(float('inf'))
        except KeyboardInterrupt:
            logger.info("Recurring Task Consumer stopped")

    async def handle_task_event(self, event: dict) -> bool:
        """
        Handle incoming task event from task-events topic.

        Args:
            event: Task event dict with event_type, event_id, user_id, task_id, data

        Returns:
            True if processed successfully, False if error
        """
        try:
            event_type = event.get("event_type")
            event_id = event.get("event_id")
            user_id = event.get("user_id")
            task_id = event.get("task_id")

            # Only process TaskCompleted events
            if event_type != "TaskCompleted":
                logger.debug(f"Ignoring {event_type} event")
                return True

            logger.info(
                f"Processing TaskCompleted event: "
                f"task {task_id} for user {user_id} "
                f"(event_id: {event_id})"
            )

            # Check idempotency
            if event_id in self.processed_event_ids:
                logger.debug(f"Event {event_id} already processed, skipping")
                return True

            # Get task from database
            session = self.session_factory()
            try:
                task = self._get_task(session, user_id, task_id)
                if not task:
                    logger.warning(f"Task {task_id} not found for user {user_id}")
                    return False

                # Check if task is recurring
                if not task.is_recurring or not task.recurring_pattern:
                    logger.debug(f"Task {task_id} is not recurring, skipping")
                    return True

                # Generate next instance
                logger.info(
                    f"Generating next instance for recurring task {task_id} "
                    f"(pattern: {task.recurring_pattern})"
                )
                next_task = generate_next_instance(session, task, user_id)

                if next_task:
                    logger.info(
                        f"Next instance created: task {next_task.id} "
                        f"(due: {next_task.due_date})"
                    )
                    self.processed_event_ids.add(event_id)
                    return True
                else:
                    logger.warning(f"Failed to generate next instance for task {task_id}")
                    return False

            finally:
                session.close()

        except Exception as e:
            logger.error(
                f"Error processing TaskCompleted event: {e}",
                exc_info=True
            )
            return False

    @staticmethod
    def _get_task(session: Session, user_id: str, task_id: int) -> Optional[Task]:
        """Get task from database with ownership check."""
        statement = select(Task).where(
            Task.id == task_id,
            Task.user_id == user_id
        )
        return session.exec(statement).first()


async def main():
    """
    Main entry point for recurring task consumer.

    In Kubernetes deployment:
    - DATABASE_URL environment variable sets the database connection
    - Consumer service runs independently with Dapr sidecar
    """
    import os
    from dotenv import load_dotenv

    load_dotenv()
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/todo_db"
    )

    consumer = RecurringTaskConsumer(database_url)
    await consumer.start()


if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    asyncio.run(main())
