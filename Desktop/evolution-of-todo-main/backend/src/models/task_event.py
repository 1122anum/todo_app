"""
TaskEvent model for immutable audit trail.

Records all task changes for audit and history tracking.
"""
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import uuid


class TaskEventType(str, Enum):
    """Task event type enumeration."""
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    COMPLETED = "completed"
    UNCOMPLETED = "uncompleted"


class TaskEvent(SQLModel, table=True):
    """
    TaskEvent entity for immutable audit trail.

    Attributes:
        id: Unique event identifier (auto-increment)
        event_id: Event UUID from Kafka (prevents duplicate processing)
        task_id: Associated task ID (may be deleted)
        user_id: User who made the change (foreign key to users.user_id)
        event_type: Type of change (created, updated, deleted, completed, uncompleted)
        changes: JSONB object with field_name: {old_value, new_value}
        metadata: JSONB with source, correlation_id, and other metadata
        timestamp: When the change occurred
    """
    __tablename__ = "task_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        unique=True,
        index=True
    )
    task_id: int = Field(index=True)
    user_id: int = Field(foreign_key="users.user_id", index=True)
    event_type: TaskEventType = Field(index=True)
    changes: Dict[str, Any] = Field(sa_column=Column(JSON))
    metadata: Dict[str, Any] = Field(sa_column=Column(JSON))
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)

    class Config:
        """SQLModel configuration."""
        json_schema_extra = {
            "example": {
                "id": 12345,
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "task_id": 123,
                "user_id": 42,
                "event_type": "updated",
                "changes": {
                    "title": {
                        "old_value": "Buy groceries",
                        "new_value": "Buy groceries and cook dinner"
                    },
                    "priority": {
                        "old_value": "medium",
                        "new_value": "high"
                    }
                },
                "metadata": {
                    "source": "chat_api",
                    "correlation_id": "660e8400-e29b-41d4-a716-446655440001"
                },
                "timestamp": "2026-02-09T10:05:00Z"
            }
        }
