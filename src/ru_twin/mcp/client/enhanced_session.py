"""Session management for MCP client with enhanced functionality."""

from typing import Any, Dict, List, Optional, TYPE_CHECKING
import json
import logging

# Import from our local session module
from .session import ClientSession as MCPClientSession

if TYPE_CHECKING:
    from .client import MCPClient  # For type hints only

logger = logging.getLogger(__name__)


class EnhancedMCPSession:
    """Enhanced wrapper around the official MCP ClientSession with additional features."""
    
    def __init__(self, session: MCPClientSession):
        self.session = session
        self._tool_cache: Optional[List[Dict[str, Any]]] = None
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize the underlying session."""
        if not self._initialized:
            await self.session.initialize()
            self._initialized = True
            logger.info("Enhanced MCP session initialized")
    
    async def get_tools_cached(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Get tools with caching support."""
        if not self._initialized:
            raise RuntimeError("Session not initialized. Call initialize() first.")
            
        if self._tool_cache is None or force_refresh:
            tools_result = await self.session.list_tools()
            self._tool_cache = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                }
                for tool in tools_result.tools
            ]
            logger.info(f"Cached {len(self._tool_cache)} tools")
        
        return self._tool_cache
    
    async def call_tool_safe(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool with error handling and logging."""
        if not self._initialized:
            raise RuntimeError("Session not initialized. Call initialize() first.")
            
        logger.info(f"Calling tool '{tool_name}' with args: {arguments}")
        
        try:
            result = await self.session.call_tool(tool_name, arguments)
            logger.info(f"Tool '{tool_name}' completed successfully")
            
            # Handle different result formats
            if hasattr(result, 'content'):
                return {"success": True, "content": result.content}
            else:
                return {"success": True, "content": result}
                
        except Exception as e:
            logger.error(f"Tool '{tool_name}' failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name,
                "arguments": arguments
            }
    
    async def validate_tool_args(self, tool_name: str, arguments: Dict[str, Any]) -> bool:
        """Validate tool arguments against the tool's schema."""
        tools = await self.get_tools_cached()
        
        for tool in tools:
            if tool["name"] == tool_name:
                # Basic validation - you could extend this with jsonschema
                required_props = tool["input_schema"].get("required", [])
                provided_props = set(arguments.keys())
                required_props_set = set(required_props)
                
                if not required_props_set.issubset(provided_props):
                    missing = required_props_set - provided_props
                    logger.warning(f"Missing required arguments for {tool_name}: {missing}")
                    return False
                
                return True
        
        logger.warning(f"Tool '{tool_name}' not found")
        return False
    
    def get_tool_by_name(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get tool information by name."""
        if self._tool_cache:
            for tool in self._tool_cache:
                if tool["name"] == tool_name:
                    return tool
        return None
    
    async def close(self):
        """Close the session gracefully."""
        # The official ClientSession should handle cleanup
        if hasattr(self.session, 'close'):
            await self.session.close()
        logger.info("MCP session closed")


# Utility functions for working with MCP tools

def format_tool_for_anthropic(tool: Dict[str, Any]) -> Dict[str, Any]:
    """Format a tool definition for use with Anthropic's API."""
    return {
        "name": tool["name"],
        "description": tool["description"],
        "input_schema": tool["input_schema"]
    }


def format_tools_for_anthropic(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format multiple tool definitions for use with Anthropic's API."""
    return [format_tool_for_anthropic(tool) for tool in tools]


def parse_tool_result(result: Any) -> str:
    """Parse and format tool result for display."""
    if isinstance(result, dict):
        if result.get("success") is False:
            return f"Error: {result.get('error', 'Unknown error')}"
        elif "content" in result:
            content = result["content"]
            if isinstance(content, (list, dict)):
                return json.dumps(content, indent=2)
            else:
                return str(content)
    
    if isinstance(result, (list, dict)):
        return json.dumps(result, indent=2)
    
    return str(result)