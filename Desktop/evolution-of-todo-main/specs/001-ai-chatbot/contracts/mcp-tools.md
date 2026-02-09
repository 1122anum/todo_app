# MCP Tools Contract Specification

**Feature**: 001-ai-chatbot
**Date**: 2026-02-05
**Version**: 1.0.0

## Overview

This document defines the contract for MCP (Model Context Protocol) tools that serve as the exclusive interface between the AI agent and task data operations. All tools are stateless and enforce user isolation.

## Tool Registry

The following tools are registered with the MCP server and available to the OpenAI Agents SDK:

1. `create_task` - Creates a new todo task
2. `get_tasks` - Retrieves user's tasks with optional filtering
3. `update_task` - Updates task properties or completion status
4. `delete_task` - Deletes a task (returns confirmation prompt)

---

## Tool: create_task

**Purpose**: Creates a new todo task for the authenticated user.

**Parameters**:
```json
{
  "type": "object",
  "properties": {
    "user_id": {
      "type": "string",
      "format": "uuid",
      "description": "User ID (injected by chat service, not from AI)"
    },
    "title": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200,
      "description": "Task title (required)"
    },
    "description": {
      "type": "string",
      "maxLength": 1000,
      "description": "Task description (optional)",
      "default": ""
    }
  },
  "required": ["user_id", "title"]
}
```

**Returns**:
```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean",
      "description": "Whether the operation succeeded"
    },
    "task_id": {
      "type": "string",
      "format": "uuid",
      "description": "ID of the created task"
    },
    "task": {
      "type": "object",
      "description": "Created task details",
      "properties": {
        "id": {"type": "string", "format": "uuid"},
        "title": {"type": "string"},
        "description": {"type": "string"},
        "completed": {"type": "boolean"},
        "created_at": {"type": "string", "format": "date-time"}
      }
    },
    "message": {
      "type": "string",
      "description": "Human-readable success message"
    }
  }
}
```

**Example Request**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Buy groceries",
  "description": "Milk, eggs, bread"
}
```

**Example Response (Success)**:
```json
{
  "success": true,
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "task": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "title": "Buy groceries",
    "description": "Milk, eggs, bread",
    "completed": false,
    "created_at": "2026-02-05T10:30:00Z"
  },
  "message": "Task 'Buy groceries' created successfully"
}
```

**Example Response (Error)**:
```json
{
  "success": false,
  "error": "Title cannot be empty",
  "code": "INVALID_INPUT"
}
```

**Validation Rules**:
- Title must not be empty or whitespace-only
- Title length: 1-200 characters
- Description length: 0-1000 characters
- user_id must be valid UUID

**Error Codes**:
- `INVALID_INPUT`: Invalid parameters (empty title, invalid UUID)
- `DATABASE_ERROR`: Database operation failed

---

## Tool: get_tasks

**Purpose**: Retrieves user's tasks with optional filtering by completion status or search term.

**Parameters**:
```json
{
  "type": "object",
  "properties": {
    "user_id": {
      "type": "string",
      "format": "uuid",
      "description": "User ID (injected by chat service, not from AI)"
    },
    "filter": {
      "type": "string",
      "enum": ["all", "incomplete", "complete"],
      "description": "Filter by completion status",
      "default": "all"
    },
    "search": {
      "type": "string",
      "maxLength": 100,
      "description": "Search term to filter tasks by title/description (optional)"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "description": "Maximum number of tasks to return",
      "default": 50
    }
  },
  "required": ["user_id"]
}
```

**Returns**:
```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean",
      "description": "Whether the operation succeeded"
    },
    "tasks": {
      "type": "array",
      "description": "List of tasks matching the filter",
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "string", "format": "uuid"},
          "title": {"type": "string"},
          "description": {"type": "string"},
          "completed": {"type": "boolean"},
          "created_at": {"type": "string", "format": "date-time"},
          "updated_at": {"type": "string", "format": "date-time"}
        }
      }
    },
    "count": {
      "type": "integer",
      "description": "Number of tasks returned"
    },
    "message": {
      "type": "string",
      "description": "Human-readable message"
    }
  }
}
```

**Example Request (All tasks)**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "filter": "all"
}
```

