from typing import Any, Callable, Dict, Type
from pydantic import BaseModel
import json

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
        # Convert Pydantic model to JSON schema
        schema_dict = input_schema.model_json_schema()
        
        self._tools[name] = {
            "function": func,
            "description": description,
            "input_schema": schema_dict
        }
    
    def get_tool(self, name: str) -> Dict[str, Any]:
        """Get a tool's configuration by name."""
        return self._tools.get(name)
    
    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        """List all registered tools and their configurations."""
        return {
            name: {
                "description": tool["description"],
                "input_schema": tool["input_schema"]
            }
            for name, tool in self._tools.items()
        } 