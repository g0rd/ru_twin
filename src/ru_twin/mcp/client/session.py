"""MCP Client Session implementation."""

from typing import Any, Dict, List, Optional, AsyncIterator, AsyncContextManager
import asyncio
import json
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class ClientSession(AsyncContextManager['ClientSession']):
    """MCP Client Session for managing connections and tool execution."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the client session."""
        self._initialized = False
        self._closed = False
        self._lock = asyncio.Lock()
        
    async def __aenter__(self) -> 'ClientSession':
        """Enter the async context manager."""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context manager and clean up resources."""
        await self.close()
        
    async def initialize(self) -> None:
        """Initialize the session."""
        if self._initialized:
            return
            
        async with self._lock:
            if self._initialized:  # Double-checked locking pattern
                return
                
            # Perform any initialization here
            self._initialized = True
            logger.info("MCP ClientSession initialized")
    
    async def close(self) -> None:
        """Close the session and release resources."""
        if self._closed:
            return
            
        async with self._lock:
            if self._closed:  # Double-checked locking pattern
                return
                
            # Perform any cleanup here
            self._closed = True
            self._initialized = False
            logger.info("MCP ClientSession closed")
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools.
        
        Returns:
            List of tool definitions
        """
        raise NotImplementedError("list_tools must be implemented by subclasses")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool with the given arguments.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            
        Returns:
            The result of the tool call
        """
        raise NotImplementedError("call_tool must be implemented by subclasses")
    
    async def stream_tool(self, tool_name: str, arguments: Dict[str, Any]) -> AsyncIterator[Any]:
        """Stream the results of a tool call.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            
        Yields:
            Chunks of the tool's output
        """
        # Default implementation just calls the tool and yields the result
        result = await self.call_tool(tool_name, arguments)
        yield result