**Example Request (Search)**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "filter": "incomplete",
  "search": "report"
}
```

**Example Response (Success)**:
```json
{
  "success": true,
  "tasks": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "title": "Buy groceries",
      "description": "Milk, eggs, bread",
      "completed": false,
      "created_at": "2026-02-05T10:30:00Z",
      "updated_at": "2026-02-05T10:30:00Z"
    },
    {
      "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "title": "Finish report",
      "description": "Q4 quarterly report",
      "completed": false,
      "created_at": "2026-02-04T15:20:00Z",
      "updated_at": "2026-02-04T15:20:00Z"
    }
  ],
  "count": 2,
  "message": "Found 2 tasks"
}
```

**Example Response (No tasks)**:
```json
{
  "success": true,
  "tasks": [],
  "count": 0,
  "message": "No tasks found"
}
```

**Validation Rules**:
- user_id must be valid UUID
- filter must be one of: "all", "incomplete", "complete"
- search term limited to 100 characters
- limit must be between 1 and 100

**Error Codes**:
- `INVALID_INPUT`: Invalid parameters
- `DATABASE_ERROR`: Database operation failed

---

## Tool: update_task

**Purpose**: Updates task properties (title, description) or marks task as complete/incomplete.

**Parameters**:
```json
{
  "type": "object",
  "properties": {
    "user_id": {
      "type": "string",
      "format": "uuid",
      "description": "User ID (injected by chat service, not from AI)"
    },
    "task_id": {
      "type": "string",
      "format": "uuid",
      "description": "ID of the task to update (required)"
    },
    "title": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200,
      "description": "New task title (optional)"
    },
    "description": {
      "type": "string",
      "maxLength": 1000,
      "description": "New task description (optional)"
    },
    "completed": {
      "type": "boolean",
      "description": "New completion status (optional)"
    }
  },
  "required": ["user_id", "task_id"]
}
```

**Returns**:
```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean",
      "description": "Whether the operation succeeded"
    },
    "task": {
      "type": "object",
      "description": "Updated task details",
      "properties": {
        "id": {"type": "string", "format": "uuid"},
        "title": {"type": "string"},
        "description": {"type": "string"},
        "completed": {"type": "boolean"},
        "updated_at": {"type": "string", "format": "date-time"}
      }
    },
    "message": {
      "type": "string",
      "description": "Human-readable success message"
    }
  }
}
```

**Example Request (Mark complete)**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "completed": true
}
```

**Example Request (Update title)**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "title": "Buy groceries and household items"
}
```

**Example Response (Success)**:
```json
{
  "success": true,
  "task": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "title": "Buy groceries",
    "description": "Milk, eggs, bread",
    "completed": true,
    "updated_at": "2026-02-05T11:45:00Z"
  },
  "message": "Task 'Buy groceries' marked as complete"
}
```

**Example Response (Error - Not Found)**:
```json
{
  "success": false,
  "error": "Task not found or you don't have permission to update it",
  "code": "NOT_FOUND"
}
```

**Validation Rules**:
- At least one of title, description, or completed must be provided
- If title provided, must not be empty or whitespace-only
- Task must belong to the authenticated user (user_id)
- task_id must be valid UUID

**Error Codes**:
- `INVALID_INPUT`: Invalid parameters (empty title, invalid UUID, no fields to update)
- `NOT_FOUND`: Task not found or doesn't belong to user
- `DATABASE_ERROR`: Database operation failed

---

## Tool: delete_task

**Purpose**: Deletes a task. Returns confirmation prompt for AI to present to user before actual deletion.

**Parameters**:
```json
{
  "type": "object",
  "properties": {
    "user_id": {
      "type": "string",
      "format": "uuid",
      "description": "User ID (injected by chat service, not from AI)"
    },
    "task_id": {
      "type": "string",
      "format": "uuid",
      "description": "ID of the task to delete (required)"
    },
    "confirmed": {
      "type": "boolean",
      "description": "Whether user has confirmed deletion",
      "default": false
    }
  },
  "required": ["user_id", "task_id"]
}
```

**Returns**:
```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean",
      "description": "Whether the operation succeeded"
    },
    "requires_confirmation": {
      "type": "boolean",
      "description": "Whether confirmation is needed before deletion"
    },
    "task": {
      "type": "object",
      "description": "Task details (for confirmation prompt)",
      "properties": {
        "id": {"type": "string", "format": "uuid"},
        "title": {"type": "string"},
        "description": {"type": "string"}
      }
    },
    "message": {
      "type": "string",
      "description": "Human-readable message or confirmation prompt"
    }
  }
}
```

**Example Request (Initial - no confirmation)**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "confirmed": false
}
```

