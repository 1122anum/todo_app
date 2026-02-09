"""
MCP (Model Context Protocol) Server initialization for Phase III AI Chatbot.

This module initializes the MCP server that provides tools for the AI agent
to interact with task data. All AI-to-data operations go through MCP tools.
"""
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class MCPServer:
    """
    MCP Server for AI Chatbot tool integration.

    Provides stateless tools for task operations that the AI agent can call.
    Enforces user isolation and maintains stateless architecture.
    """

    def __init__(self, port: Optional[int] = None):
        """
        Initialize MCP server.

        Args:
            port: Server port (defaults to MCP_SERVER_PORT from env)
        """
        self.port = port or int(os.getenv("MCP_SERVER_PORT", "8001"))
        self.tools = {}
        logger.info(f"MCP Server initialized on port {self.port}")

    def register_tool(self, name: str, tool_instance):
        """
        Register an MCP tool with the server.

        Args:
            name: Tool name (e.g., "create_task")
            tool_instance: Tool instance implementing execute() method
        """
        self.tools[name] = tool_instance
        logger.info(f"Registered MCP tool: {name}")

    def get_tool(self, name: str):
        """
        Get a registered tool by name.

        Args:
            name: Tool name

        Returns:
            Tool instance or None if not found
        """
        return self.tools.get(name)

    def list_tools(self):
        """
        List all registered tools.

        Returns:
            List of tool names
        """
        return list(self.tools.keys())

    def execute_tool(self, name: str, user_id: str, **kwargs):
        """
        Execute a tool with given parameters.

        Args:
            name: Tool name
            user_id: Authenticated user ID (injected by chat service)
            **kwargs: Tool-specific parameters

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool not found
        """
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")

        # Inject user_id for user isolation
        return tool.execute(user_id=user_id, **kwargs)


# Global MCP server instance
_mcp_server: Optional[MCPServer] = None


def get_mcp_server() -> MCPServer:
    """
    Get or create the global MCP server instance.

    Returns:
        MCPServer instance
    """
    global _mcp_server
    if _mcp_server is None:
        _mcp_server = MCPServer()
    return _mcp_server


def initialize_mcp_server() -> MCPServer:
    """
    Initialize and configure the MCP server with all tools.

    Returns:
        Configured MCPServer instance
    """
    server = get_mcp_server()

    # Tools will be registered by the registry module
    logger.info("MCP Server initialization complete")

    return server
