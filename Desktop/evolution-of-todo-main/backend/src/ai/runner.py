"""
Agent runner for Phase III AI Chatbot.

Orchestrates the execution of the AI agent with conversation context,
tool calling, and response generation.
"""
import json
import logging
from typing import List, Dict, Any, Optional
from .agent import get_agent
from .prompts import get_system_prompt
from ..mcp.registry import get_tool_registry
from ..mcp.server import get_mcp_server

logger = logging.getLogger(__name__)


class AgentRunner:
    """
    Orchestrates AI agent execution with MCP tools.

    Handles conversation context, tool execution, and response generation
    while maintaining stateless architecture.
    """

    def __init__(self):
        """Initialize the agent runner."""
        self.agent = get_agent(system_prompt=get_system_prompt())
        self.tool_registry = get_tool_registry()
        self.mcp_server = get_mcp_server()

    def run_conversation(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Run a conversation turn with the AI agent.

        Args:
            user_message: Current user message
            conversation_history: Previous messages (list of {role, content})
            user_id: Authenticated user ID

        Returns:
            Dict containing:
                - response: AI assistant's response message
                - tool_calls: List of tools executed with results
                - finish_reason: Completion reason
        """
        try:
            # Get available tools for the agent
            tools = self.tool_registry.get_tools_for_agent()

            # Run the AI agent
            agent_response = self.agent.run(
                user_message=user_message,
                conversation_history=conversation_history,
                tools=tools,
                user_id=user_id
            )

            # Execute any tool calls
            tool_results = []
            if agent_response.get("tool_calls"):
                tool_results = self._execute_tool_calls(
                    agent_response["tool_calls"],
                    user_id
                )

                # If tools were called, run agent again with tool results
                if tool_results:
                    agent_response = self._run_with_tool_results(
                        user_message,
                        conversation_history,
                        agent_response["tool_calls"],
                        tool_results,
                        tools,
                        user_id
                    )

            return {
                "response": agent_response.get("content", ""),
                "tool_calls": tool_results,
                "finish_reason": agent_response.get("finish_reason", "stop")
            }

        except Exception as e:
            logger.error(f"Agent runner error: {str(e)}")
            return {
                "response": "I apologize, but I encountered an error while processing your request. Please try again.",
                "tool_calls": [],
                "finish_reason": "error",
                "error": str(e)
            }

    def _execute_tool_calls(
        self,
        tool_calls: List[Dict[str, Any]],
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Execute MCP tool calls from the AI agent.

        Args:
            tool_calls: List of tool calls from agent
            user_id: Authenticated user ID

        Returns:
            List of tool execution results
        """
        results = []

        for tool_call in tool_calls:
            try:
                function_name = tool_call["function"]["name"]
                arguments_str = tool_call["function"]["arguments"]

                # Parse arguments
                try:
                    arguments = json.loads(arguments_str)
                except json.JSONDecodeError:
                    arguments = {}

                # Execute tool via MCP server
                result = self.mcp_server.execute_tool(
                    name=function_name,
                    user_id=user_id,
                    **arguments
                )

                results.append({
                    "tool": function_name,
                    "parameters": arguments,
                    "result": result,
                    "success": True
                })

                logger.info(f"Tool executed: {function_name}")

            except Exception as e:
                logger.error(f"Tool execution error: {str(e)}")
                results.append({
                    "tool": tool_call["function"]["name"],
                    "parameters": {},
                    "result": {"error": str(e)},
                    "success": False
                })

        return results

    def _run_with_tool_results(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        tool_calls: List[Dict[str, Any]],
        tool_results: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Run agent again with tool execution results.

        Args:
            user_message: Original user message
            conversation_history: Conversation history
            tool_calls: Original tool calls
            tool_results: Tool execution results
            tools: Available tools
            user_id: User ID

        Returns:
            Agent response with tool results incorporated
        """
        # Build messages with tool results
        messages = list(conversation_history)
        messages.append({"role": "user", "content": user_message})

        # Add assistant message with tool calls
        messages.append({
            "role": "assistant",
            "content": "",
            "tool_calls": tool_calls
        })

        # Add tool results
        for i, result in enumerate(tool_results):
            messages.append({
                "role": "tool",
                "tool_call_id": tool_calls[i].get("id", f"call_{i}"),
                "content": json.dumps(result["result"])
            })

        # Run agent with tool results
        return self.agent.run(
            user_message="",  # Empty since we're continuing from tool results
            conversation_history=messages,
            tools=tools,
            user_id=user_id
        )


# Global runner instance
_runner: Optional[AgentRunner] = None


def get_agent_runner() -> AgentRunner:
    """
    Get or create the global agent runner instance.

    Returns:
        AgentRunner instance
    """
    global _runner
    if _runner is None:
        _runner = AgentRunner()
    return _runner


def initialize_agent_runner() -> AgentRunner:
    """
    Initialize the agent runner.

    Returns:
        Configured AgentRunner instance
    """
    global _runner
    _runner = AgentRunner()
    logger.info("Agent runner initialization complete")
    return _runner
