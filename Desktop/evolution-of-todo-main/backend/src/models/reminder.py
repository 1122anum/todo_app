"""
Reminder model for task notifications.

Scheduled notifications to remind users about upcoming tasks.
"""
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class NotificationChannel(str, Enum):
    """Notification channel enumeration."""
    IN_APP = "in_app"
    # Future: EMAIL = "email", PUSH = "push"


class ReminderStatus(str, Enum):
    """Reminder status enumeration."""
    PENDING = "pending"
    SENT = "sent"
    SNOOZED = "snoozed"
    CANCELLED = "cancelled"


class Reminder(SQLModel, table=True):
    """
    Reminder entity for task notifications.

    Attributes:
        id: Unique reminder identifier
        task_id: Associated task (foreign key to tasks.id)
        user_id: Owner of the reminder (foreign key to users.user_id)
        scheduled_time: When to send the reminder
        notification_channel: Notification channel (in_app only in Phase V)
        status: Reminder status (pending, sent, snoozed, cancelled)
        snoozed_until: When to re-trigger if snoozed (optional)
        sent_at: When reminder was actually sent (optional)
        created_at: Reminder creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "reminders"

    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="tasks.id", index=True)
    user_id: int = Field(foreign_key="users.user_id", index=True)
    scheduled_time: datetime = Field(index=True)
    notification_channel: NotificationChannel = Field(default=NotificationChannel.IN_APP)
    status: ReminderStatus = Field(default=ReminderStatus.PENDING, index=True)
    snoozed_until: Optional[datetime] = Field(default=None, index=True)
    sent_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """SQLModel configuration."""
        json_schema_extra = {
            "example": {
                "id": 1,
                "task_id": 123,
                "user_id": 42,
                "scheduled_time": "2026-02-10T16:00:00Z",
                "notification_channel": "in_app",
                "status": "pending",
                "snoozed_until": None,
                "sent_at": None,
                "created_at": "2026-02-09T10:00:00Z",
                "updated_at": "2026-02-09T10:00:00Z"
            }
        }
