"""
WebSocket Real-Time Updates Consumer Service (Phase 7+).

Consumes: task-updates topic
Listens for: All real-time task updates
Action: Broadcasts updates to connected WebSocket clients

This is an independent service that can run as a separate Kubernetes deployment.
Phase 7+: Real-time bidirectional communication with clients
Phase 2.7: Foundation and consumer structure
"""
import asyncio
import json
import logging
from typing import Set, Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections and real-time updates.

    Phase 7+ Extension:
    - Maintains active WebSocket connections
    - Broadcasts updates to connected clients
    - Handles connection/disconnection lifecycle
    - Filters updates by user (user_id isolation)
    """

    def __init__(self):
        """Initialize WebSocket manager."""
        # Maps user_id -> set of connected WebSocket connections
        self.active_connections: Dict[str, Set] = {}
        self.processed_event_ids: Set[str] = set()

    def register_connection(self, user_id: str, connection) -> None:
        """
        Register a new WebSocket connection.

        Args:
            user_id: User owning the connection
            connection: WebSocket connection object
        """
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(connection)
        logger.info(
            f"WebSocket connected for user {user_id} "
            f"({len(self.active_connections[user_id])} total)"
        )

    def unregister_connection(self, user_id: str, connection) -> None:
        """
        Unregister a WebSocket connection.

        Args:
            user_id: User owning the connection
            connection: WebSocket connection object
        """
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(connection)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
            logger.info(
                f"WebSocket disconnected for user {user_id} "
                f"({len(self.active_connections.get(user_id, set()))} remaining)"
            )

    async def broadcast_to_user(self, user_id: str, message: dict) -> int:
        """
        Broadcast message to all connections for a user.

        Args:
            user_id: User to broadcast to
            message: Message dict to send

        Returns:
            Number of connections notified
        """
        if user_id not in self.active_connections:
            return 0

        connections = self.active_connections[user_id]
        disconnected = set()

        for connection in connections:
            try:
                # In production: await connection.send_json(message)
                logger.debug(
                    f"Broadcasting to {user_id}: "
                    f"{message.get('event_type', 'unknown')} "
                    f"task {message.get('task_id')}"
                )
                # Future: Actual WebSocket send
            except Exception as e:
                logger.error(f"Failed to broadcast to connection: {e}")
                disconnected.add(connection)

        # Clean up disconnected connections
        for connection in disconnected:
            self.unregister_connection(user_id, connection)

        return len(connections)

    async def broadcast_to_all(self, message: dict) -> int:
        """
        Broadcast message to all connected users.

        Args:
            message: Message dict to send

        Returns:
            Total number of connections notified
        """
        total = 0
        for user_id in list(self.active_connections.keys()):
            count = await self.broadcast_to_user(user_id, message)
            total += count
        return total


class WebSocketConsumer:
    """
    Consumes task-updates events and broadcasts to WebSocket clients.

    Phase 7+ Extension (Spec-006):
    - Listens to task-updates topic via Dapr Pub/Sub
    - Processes TaskUpdated events for real-time sync
    - Broadcasts to all connected clients of the task owner
    - Handles errors gracefully (doesn't block processing)
    - Idempotent: Safe to re-process same event
    """

    def __init__(self):
        """Initialize the WebSocket consumer."""
        self.ws_manager = WebSocketManager()
        self.processed_event_ids = set()

    async def start(self):
        """
        Start listening to task-updates topic.

        Phase 7+: Dapr Pub/Sub subscriber pattern
        In production with Dapr:
        - Subscribe to "kafka" pub/sub / "task-updates" topic
        - Dapr delivers events via HTTP POST
        - This service exposes /dapr/subscribe endpoint

        For MVP (without Dapr):
        - Simulates event consumption via logging
        """
        logger.info("WebSocket Consumer started")
        logger.info(
            "Listening for task updates on task-updates topic... "
            "(Phase 7+: Real-time sync)"
        )

        try:
            await asyncio.sleep(float('inf'))
        except KeyboardInterrupt:
            logger.info("WebSocket Consumer stopped")

    async def handle_task_update_event(self, event: dict) -> bool:
        """
        Handle incoming task update event from task-updates topic.

        Args:
            event: Task update event dict

        Returns:
            True if processed successfully, False if error
        """
        try:
            event_id = event.get("event_id")
            user_id = event.get("user_id")
            task_id = event.get("task_id")
            data = event.get("data", {})

            logger.debug(
                f"WebSocket: Received update for task {task_id} "
                f"from user {user_id} (event_id: {event_id})"
            )

            # Check idempotency
            if event_id in self.processed_event_ids:
                logger.debug(f"Event {event_id} already broadcasted, skipping")
                return True

            # Create WebSocket message
            ws_message = {
                "type": "task_update",
                "event_id": event_id,
                "timestamp": event.get("timestamp"),
                "task_id": task_id,
                "task": {
                    "id": data.get("id"),
                    "title": data.get("title"),
                    "is_complete": data.get("is_complete"),
                    "priority": data.get("priority"),
                    "due_date": data.get("due_date"),
                    "updated_at": data.get("updated_at")
                }
            }

            # Broadcast to user's WebSocket clients
            connections_notified = await self.ws_manager.broadcast_to_user(
                user_id,
                ws_message
            )

            logger.info(
                f"Broadcasted task {task_id} update to {connections_notified} "
                f"WebSocket(s) for user {user_id}"
            )

            self.processed_event_ids.add(event_id)
            return True

        except Exception as e:
            logger.error(
                f"Error processing task update event: {e}",
                exc_info=True
            )
            return False

    def get_connection_stats(self) -> dict:
        """
        Get statistics about active WebSocket connections.

        Returns:
            Dict with connection stats
        """
        total_connections = sum(
            len(conns) for conns in self.ws_manager.active_connections.values()
        )
        return {
            "active_users": len(self.ws_manager.active_connections),
            "total_connections": total_connections,
            "connections_by_user": {
                user_id: len(conns)
                for user_id, conns in self.ws_manager.active_connections.items()
            }
        }


async def main():
    """
    Main entry point for WebSocket consumer.

    In Kubernetes deployment:
    - Consumer service runs independently with Dapr sidecar
    - Receives task-updates events via HTTP POST
    - Maintains WebSocket connections to clients
    - Broadcasts real-time updates
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    consumer = WebSocketConsumer()
    await consumer.start()


if __name__ == "__main__":
    asyncio.run(main())
