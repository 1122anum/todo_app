"""
RecurrencePattern model for recurring task support.

Defines how recurring tasks repeat (daily, weekly, monthly patterns).
"""
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON
from datetime import datetime
from typing import Optional, List
from enum import Enum


class RecurrenceFrequency(str, Enum):
    """Recurrence frequency enumeration."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class RecurrencePattern(SQLModel, table=True):
    """
    RecurrencePattern entity for recurring task generation.

    Attributes:
        id: Unique pattern identifier
        user_id: Owner of the pattern (foreign key to users.user_id)
        frequency: Recurrence frequency (daily, weekly, monthly, custom)
        interval: Repeat every N units (e.g., every 2 weeks)
        days_of_week: Days of week for weekly patterns (0=Sunday, 6=Saturday)
        day_of_month: Day of month (1-31) for monthly patterns
        start_date: When to start generating instances
        end_date: When to stop generating instances (optional)
        last_generated_at: Last time an instance was generated
        created_at: Pattern creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "recurrence_patterns"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.user_id", index=True)
    frequency: RecurrenceFrequency = Field()
    interval: int = Field(default=1, ge=1)

    # Pattern-specific fields
    days_of_week: Optional[List[int]] = Field(
        default=None,
        sa_column=Column(JSON)
    )
    day_of_month: Optional[int] = Field(default=None, ge=1, le=31)

    # Schedule
    start_date: datetime = Field()
    end_date: Optional[datetime] = Field(default=None)
    last_generated_at: Optional[datetime] = Field(default=None, index=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """SQLModel configuration."""
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": 42,
                "frequency": "weekly",
                "interval": 1,
                "days_of_week": [1, 3, 5],
                "day_of_month": None,
                "start_date": "2026-02-09T09:00:00Z",
                "end_date": None,
                "last_generated_at": "2026-02-09T09:00:00Z",
                "created_at": "2026-02-09T09:00:00Z",
                "updated_at": "2026-02-09T09:00:00Z"
            }
        }
