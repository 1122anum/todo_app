"""
Chat Service for Phase III AI Chatbot.

Orchestrates AI agent execution, conversation management, and message persistence.
Maintains stateless architecture by fetching conversation context from database.
"""
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from datetime import datetime
import logging
from sqlmodel import Session, select
from ..database import get_session
from ..models.conversation import Conversation
from ..models.message import Message, MessageRole
from ..ai.runner import get_agent_runner
from ..mcp.registry import register_all_tools

logger = logging.getLogger(__name__)


class ChatService:
    """
    Service for managing chat conversations and AI interactions.

    Handles conversation lifecycle, message persistence, and AI agent execution
    while maintaining stateless server architecture.
    """

    def __init__(self):
        """Initialize the chat service."""
        # Ensure MCP tools are registered
        register_all_tools()
        self.agent_runner = get_agent_runner()

    def process_message(
        self,
        user_id: UUID,
        message: str,
        conversation_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Process a user message and generate AI response.

        Args:
            user_id: Authenticated user ID
            message: User's message text
            conversation_id: Optional conversation ID to continue existing conversation

        Returns:
            Dict containing:
                - conversation_id: Conversation UUID
                - response: AI assistant's response
                - tool_calls: List of tools executed
        """
        try:
            with get_session() as session:
                # Get or create conversation
                if conversation_id:
                    conversation = self._get_conversation(session, conversation_id, user_id)
                    if not conversation:
                        return {
                            "error": "Conversation not found or access denied",
                            "code": "NOT_FOUND"
                        }
                else:
                    conversation = self._create_conversation(session, user_id)

                # Fetch conversation history
                conversation_history = self._get_conversation_history(
                    session,
                    conversation.id,
                    user_id
                )

                # Save user message
                self._save_message(
                    session,
                    conversation.id,
                    user_id,
                    MessageRole.USER,
                    message
                )

                # Run AI agent
                agent_response = self.agent_runner.run_conversation(
                    user_message=message,
                    conversation_history=conversation_history,
                    user_id=str(user_id)
                )

                # Save assistant response
                self._save_message(
                    session,
                    conversation.id,
                    user_id,
                    MessageRole.ASSISTANT,
                    agent_response["response"]
                )

                # Commit all changes
                session.commit()

                logger.info(f"Message processed for conversation {conversation.id}")

                return {
                    "conversation_id": str(conversation.id),
                    "response": agent_response["response"],
                    "tool_calls": agent_response.get("tool_calls", [])
                }

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            raise

    def _create_conversation(self, session: Session, user_id: UUID) -> Conversation:
        """
        Create a new conversation for the user.

        Args:
            session: Database session
            user_id: User ID

        Returns:
            Created Conversation instance
        """
        conversation = Conversation(
            id=uuid4(),
            user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(conversation)
        session.flush()  # Get the ID without committing

        logger.info(f"Created conversation {conversation.id} for user {user_id}")
        return conversation

    def _get_conversation(
        self,
        session: Session,
        conversation_id: UUID,
        user_id: UUID
    ) -> Optional[Conversation]:
        """
        Get a conversation by ID with user isolation check.

        Args:
            session: Database session
            conversation_id: Conversation ID
            user_id: User ID (for isolation check)

        Returns:
            Conversation instance or None if not found/unauthorized
        """
        statement = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        )
        conversation = session.exec(statement).first()

        if conversation:
            logger.info(f"Retrieved conversation {conversation_id}")
        else:
            logger.warning(f"Conversation {conversation_id} not found for user {user_id}")

        return conversation

    def _get_conversation_history(
        self,
        session: Session,
        conversation_id: UUID,
        user_id: UUID
    ) -> List[Dict[str, str]]:
        """
        Get conversation message history formatted for AI agent.

        Args:
            session: Database session
            conversation_id: Conversation ID
            user_id: User ID (for isolation check)

        Returns:
            List of messages in format [{role, content}, ...]
        """
        statement = select(Message).where(
            Message.conversation_id == conversation_id,
            Message.user_id == user_id
        ).order_by(Message.created_at.asc())

        messages = session.exec(statement).all()

        history = [
            {
                "role": msg.role.value,
                "content": msg.content
            }
            for msg in messages
        ]

        logger.info(f"Retrieved {len(history)} messages for conversation {conversation_id}")
        return history

    def _save_message(
        self,
        session: Session,
        conversation_id: UUID,
        user_id: UUID,
        role: MessageRole,
        content: str
    ) -> Message:
        """
        Save a message to the database.

        Args:
            session: Database session
            conversation_id: Conversation ID
            user_id: User ID
            role: Message role (user or assistant)
            content: Message content

        Returns:
            Created Message instance
        """
        message = Message(
            id=uuid4(),
            user_id=user_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
            created_at=datetime.utcnow()
        )
        session.add(message)
        session.flush()

        logger.info(f"Saved {role.value} message to conversation {conversation_id}")
        return message

    def get_user_conversations(
        self,
        user_id: UUID,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get user's recent conversations.

        Args:
            user_id: User ID
            limit: Maximum number of conversations to return

        Returns:
            List of conversation summaries
        """
        try:
            with get_session() as session:
                statement = select(Conversation).where(
                    Conversation.user_id == user_id
                ).order_by(Conversation.updated_at.desc()).limit(limit)

                conversations = session.exec(statement).all()

                return [
                    {
                        "id": str(conv.id),
                        "created_at": conv.created_at.isoformat(),
                        "updated_at": conv.updated_at.isoformat()
                    }
                    for conv in conversations
                ]

        except Exception as e:
            logger.error(f"Error fetching conversations: {str(e)}")
            raise


# Global service instance
_chat_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """
    Get or create the global chat service instance.

    Returns:
        ChatService instance
    """
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service
