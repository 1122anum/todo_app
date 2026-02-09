"""
Conversation model for Phase III AI Chatbot.

Represents a chat session between a user and the AI assistant.
Each conversation maintains independent context and contains multiple messages.
"""
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class Conversation(SQLModel, table=True):
    """
    Conversation entity for AI chatbot.

    Attributes:
        id: Unique identifier for the conversation (TEXT in SQLite)
        user_id: Owner of the conversation (foreign key to users.user_id)
        created_at: Conversation start timestamp
        updated_at: Last message timestamp (auto-updated by trigger)
    """
    __tablename__ = "conversations"

    id: str = Field(primary_key=True)
    user_id: int = Field(foreign_key="users.user_id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """SQLModel configuration."""
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": 1,
                "created_at": "2026-02-05T10:30:00Z",
                "updated_at": "2026-02-05T11:45:00Z"
            }
        }
