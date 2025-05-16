from typing import Any, Callable, Dict, Type
from pydantic import BaseModel

class ToolRegistry:
    """Registry for managing tools and their configurations."""
    
    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}
    
    def register_tool(
        self,
        name: str,
        func: Callable,
        description: str,
        input_schema: Type[BaseModel]
    ) -> None:
        """Register a tool with its configuration."""
        self._tools[name] = {
            "function": func,
            "description": description,
            "input_schema": input_schema
        }
    
    def get_tool(self, name: str) -> Dict[str, Any]:
        """Get a tool's configuration by name."""
        return self._tools.get(name)
    
    def list_tools(self) -> Dict[str, str]:
        """List all registered tools and their descriptions."""
        return {name: tool["description"] for name, tool in self._tools.items()} 