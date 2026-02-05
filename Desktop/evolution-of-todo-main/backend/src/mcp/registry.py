"""
MCP Tool Registry for Phase III AI Chatbot.

Registers all MCP tools with the server and provides tool metadata
for the AI agent to understand available capabilities.
"""
from typing import Dict, List, Any
import logging
from .server import get_mcp_server

logger = logging.getLogger(__name__)


class MCPToolRegistry:
    """
    Registry for MCP tools.

    Manages tool registration and provides tool metadata for AI agent.
    """

    def __init__(self):
        """Initialize the tool registry."""
        self.server = get_mcp_server()
        self._tool_metadata: Dict[str, Dict[str, Any]] = {}

    def register_tool(self, name: str, tool_instance, metadata: Dict[str, Any]):
        """
        Register a tool with metadata.

        Args:
            name: Tool name
            tool_instance: Tool instance
            metadata: Tool metadata (description, parameters, etc.)
        """
        self.server.register_tool(name, tool_instance)
        self._tool_metadata[name] = metadata
        logger.info(f"Registered tool '{name}' with metadata")

    def get_tool_metadata(self, name: str) -> Dict[str, Any]:
        """
        Get metadata for a specific tool.

        Args:
            name: Tool name

        Returns:
            Tool metadata dictionary
        """
        return self._tool_metadata.get(name, {})

    def get_all_tools_metadata(self) -> List[Dict[str, Any]]:
        """
        Get metadata for all registered tools.

        Returns:
            List of tool metadata dictionaries
        """
        return [
            {"name": name, **metadata}
            for name, metadata in self._tool_metadata.items()
        ]

    def get_tools_for_agent(self) -> List[Dict[str, Any]]:
        """
        Get tool definitions formatted for OpenAI Agents SDK.

        Returns:
            List of tool definitions in OpenAI format
        """
        tools = []
        for name, metadata in self._tool_metadata.items():
            tool_def = {
                "type": "function",
                "function": {
                    "name": name,
                    "description": metadata.get("description", ""),
                    "parameters": metadata.get("parameters", {})
                }
            }
            tools.append(tool_def)
        return tools


# Global registry instance
_registry: MCPToolRegistry = None


def get_tool_registry() -> MCPToolRegistry:
    """
    Get or create the global tool registry.

    Returns:
        MCPToolRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = MCPToolRegistry()
    return _registry


def register_all_tools():
    """
    Register all MCP tools with the registry.

    This function imports and registers all available tools.
    Called during application startup.
    """
    registry = get_tool_registry()

    # Register create_task tool (Phase 3 - US1)
    try:
        from .tools.create_task import CreateTaskTool, create_task_metadata
        registry.register_tool("create_task", CreateTaskTool(), create_task_metadata)
        logger.info("Registered create_task tool")
    except ImportError as e:
        logger.warning(f"create_task tool not yet implemented: {e}")

    # Register get_tasks tool (Phase 4 - US2)
    try:
        from .tools.get_tasks import GetTasksTool, get_tasks_metadata
        registry.register_tool("get_tasks", GetTasksTool(), get_tasks_metadata)
    except ImportError:
        logger.warning("get_tasks tool not yet implemented")

    # Register update_task tool (Phase 5 - US3)
    try:
        from .tools.update_task import UpdateTaskTool, update_task_metadata
        registry.register_tool("update_task", UpdateTaskTool(), update_task_metadata)
    except ImportError:
        logger.warning("update_task tool not yet implemented")

    # Register delete_task tool (Phase 6 - US4)
    try:
        from .tools.delete_task import DeleteTaskTool, delete_task_metadata
        registry.register_tool("delete_task", DeleteTaskTool(), delete_task_metadata)
    except ImportError:
        logger.warning("delete_task tool not yet implemented")

    logger.info(f"Registered {len(registry.get_all_tools_metadata())} MCP tools")
