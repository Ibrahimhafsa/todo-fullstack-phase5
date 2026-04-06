"""
Notification Consumer Service (Phase 2.7).

Consumes: reminders topic
Listens for: ReminderTriggered events
Action: Sends notifications (in-app, email, push, SMS)

This is an independent service that can run as a separate Kubernetes deployment.
Phase 7+: Implements multi-channel notification delivery.
Phase 2.7: Foundation for reminder handling.
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, Literal
from enum import Enum

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """Supported notification channels."""
    IN_APP = "in_app"
    EMAIL = "email"
    PUSH = "push"
    SMS = "sms"


class NotificationService:
    """
    Base notification service for multi-channel delivery.

    Phase 7+: Full notification system
    Phase 2.7: MVP reminder handling via logging
    """

    def __init__(self):
        """Initialize notification service."""
        self.channel_handlers = {
            NotificationChannel.IN_APP: self._send_in_app,
            NotificationChannel.EMAIL: self._send_email,
            NotificationChannel.PUSH: self._send_push,
            NotificationChannel.SMS: self._send_sms,
        }
        self.processed_event_ids = set()

    async def send_notification(
        self,
        user_id: str,
        task_id: int,
        task_title: str,
        message: str,
        channels: list[NotificationChannel] = None
    ) -> bool:
        """
        Send notification through multiple channels.

        Args:
            user_id: User to notify
            task_id: Task ID (for context)
            task_title: Task title (for notification)
            message: Notification message
            channels: List of channels (defaults to [IN_APP])

        Returns:
            True if all channels succeeded, False if any failed
        """
        if channels is None:
            channels = [NotificationChannel.IN_APP]

        results = []
        for channel in channels:
            try:
                handler = self.channel_handlers.get(channel)
                if handler:
                    result = await handler(user_id, task_id, task_title, message)
                    results.append(result)
                else:
                    logger.warning(f"Unknown notification channel: {channel}")
                    results.append(False)
            except Exception as e:
                logger.error(
                    f"Error sending {channel.value} notification to {user_id}: {e}",
                    exc_info=True
                )
                results.append(False)

        return all(results)

    @staticmethod
    async def _send_in_app(
        user_id: str,
        task_id: int,
        task_title: str,
        message: str
    ) -> bool:
        """
        Send in-app notification.

        Phase 7+: Store in database, deliver via WebSocket
        Phase 2.7: Log to console
        """
        try:
            logger.info(
                f"[IN-APP] Notification to user {user_id}: "
                f"Task {task_id} ({task_title}) - {message}"
            )
            # Future: Store in notifications table
            # Future: Push via WebSocket to client
            return True
        except Exception as e:
            logger.error(f"Failed to send in-app notification: {e}")
            return False

    @staticmethod
    async def _send_email(
        user_id: str,
        task_id: int,
        task_title: str,
        message: str
    ) -> bool:
        """
        Send email notification.

        Phase 7+: Use SendGrid, Mailgun, or AWS SES
        Phase 2.7: Log to console
        """
        try:
            logger.info(
                f"[EMAIL] Would send to {user_id}: "
                f"Task {task_id} ({task_title}) - {message}"
            )
            # Future: Integrate with email service (SendGrid, etc.)
            return True
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False

    @staticmethod
    async def _send_push(
        user_id: str,
        task_id: int,
        task_title: str,
        message: str
    ) -> bool:
        """
        Send push notification.

        Phase 7+: Use Firebase Cloud Messaging, APNs, etc.
        Phase 2.7: Log to console
        """
        try:
            logger.info(
                f"[PUSH] Would send to {user_id}: "
                f"Task {task_id} ({task_title}) - {message}"
            )
            # Future: Integrate with push service (FCM, APNs, etc.)
            return True
        except Exception as e:
            logger.error(f"Failed to send push notification: {e}")
            return False

    @staticmethod
    async def _send_sms(
        user_id: str,
        task_id: int,
        task_title: str,
        message: str
    ) -> bool:
        """
        Send SMS notification.

        Phase 7+: Use Twilio, AWS SNS, etc.
        Phase 2.7: Log to console
        """
        try:
            logger.info(
                f"[SMS] Would send to {user_id}: "
                f"Task {task_id} ({task_title}) - {message}"
            )
            # Future: Integrate with SMS service (Twilio, etc.)
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS notification: {e}")
            return False


class NotificationConsumer:
    """
    Consumes ReminderTriggered events and sends notifications.

    Phase 2.7 Extension (Spec-006):
    - Listens to reminders topic via Dapr Pub/Sub
    - Filters for ReminderTriggered events
    - Sends notifications via NotificationService
    - Handles errors gracefully (doesn't block processing)
    - Idempotent: Safe to re-process same event
    """

    def __init__(self):
        """Initialize the notification consumer."""
        self.notification_service = NotificationService()
        self.processed_event_ids = set()

    async def start(self):
        """
        Start listening to reminders topic.

        Phase 2.7: Dapr Pub/Sub subscriber pattern
        In production with Dapr:
        - Subscribe to "kafka" pub/sub / "reminders" topic
        - Dapr delivers events via HTTP POST
        - This service exposes /dapr/subscribe endpoint

        For MVP (without Dapr):
        - Simulates event consumption via logging
        """
        logger.info("Notification Consumer started")
        logger.info("Waiting for ReminderTriggered events from reminders topic...")

        try:
            await asyncio.sleep(float('inf'))
        except KeyboardInterrupt:
            logger.info("Notification Consumer stopped")

    async def handle_reminder_event(self, event: dict) -> bool:
        """
        Handle incoming reminder event from reminders topic.

        Args:
            event: Reminder event dict with event_id, user_id, task_id, task_title, reminder_time

        Returns:
            True if processed successfully, False if error
        """
        try:
            event_id = event.get("event_id")
            user_id = event.get("user_id")
            task_id = event.get("task_id")
            task_title = event.get("task_title")
            reminder_time = event.get("reminder_time")

            logger.info(
                f"Processing ReminderTriggered event: "
                f"task {task_id} for user {user_id} "
                f"(event_id: {event_id})"
            )

            # Check idempotency
            if event_id in self.processed_event_ids:
                logger.debug(f"Event {event_id} already processed, skipping")
                return True

            # Create notification message
            message = f"Reminder: {task_title}"

            # Send notification (default: in-app)
            result = await self.notification_service.send_notification(
                user_id=user_id,
                task_id=task_id,
                task_title=task_title,
                message=message,
                channels=[NotificationChannel.IN_APP]
            )

            if result:
                logger.info(f"Notification sent for event {event_id}")
                self.processed_event_ids.add(event_id)
                return True
            else:
                logger.warning(f"Failed to send notification for event {event_id}")
                return False

        except Exception as e:
            logger.error(
                f"Error processing ReminderTriggered event: {e}",
                exc_info=True
            )
            return False


async def main():
    """
    Main entry point for notification consumer.

    In Kubernetes deployment:
    - Consumer service runs independently with Dapr sidecar
    - Receives ReminderTriggered events via HTTP POST
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    consumer = NotificationConsumer()
    await consumer.start()


if __name__ == "__main__":
    asyncio.run(main())
