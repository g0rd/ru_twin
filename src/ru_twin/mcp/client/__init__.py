from typing import Dict, Any, Optional
from pydantic import BaseModel
import aiohttp
import json

class ClientConfig(BaseModel):
    """Client configuration schema"""
    base_url: str = "http://localhost:8000"
    api_version: str = "v1"
    timeout: int = 30

class MCPClient:
    """Mission Control Platform Client"""
    
    def __init__(self, config: Optional[ClientConfig] = None):
        self.config = config or ClientConfig()
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to MCP server"""
        if not self._session:
            raise RuntimeError("Client session not initialized. Use async with context.")
            
        url = f"{self.config.base_url}/api/{self.config.api_version}/{endpoint}"
        
        async with self._session.request(method, url, **kwargs) as response:
            if response.status >= 400:
                error_data = await response.json()
                raise Exception(f"Request failed: {error_data.get('message', str(response.status))}")
            return await response.json()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check server health"""
        return await self._request("GET", "health")
    
    async def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool on the server"""
        return await self._request(
            "POST",
            f"tools/{tool_name}/execute",
            json=tool_input
        )

# Create default client instance
client = MCPClient()

__all__ = ['MCPClient', 'ClientConfig', 'client']
