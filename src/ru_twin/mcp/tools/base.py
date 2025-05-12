from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from pydantic import BaseModel

class ToolInputSchema(BaseModel):
    """Base class for tool input schemas."""
    pass

class BaseTool(ABC):
    def __init__(
        self,
        name: str,
        description: str,
        input_schema: Optional[Dict[str, Any]] = None,
        version: str = "1.0.0"
    ):
        """Initialize a base tool.
        
        Args:
            name: The name of the tool
            description: A description of what the tool does
            input_schema: JSON Schema for the tool's input
            version: Tool version
        """
        self.name = name
        self.description = description
        self.input_schema = input_schema or {}
        self.version = version
        
    @abstractmethod
    async def execute(self, agent_name: str, payload: Dict[str, Any]) -> Any:
        """Execute the tool with the given payload.
        
        Args:
            agent_name: Name of the agent executing the tool
            payload: Tool input payload
            
        Returns:
            Tool execution result
        """
        pass
        
    def validate_input(self, payload: Dict[str, Any]) -> bool:
        """Validate the input payload against the tool's schema.
        
        Args:
            payload: Input payload to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            ToolInputSchema(**payload)
            return True
        except Exception:
            return False
            
    def get_info(self) -> Dict[str, Any]:
        """Get tool information.
        
        Returns:
            Dictionary containing tool metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "version": self.version
        } 