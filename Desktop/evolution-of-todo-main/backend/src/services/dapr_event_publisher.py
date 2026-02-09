"""
Dapr event publisher for publishing events to Kafka topics.

Uses Dapr Pub/Sub API for event-driven architecture.
"""
import httpx
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from backend.src.models.todo import Task

logger = logging.getLogger(__name__)

# Dapr configuration
DAPR_HTTP_PORT = 3500
DAPR_PUBSUB_NAME = "pubsub"


class DaprEventPublisher:
    """Publisher for Dapr Pub/Sub events."""

    def __init__(self, dapr_port: int = DAPR_HTTP_PORT):
        """Initialize publisher with Dapr HTTP port."""
        self.dapr_url = f"http://localhost:{dapr_port}"
        self.pubsub_name = DAPR_PUBSUB_NAME

    async def publish_task_created(
        self,
        task: Task,
        source: str,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publish task.created event to task-events topic.

        Args:
            task: Created task
            source: Service that created the task (e.g., "chat_api", "todo_api")
            correlation_id: Correlation ID for tracing (optional)

        Returns:
            True if published successfully, False otherwise
        """
        event = self._build_task_event(
            event_type="task.created",
            task=task,
            changes=None,
            source=source,
            correlation_id=correlation_id
        )

        return await self._publish("task-events", event)

    async def publish_task_updated(
        self,
        task: Task,
        changes: Dict[str, Dict[str, Any]],
        source: str,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publish task.updated event to task-events topic.

        Args:
            task: Updated task
            changes: Dictionary of changed fields with old/new values
            source: Service that updated the task
            correlation_id: Correlation ID for tracing (optional)

        Returns:
            True if published successfully, False otherwise
        """
        event = self._build_task_event(
            event_type="task.updated",
            task=task,
            changes=changes,
            source=source,
            correlation_id=correlation_id
        )

        return await self._publish("task-events", event)

    async def publish_task_completed(
        self,
        task: Task,
        source: str,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publish task.completed event to task-events topic.

        Args:
            task: Completed task
            source: Service that completed the task
            correlation_id: Correlation ID for tracing (optional)

        Returns:
            True if published successfully, False otherwise
        """
        changes = {
            "completed": {
                "old_value": False,
                "new_value": True
            }
        }

        event = self._build_task_event(
            event_type="task.completed",
            task=task,
            changes=changes,
            source=source,
            correlation_id=correlation_id
        )

        return await self._publish("task-events", event)

    async def publish_task_deleted(
        self,
        task: Task,
        source: str,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publish task.deleted event to task-events topic.

        Args:
            task: Deleted task
            source: Service that deleted the task
            correlation_id: Correlation ID for tracing (optional)

        Returns:
            True if published successfully, False otherwise
        """
        event = self._build_task_event(
            event_type="task.deleted",
            task=task,
            changes=None,
            source=source,
            correlation_id=correlation_id
        )

        return await self._publish("task-events", event)

    async def publish_task_update_sync(
        self,
        task: Task,
        event_type: str,
        changes: Optional[Dict[str, Dict[str, Any]]],
        source: str,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publish task update to task-updates topic for real-time sync.

        Args:
            task: Task
            event_type: Event type (task.created, task.updated, etc.)
            changes: Changed fields (optional)
            source: Service that triggered the event
            correlation_id: Correlation ID for tracing (optional)

        Returns:
            True if published successfully, False otherwise
        """
        event = self._build_task_update_event(
            event_type=event_type,
            task=task,
            changes=changes,
            source=source,
            correlation_id=correlation_id
        )

        return await self._publish("task-updates", event)

    def _build_task_event(
        self,
        event_type: str,
        task: Task,
        changes: Optional[Dict[str, Dict[str, Any]]],
        source: str,
        correlation_id: Optional[str]
    ) -> Dict[str, Any]:
        """Build task event payload."""
        event_id = str(uuid.uuid4())
        correlation_id = correlation_id or str(uuid.uuid4())

        return {
            "schema_version": "1.0",
            "event_id": event_id,
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user_id": task.user_id,
            "task": {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "completed": task.completed,
                "priority": task.priority.value,
                "due_date": task.due_date.isoformat() + "Z" if task.due_date else None,
                "tags": task.tags,
                "recurrence_pattern_id": task.recurrence_pattern_id,
                "is_recurring_instance": task.is_recurring_instance,
                "parent_task_id": task.parent_task_id,
                "created_at": task.created_at.isoformat() + "Z",
                "updated_at": task.updated_at.isoformat() + "Z"
            },
            "changes": changes,
            "metadata": {
                "source": source,
                "correlation_id": correlation_id
            }
        }

    def _build_task_update_event(
        self,
        event_type: str,
        task: Task,
        changes: Optional[Dict[str, Dict[str, Any]]],
        source: str,
        correlation_id: Optional[str]
    ) -> Dict[str, Any]:
        """Build task update event payload for real-time sync."""
        event_id = str(uuid.uuid4())
        correlation_id = correlation_id or str(uuid.uuid4())

        return {
            "schema_version": "1.0",
            "event_id": event_id,
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user_id": task.user_id,
            "task": {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "completed": task.completed,
                "priority": task.priority.value,
                "due_date": task.due_date.isoformat() + "Z" if task.due_date else None,
                "tags": task.tags,
                "created_at": task.created_at.isoformat() + "Z",
                "updated_at": task.updated_at.isoformat() + "Z"
            },
            "changes": changes,
            "reminder": None,
            "metadata": {
                "source": source,
                "correlation_id": correlation_id,
                "device_id": None,
                "sync_priority": "normal"
            }
        }

    async def _publish(self, topic: str, event: Dict[str, Any]) -> bool:
        """
        Publish event to Dapr Pub/Sub.

        Args:
            topic: Topic name
            event: Event payload

        Returns:
            True if published successfully, False otherwise
        """
        url = f"{self.dapr_url}/v1.0/publish/{self.pubsub_name}/{topic}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=event, timeout=5.0)
                response.raise_for_status()

            logger.info(f"Published event to {topic}: {event['event_id']}")
            return True

        except httpx.HTTPError as e:
            logger.error(f"Failed to publish event to {topic}: {str(e)}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Unexpected error publishing event: {str(e)}", exc_info=True)
            return False
