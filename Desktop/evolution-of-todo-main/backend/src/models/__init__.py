"""
Models package for Todo application.

Exports all database models for Phase II and Phase III.
"""
# Phase II models (must be imported first for foreign key resolution)
from .user import User
from .todo import Todo

# Phase III models
from .conversation import Conversation
from .message import Message, MessageRole

__all__ = [
    # Phase II
    "User",
    "Todo",
    # Phase III
    "Conversation",
    "Message",
    "MessageRole",
]
