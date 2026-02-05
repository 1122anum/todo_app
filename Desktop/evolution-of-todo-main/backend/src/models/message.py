"""
Message model for Phase III AI Chatbot.

Represents a single message in a conversation between user and AI assistant.
Messages are immutable once created and ordered chronologically.
"""
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Enum as SQLEnum
from datetime import datetime
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
        id: Unique identifier for the message (TEXT in SQLite)
        user_id: Owner of the conversation (foreign key to users.user_id)
        conversation_id: Parent conversation (foreign key to conversations.id)
        role: Message sender role (user or assistant)
        content: Message text content (max 10000 characters)
        created_at: Message creation timestamp
    """
    __tablename__ = "messages"

    id: str = Field(primary_key=True)
    user_id: int = Field(foreign_key="users.user_id", index=True)
    conversation_id: str = Field(foreign_key="conversations.id", index=True)
    role: MessageRole = Field(sa_column=Column(SQLEnum(MessageRole, values_callable=lambda x: [e.value for e in x])))
    content: str = Field(max_length=10000)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """SQLModel configuration."""
        json_schema_extra = {
            "example": {
                "id": "msg-a1b2c3d4",
                "user_id": 1,
                "conversation_id": "conv-550e8400",
                "role": "user",
                "content": "Create a task to buy groceries",
                "created_at": "2026-02-05T10:30:00Z"
            }
        }
