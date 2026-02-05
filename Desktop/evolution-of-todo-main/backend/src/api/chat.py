"""
Chat API endpoint for Phase III AI Chatbot.

Provides POST /api/{user_id}/chat endpoint for conversational task management.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging
from ..services.chat_service import get_chat_service
from ..middleware.auth import get_current_user
from ..models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., min_length=1, max_length=1000, description="User message")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID to continue")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Create a task to buy groceries",
                "conversation_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7"
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    conversation_id: str = Field(..., description="Conversation ID")
    response: str = Field(..., description="AI assistant's response")
    tool_calls: List[Dict[str, Any]] = Field(default=[], description="Tools executed")

    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                "response": "I've created a task titled 'Buy groceries' for you.",
                "tool_calls": [
                    {
                        "tool": "create_task",
                        "parameters": {"title": "Buy groceries"},
                        "result": {"success": True, "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"}
                    }
                ]
            }
        }


@router.post("/{user_id}/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat(
    user_id: str,
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
) -> ChatResponse:
    """
    Process a chat message and return AI response.

    This endpoint:
    1. Validates user authentication and authorization
    2. Fetches or creates conversation
    3. Processes message through AI agent with MCP tools
    4. Persists conversation and messages
    5. Returns AI response with tool execution results

    Args:
        user_id: User ID from path (must match authenticated user)
        request: Chat request with message and optional conversation_id
        current_user: Authenticated user from middleware

    Returns:
        ChatResponse with conversation_id, AI response, and tool_calls

    Raises:
        HTTPException: 400 (invalid input), 401 (unauthorized), 403 (forbidden), 500 (server error)
    """
    try:
        # Validate user_id matches authenticated user
        if str(current_user.id) != user_id:
            logger.warning(f"User {current_user.id} attempted to access chat for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this conversation"
            )

        # Validate message
        if not request.message or not request.message.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty"
            )

        if len(request.message) > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message exceeds maximum length of 1000 characters"
            )

        # Parse conversation_id if provided
        conversation_id = None
        if request.conversation_id:
            try:
                conversation_id = UUID(request.conversation_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid conversation_id format"
                )

        # Process message through chat service
        chat_service = get_chat_service()
        result = chat_service.process_message(
            user_id=UUID(user_id),
            message=request.message.strip(),
            conversation_id=conversation_id
        )

        # Check for errors in result
        if "error" in result:
            if result.get("code") == "NOT_FOUND":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result["error"]
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result["error"]
                )

        logger.info(f"Chat message processed successfully for user {user_id}")

        return ChatResponse(
            conversation_id=result["conversation_id"],
            response=result["response"],
            tool_calls=result.get("tool_calls", [])
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your request. Please try again."
        )


@router.get("/{user_id}/conversations", status_code=status.HTTP_200_OK)
async def get_conversations(
    user_id: str,
    current_user: User = Depends(get_current_user),
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Get user's recent conversations.

    Args:
        user_id: User ID from path
        current_user: Authenticated user
        limit: Maximum number of conversations to return

    Returns:
        List of conversation summaries

    Raises:
        HTTPException: 403 (forbidden), 500 (server error)
    """
    try:
        # Validate user_id matches authenticated user
        if str(current_user.id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access these conversations"
            )

        chat_service = get_chat_service()
        conversations = chat_service.get_user_conversations(
            user_id=UUID(user_id),
            limit=limit
        )

        return conversations

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error fetching conversations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching conversations"
        )