**Example Response (Confirmation needed)**:
```json
{
  "success": false,
  "requires_confirmation": true,
  "task": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "title": "Buy groceries",
    "description": "Milk, eggs, bread"
  },
  "message": "Are you sure you want to delete the task 'Buy groceries'? This action cannot be undone."
}
```

**Example Request (With confirmation)**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "confirmed": true
}
```

**Example Response (Deleted)**:
```json
{
  "success": true,
  "requires_confirmation": false,
  "message": "Task 'Buy groceries' has been deleted"
}
```

**Example Response (Error - Not Found)**:
```json
{
  "success": false,
  "error": "Task not found or you don't have permission to delete it",
  "code": "NOT_FOUND"
}
```

**Validation Rules**:
- task_id must be valid UUID
- Task must belong to the authenticated user (user_id)
- First call (confirmed=false) returns confirmation prompt
- Second call (confirmed=true) performs actual deletion

**Error Codes**:
- `INVALID_INPUT`: Invalid parameters (invalid UUID)
- `NOT_FOUND`: Task not found or doesn't belong to user
- `DATABASE_ERROR`: Database operation failed

---

## Common Patterns

### User Isolation

All tools enforce user isolation by:
1. Accepting `user_id` parameter (injected by chat service, not from AI)
2. Filtering all database queries by `user_id`
3. Returning `NOT_FOUND` error if task doesn't belong to user

**Implementation**:
```python
# Chat service injects user_id before calling MCP tool
tool_result = mcp_tool.execute(
    user_id=authenticated_user_id,  # From auth token
    **ai_provided_parameters
)
```

### Error Handling

All tools return structured responses with:
- `success` boolean indicating operation status
- `message` string with human-readable description
- `error` and `code` fields for failures

**AI Agent Behavior**:
- On success: Present friendly confirmation to user
- On error: Translate error code to user-friendly message
- On NOT_FOUND: Suggest alternatives or ask for clarification

### Idempotency

- `create_task`: Not idempotent (creates new task each time)
- `get_tasks`: Idempotent (read-only operation)
- `update_task`: Idempotent (same update produces same result)
- `delete_task`: Idempotent (deleting non-existent task returns NOT_FOUND)

---

## Testing

### Unit Tests

Each tool should have unit tests covering:
- Valid inputs with expected outputs
- Invalid inputs with appropriate error codes
- User isolation (accessing other user's tasks)
- Edge cases (empty strings, max lengths, special characters)

### Integration Tests

Test MCP tools with actual database:
- Create, retrieve, update, delete workflow
- Concurrent operations on same task
- User isolation across multiple users
- Error scenarios (database unavailable, constraint violations)

### AI Agent Tests

Test tools through AI agent:
- Natural language commands map to correct tool calls
- Tool results are presented clearly to users
- Error messages are user-friendly
- Confirmation flows work correctly (delete)

---

## Security Considerations

1. **User Isolation**: All tools enforce user_id filtering at database level
2. **Input Validation**: All inputs validated before database operations
3. **SQL Injection**: Use parameterized queries (SQLModel ORM)
4. **Rate Limiting**: Enforce at API level (not tool level)
5. **Audit Logging**: Log all tool executions with user_id and parameters

---

## Performance Considerations

1. **Database Indexes**: Ensure indexes on (user_id, completed) and (user_id, created_at)
2. **Query Limits**: get_tasks limited to 100 results maximum
3. **Search Performance**: Use database LIKE queries (consider full-text search for future)
4. **Connection Pooling**: Reuse database connections across tool calls

---

## Future Enhancements (Out of Scope for Phase III)

- Batch operations (create/update/delete multiple tasks)
- Task priorities and tags
- Due dates and reminders
- Task dependencies
- Subtasks
- Task sharing between users
- Advanced search (full-text, filters)

---

## References

- MCP Protocol Specification: https://modelcontextprotocol.io/
- OpenAI Agents SDK Tool Calling: https://platform.openai.com/docs/agents/tools
- Feature Specification: `specs/001-ai-chatbot/spec.md`
- Data Model: `specs/001-ai-chatbot/data-model.md`
