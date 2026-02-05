"""
Create Task MCP Tool for Phase III AI Chatbot.

Provides the create_task tool that allows the AI agent to create new tasks
through natural language conversation.
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class CreateTaskTool:
    """
    MCP tool for creating tasks.

    Stateless tool that creates a new task for the authenticated user.
    Enforces user isolation and validates inputs.
    """

    def execute(self, user_id: int, title: str, description: str = "") -> Dict[str, Any]:
        """
        Create a new task for the user.

        Args:
            user_id: Authenticated user ID (injected by chat service)
            title: Task title (required, 1-200 characters)
            description: Task description (optional, max 1000 characters)

        Returns:
            Dict containing:
                - success: Boolean indicating operation success
                - task_id: ID of created task
                - task: Task details
                - message: Human-readable success message
        """
        try:
            # Validate inputs
            if not title or not title.strip():
                return {
                    "success": False,
                    "error": "Title cannot be empty",
                    "code": "INVALID_INPUT"
                }

            if len(title) > 200:
                return {
                    "success": False,
                    "error": "Title cannot exceed 200 characters",
                    "code": "INVALID_INPUT"
                }

            if len(description) > 1000:
                return {
                    "success": False,
                    "error": "Description cannot exceed 1000 characters",
                    "code": "INVALID_INPUT"
                }

            # Import dependencies (lazy import to avoid circular dependencies)
            from ...services.todo_service import TodoService
            from ...database import get_session_context

            # Create task using existing Phase II service with proper session management
            with get_session_context() as session:
                task = TodoService.create_todo(
                    session=session,
                    user_id=user_id,
                    title=title.strip(),
                    description=description.strip() if description else ""
                )

            logger.info(f"Task created via MCP tool: {task.todo_id} for user {user_id}")

            return {
                "success": True,
                "task_id": str(task.todo_id),
                "task": {
                    "id": str(task.todo_id),
                    "title": task.title,
                    "description": task.description,
                    "completed": task.completed,
                    "created_at": task.created_at.isoformat()
                },
                "message": f"Task '{title}' created successfully"
            }

        except ValueError as e:
            logger.error(f"Validation error in create_task: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "code": "INVALID_INPUT"
            }

        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            return {
                "success": False,
                "error": "Failed to create task",
                "code": "DATABASE_ERROR"
            }


# Tool metadata for OpenAI Agents SDK
create_task_metadata = {
    "description": "Creates a new todo task for the user with a title and optional description",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Task title (required, 1-200 characters)",
                "minLength": 1,
                "maxLength": 200
            },
            "description": {
                "type": "string",
                "description": "Task description (optional, max 1000 characters)",
                "maxLength": 1000,
                "default": ""
            }
        },
        "required": ["title"]
    }
}
