# Data Model: AI-Powered Todo Chatbot

**Feature**: 001-ai-chatbot
**Date**: 2026-02-05
**Phase**: 1 - Design

## Overview

This document defines the data entities for Phase III AI Chatbot feature. The data model extends the existing Phase II schema with two new entities (Conversation and Message) while reusing the existing Task entity.

## Entity Relationship Diagram

```
User (Phase II)
  |
  ├─── 1:N ──> Task (Phase II - existing)
  |
  └─── 1:N ──> Conversation (Phase III - new)
                  |
                  └─── 1:N ──> Message (Phase III - new)
```

## Entities

### Task (Existing - Phase II)

**Purpose**: Represents a todo item that users can create, view, update, and complete.

**Source**: Existing entity from Phase II, no changes required for Phase III.

**Attributes**:
- `id` (UUID, Primary Key): Unique identifier for the task
- `user_id` (UUID, Foreign Key → User): Owner of the task
- `title` (String, Required, Max 200): Task title
- `description` (String, Optional, Max 1000): Detailed task description
- `completed` (Boolean, Default: false): Task completion status
- `created_at` (Timestamp, Auto): Task creation timestamp
- `updated_at` (Timestamp, Auto): Last modification timestamp

**Indexes**:
- Primary: `id`
- Foreign Key: `user_id`
- Composite: `(user_id, completed)` for filtering user's incomplete/complete tasks
- Composite: `(user_id, created_at)` for chronological ordering

**Validation Rules**:
- `title` must not be empty or whitespace-only
- `user_id` must reference valid user
- `completed` defaults to false on creation

**Relationships**:
- Belongs to: User (1:N)
- Referenced by: MCP tools (create_task, get_tasks, update_task, delete_task)

---

### Conversation (New - Phase III)

**Purpose**: Represents a chat session between a user and the AI assistant. Each conversation maintains independent context and contains multiple messages.

**Attributes**:
- `id` (UUID, Primary Key): Unique identifier for the conversation
- `user_id` (UUID, Foreign Key → User): Owner of the conversation
- `created_at` (Timestamp, Auto): Conversation start timestamp
- `updated_at` (Timestamp, Auto): Last message timestamp

**Indexes**:
- Primary: `id`
- Foreign Key: `user_id`
- Composite: `(user_id, updated_at DESC)` for listing user's recent conversations

**Validation Rules**:
- `user_id` must reference valid user
- `id` must be unique across all conversations
- `updated_at` automatically updates when new message is added

**Relationships**:
- Belongs to: User (1:N)
- Has many: Message (1:N)

