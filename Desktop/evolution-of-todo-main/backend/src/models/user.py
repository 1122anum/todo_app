"""
User model for authentication and authorization.

Represents a user account in the system.
"""
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class User(SQLModel, table=True):
    """
    User entity for authentication.

    Attributes:
        user_id: Unique identifier for the user (auto-increment primary key)
        email: User's email address (unique)
        username: User's display name
        hashed_password: Bcrypt hashed password
        created_at: Account creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "users"

    user_id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    username: Optional[str] = Field(default=None, max_length=100)
    hashed_password: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """SQLModel configuration."""
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "email": "user@example.com",
                "username": "johndoe",
                "created_at": "2026-02-05T10:30:00Z",
                "updated_at": "2026-02-05T10:30:00Z"
            }
        }
