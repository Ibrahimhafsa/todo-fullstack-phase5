"""
Event consumer workers for Phase 2.7.

This package contains independent consumer services that process events from Kafka topics.
Each service runs as a separate Kubernetes deployment with Dapr sidecar integration.

Services:
1. recurring_consumer: Generates next task instances on TaskCompleted
2. notification_consumer: Sends notifications on ReminderTriggered
3. audit_consumer: Logs all task mutations for compliance
4. websocket_consumer: Broadcasts real-time updates to WebSocket clients (Phase 7+)
"""

__all__ = [
    "recurring_consumer",
    "notification_consumer",
    "audit_consumer",
    "websocket_consumer",
]