**Business Rules**:
- Users can have unlimited conversations
- Conversations are never automatically deleted (retention policy deferred to future phase)
- Each conversation maintains independent context (messages from one conversation don't affect another)
- Empty conversations (no messages) are allowed (created when user starts new chat)

**SQLModel Definition**:
```python
from sqlmodel import SQLModel, Field
from datetime import datetime
from uuid import UUID, uuid4

class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships (not stored in DB, for ORM navigation)
    # messages: List["Message"] = Relationship(back_populates="conversation")
```

---

### Message (New - Phase III)

**Purpose**: Represents a single message in a conversation. Messages can be from the user or the AI assistant and are ordered chronologically within a conversation.

**Attributes**:
- `id` (UUID, Primary Key): Unique identifier for the message
- `user_id` (UUID, Foreign Key → User): Owner of the conversation (denormalized for query efficiency)
- `conversation_id` (UUID, Foreign Key → Conversation): Parent conversation
- `role` (Enum: "user" | "assistant", Required): Message sender role
- `content` (String, Required, Max 10000): Message text content
- `created_at` (Timestamp, Auto): Message creation timestamp

**Indexes**:
- Primary: `id`
- Foreign Key: `user_id`
- Foreign Key: `conversation_id`
- Composite: `(conversation_id, created_at ASC)` for chronological message ordering
- Composite: `(user_id, conversation_id)` for user isolation enforcement

**Validation Rules**:
- `content` must not be empty or whitespace-only
- `content` length limited to 10000 characters (allows for long AI responses)
- `role` must be either "user" or "assistant"
- `user_id` must match the conversation's user_id (enforced at application level)
- `conversation_id` must reference valid conversation

**Relationships**:
- Belongs to: User (1:N)
- Belongs to: Conversation (1:N)

**Business Rules**:
- Messages are immutable once created (no updates or edits)
- Messages are ordered chronologically within a conversation (by `created_at`)
- User messages are saved before AI processing
- Assistant messages are saved after AI response is generated
- Messages are never deleted individually (only when conversation is deleted, if implemented in future)
- User isolation: Users can only access messages from their own conversations

**SQLModel Definition**:
```python
from sqlmodel import SQLModel, Field, Enum as SQLEnum
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"

class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    conversation_id: UUID = Field(foreign_key="conversations.id", index=True)
    role: MessageRole = Field(sa_column=SQLEnum(MessageRole))
    content: str = Field(max_length=10000)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships (not stored in DB, for ORM navigation)
    # conversation: Conversation = Relationship(back_populates="messages")
```

---

## Database Schema (SQL)

```sql
-- Conversations table (new)
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_user_updated ON conversations(user_id, updated_at DESC);

-- Messages table (new)
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL CHECK (LENGTH(content) > 0 AND LENGTH(content) <= 10000),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_messages_user_id ON messages(user_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_conversation_created ON messages(conversation_id, created_at ASC);
CREATE INDEX idx_messages_user_conversation ON messages(user_id, conversation_id);

-- Trigger to update conversation.updated_at when message is added
CREATE OR REPLACE FUNCTION update_conversation_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations
    SET updated_at = NEW.created_at
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_conversation_timestamp
AFTER INSERT ON messages
FOR EACH ROW
EXECUTE FUNCTION update_conversation_timestamp();
```

---

## Migration Strategy

**Phase II → Phase III Migration**:

1. **No changes to existing tables**: Task and User tables remain unchanged
2. **Add new tables**: Create Conversations and Messages tables
3. **No data migration needed**: Phase III starts with empty conversation/message tables
4. **Backward compatibility**: Phase II functionality (task CRUD via REST API) continues to work unchanged

**Migration Script** (`backend/migrations/003_add_conversations.sql`):
```sql
-- Migration: Add Conversation and Message tables for Phase III AI Chatbot
-- Date: 2026-02-05
-- Depends on: 002_add_tasks.sql (Phase II)

BEGIN;

-- Create conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user_updated ON conversations(user_id, updated_at DESC);

-- Create messages table
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL CHECK (LENGTH(content) > 0 AND LENGTH(content) <= 10000),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_created ON messages(conversation_id, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_messages_user_conversation ON messages(user_id, conversation_id);

-- Create trigger to update conversation.updated_at
CREATE OR REPLACE FUNCTION update_conversation_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations
    SET updated_at = NEW.created_at
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_conversation_timestamp
AFTER INSERT ON messages
FOR EACH ROW
EXECUTE FUNCTION update_conversation_timestamp();

COMMIT;
```

**Rollback Script** (`backend/migrations/003_add_conversations_rollback.sql`):
```sql
-- Rollback: Remove Conversation and Message tables
BEGIN;

DROP TRIGGER IF EXISTS trigger_update_conversation_timestamp ON messages;
DROP FUNCTION IF EXISTS update_conversation_timestamp();
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS conversations CASCADE;

COMMIT;
```

---

## Query Patterns

### Common Queries

**1. Get user's recent conversations**:
```sql
SELECT id, created_at, updated_at
FROM conversations
WHERE user_id = $1
ORDER BY updated_at DESC
LIMIT 20;
```

**2. Get conversation messages (chronological)**:
```sql
SELECT id, role, content, created_at
FROM messages
WHERE conversation_id = $1 AND user_id = $2
ORDER BY created_at ASC;
```

**3. Create new conversation**:
```sql
INSERT INTO conversations (user_id)
VALUES ($1)
RETURNING id, created_at, updated_at;
```

**4. Add message to conversation**:
```sql
INSERT INTO messages (user_id, conversation_id, role, content)
VALUES ($1, $2, $3, $4)
RETURNING id, created_at;
```

**5. Get conversation with message count**:
```sql
SELECT c.id, c.created_at, c.updated_at, COUNT(m.id) as message_count
FROM conversations c
LEFT JOIN messages m ON m.conversation_id = c.id
WHERE c.user_id = $1
GROUP BY c.id
ORDER BY c.updated_at DESC;
```

---

## Performance Considerations

**Indexes**:
- All foreign keys indexed for join performance
- Composite indexes for common query patterns (user + timestamp, conversation + timestamp)
- User isolation queries benefit from `(user_id, conversation_id)` composite index

**Query Optimization**:
- Conversation history queries limited to single conversation (indexed on conversation_id)
- Message ordering uses indexed `created_at` column
- User's conversation list uses indexed `updated_at DESC` for recent-first ordering

**Scalability**:
- Conversations and messages grow linearly with user activity
- No cross-user queries (all queries filtered by user_id)
- Potential optimization: Archive old conversations (>6 months inactive) to separate table (deferred to future phase)

**Estimated Storage**:
- Average message: ~200 bytes (content) + ~100 bytes (metadata) = 300 bytes
- 100 messages per conversation: 30 KB
- 1000 users × 10 conversations × 100 messages = 300 MB (manageable for Phase III)

---

## Data Integrity

**Constraints**:
- Foreign key constraints ensure referential integrity (user_id, conversation_id)
- Check constraints enforce valid role values and content length
- NOT NULL constraints on required fields
- CASCADE DELETE: Deleting user deletes all conversations and messages

**Application-Level Validation**:
- User isolation: All queries must filter by authenticated user's user_id
- Content sanitization: Validate and sanitize message content before storage
- Role validation: Ensure role matches expected sender (user vs. assistant)

**Audit Trail**:
- All messages immutable (no updates/deletes)
- Timestamps provide chronological audit trail
- Consider adding `tool_calls` JSONB column to messages for debugging (deferred to implementation)

---

## Future Considerations (Out of Scope for Phase III)

- **Message Reactions**: Add reactions/feedback table for user feedback on AI responses
- **Conversation Metadata**: Add title, summary, or tags to conversations
- **Message Attachments**: Support file attachments in messages
- **Conversation Sharing**: Enable sharing conversations between users
- **Conversation Export**: Export conversation history as JSON/PDF
- **Message Search**: Full-text search across message content
- **Conversation Archival**: Archive old conversations to cold storage

---

## References

- Phase III Constitution: `.specify/memory/constitution.md`
- Feature Specification: `specs/001-ai-chatbot/spec.md`
- Research Document: `specs/001-ai-chatbot/research.md`
- SQLModel Documentation: https://sqlmodel.tiangolo.com/
- PostgreSQL UUID Functions: https://www.postgresql.org/docs/current/functions-uuid.html
