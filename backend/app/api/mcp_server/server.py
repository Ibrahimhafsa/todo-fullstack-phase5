"""MCP Server initialization for AI Chatbot tools (Spec-4)."""
from typing import Any, Callable, Dict

from sqlmodel import Session

from . import tools


class MCPToolRegistry:
    """
    Registry for MCP tools.

    Exposes task_service methods via MCP protocol for OpenAI Agents SDK.
    """

    def __init__(self, session: Session):
        """Initialize tool registry with database session."""
        self.session = session
        self.tools = tools.TOOLS

    def call_tool(self, tool_name: str, **kwargs: Any) -> Any:
        """
        Call an MCP tool by name.

        Args:
            tool_name: Name of tool to call (e.g., 'list_tasks')
            **kwargs: Tool parameters

        Returns:
            Tool result

        Raises:
            ValueError: If tool not found
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")

        # Get tool function by name
        tool_func = getattr(tools, tool_name)

        # Add session to kwargs
        kwargs["session"] = self.session

        # Call tool with parameters
        return tool_func(**kwargs)

    def get_tool_schemas(self) -> Dict[str, Any]:
        """Get all tool schemas for OpenAI Agents SDK."""
        return self.tools


def create_mcp_tools(session: Session) -> MCPToolRegistry:
    """
    Create MCP tool registry.

    Wraps task_service methods for agent access.

    Args:
        session: Database session

    Returns:
        MCPToolRegistry instance
    """
    return MCPToolRegistry(session)
