"""
Tag model for task categorization.

Custom labels for organizing and filtering tasks.
"""
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class Tag(SQLModel, table=True):
    """
    Tag entity for task categorization.

    Attributes:
        id: Unique tag identifier
        user_id: Owner of the tag (foreign key to users.user_id)
        name: Tag name (unique per user, 1-50 chars, alphanumeric + spaces/hyphens)
        color: Hex color code for visual display (e.g., #FF5733)
        usage_count: Number of tasks currently using this tag
        created_at: Tag creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "tags"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.user_id", index=True)
    name: str = Field(max_length=50, index=True)
    color: Optional[str] = Field(default=None, max_length=7, regex=r"^#[0-9A-Fa-f]{6}$")
    usage_count: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """SQLModel configuration."""
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": 42,
                "name": "personal",
                "color": "#FF5733",
                "usage_count": 5,
                "created_at": "2026-02-09T10:00:00Z",
                "updated_at": "2026-02-09T10:00:00Z"
            }
        }
