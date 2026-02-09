"""
Task model for event-driven todo platform (Phase V).

Represents a task with advanced features: priority, due dates, tags, recurrence.
"""
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import ARRAY, String
from datetime import datetime
from typing import Optional, List
from enum import Enum


class TaskPriority(str, Enum):
    """Task priority enumeration."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Task(SQLModel, table=True):
    """
    Task entity with event-driven architecture support.

    Attributes:
        id: Unique identifier for the task (auto-increment primary key)
        user_id: Owner of the task (foreign key to users.user_id)
        title: Task title (1-255 characters)
        description: Task description (optional, max 2000 characters)
        completed: Completion status (boolean)
        priority: Task priority (high, medium, low)
        due_date: When task is due (optional)
        tags: Array of tag names for categorization (max 10 tags)
        recurrence_pattern_id: Link to recurrence pattern (if recurring)
        is_recurring_instance: True if generated from recurrence pattern
        parent_task_id: Link to parent recurring task (if instance)
        created_at: Task creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.user_id", index=True)
    title: str = Field(max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    completed: bool = Field(default=False)

    # Phase V: Advanced features
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    due_date: Optional[datetime] = Field(default=None, index=True)
    tags: List[str] = Field(default_factory=list, sa_column=Column(ARRAY(String(50))))

    # Phase V: Recurrence support
    recurrence_pattern_id: Optional[int] = Field(
        default=None,
        foreign_key="recurrence_patterns.id",
        index=True
    )
    is_recurring_instance: bool = Field(default=False)
    parent_task_id: Optional[int] = Field(
        default=None,
        foreign_key="tasks.id",
        index=True
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """SQLModel configuration."""
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "title": "Buy groceries",
                "description": "Milk, eggs, bread",
                "completed": False,
                "priority": "high",
                "due_date": "2026-02-10T17:00:00Z",
                "tags": ["personal", "shopping"],
                "recurrence_pattern_id": None,
                "is_recurring_instance": False,
                "parent_task_id": None,
                "created_at": "2026-02-09T10:00:00Z",
                "updated_at": "2026-02-09T10:00:00Z"
            }
        }


# Alias for backward compatibility
Todo = Task
