"""
AI Agent setup for Phase III AI Chatbot using OpenAI Agents SDK.

This module initializes the OpenAI agent that handles natural language
processing and tool calling for conversational task management.
"""
import os
from typing import List, Dict, Any, Optional
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)


class TodoAgent:
    """
    AI Agent for conversational task management.

    Uses OpenAI Agents SDK to process natural language and call MCP tools.
    Maintains stateless architecture - conversation context passed per request.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None
    ):
        """
        Initialize the AI agent.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use (defaults to OPENAI_MODEL env var or gpt-4)
            system_prompt: System prompt for agent behavior
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set in environment")

        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4")
        self.system_prompt = system_prompt
        self.client = OpenAI(api_key=self.api_key)

        logger.info(f"AI Agent initialized with model: {self.model}")

    def run(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Run the AI agent with a user message and conversation context.

        Args:
            user_message: Current user message
            conversation_history: Previous messages in conversation
            tools: Available MCP tools in OpenAI format
            user_id: Authenticated user ID (for tool execution)

        Returns:
            Dict containing:
                - content: AI response message
                - tool_calls: List of tools called
                - finish_reason: Completion reason
        """
        # Build messages array with system prompt and history
        messages = []

        if self.system_prompt:
            messages.append({
                "role": "system",
                "content": self.system_prompt
            })

        # Add conversation history
        messages.extend(conversation_history)

        # Add current user message
        messages.append({
            "role": "user",
            "content": user_message
        })

        try:
            # Call OpenAI API with tools
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )

            # Extract response
            choice = response.choices[0]
            message = choice.message

            result = {
                "content": message.content or "",
                "tool_calls": [],
                "finish_reason": choice.finish_reason
            }

            # Process tool calls if any
            if message.tool_calls:
                result["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]

            logger.info(f"AI response generated: {len(result['content'])} chars, {len(result['tool_calls'])} tool calls")
            return result

        except Exception as e:
            logger.error(f"AI agent error: {str(e)}")
            raise


# Global agent instance
_agent: Optional[TodoAgent] = None


def get_agent(system_prompt: Optional[str] = None) -> TodoAgent:
    """
    Get or create the global AI agent instance.

    Args:
        system_prompt: System prompt (only used on first initialization)

    Returns:
        TodoAgent instance
    """
    global _agent
    if _agent is None:
        _agent = TodoAgent(system_prompt=system_prompt)
    return _agent


def initialize_agent(system_prompt: str) -> TodoAgent:
    """
    Initialize the AI agent with system prompt.

    Args:
        system_prompt: System prompt defining agent behavior

    Returns:
        Configured TodoAgent instance
    """
    global _agent
    _agent = TodoAgent(system_prompt=system_prompt)
    logger.info("AI Agent initialization complete")
    return _agent
