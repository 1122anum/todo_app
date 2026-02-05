"""
Message model for Phase III AI Chatbot.

Represents a single message in a conversation between user and AI assistant.
Messages are immutable once created and ordered chronologically.
"""
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Enum as SQLEnum
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum
from typing import Optional


class MessageRole(str, Enum):
    """Message sender role."""
    USER = "user"
    ASSISTANT = "assistant"


class Message(SQLModel, table=True):
    """
    Message entity for AI chatbot conversations.

    Attributes:
        id: Unique identifier for the message
        user_id: Owner of the conversation (denormalized for query efficiency)
        conversation_id: Parent conversation
        role: Message sender role (user or assistant)
        content: Message text content (max 10000 characters)
        created_at: Message creation timestamp
    """
    __tablename__ = "messages"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    conversation_id: UUID = Field(foreign_key="conversations.id", index=True)
    role: MessageRole = Field(sa_column=Column(SQLEnum(MessageRole)))
    content: str = Field(max_length=10000)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """SQLModel configuration."""
        json_schema_extra = {
            "example": {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "conversation_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                "role": "user",
                "content": "Create a task to buy groceries",
                "created_at": "2026-02-05T10:30:00Z"
            }
        }
