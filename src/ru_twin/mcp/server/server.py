from fastapi import FastAPI, HTTPException, Depends
from typing import Dict, Any, Optional
import yaml
import os
from pathlib import Path

class MCPServer:
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the MCP server with configuration."""
        self.app = FastAPI(title="MCP Server", version="1.0.0")
        self.tools = {}
        self.agents = {}
        self.config = self._load_config(config_path) if config_path else {}
        self._setup_routes()
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load server configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
            
    def _setup_routes(self):
        """Set up FastAPI routes for the MCP server."""
        
        @self.app.post("/tools/{tool_name}/invoke")
        async def invoke_tool(tool_name: str, request: Dict[str, Any]):
            """Invoke a tool with the given name and payload."""
            if tool_name not in self.tools:
                raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")
                
            tool = self.tools[tool_name]
            agent_name = request.get("agent")
            
            if not agent_name or agent_name not in self.agents:
                raise HTTPException(status_code=400, detail="Invalid agent name")
                
            try:
                result = await tool.execute(agent_name, request.get("payload", {}))
                return {"result": result}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.get("/tools")
        async def list_tools():
            """List all available tools."""
            return {
                "tools": [
                    {
                        "name": name,
                        "description": tool.description,
                        "input_schema": tool.input_schema
                    }
                    for name, tool in self.tools.items()
                ]
            }
            
        @self.app.get("/agents")
        async def list_agents():
            """List all registered agents."""
            return {
                "agents": [
                    {
                        "name": name,
                        "capabilities": agent.capabilities
                    }
                    for name, agent in self.agents.items()
                ]
            }
            
    def register_tool(self, tool):
        """Register a new tool with the MCP server."""
        self.tools[tool.name] = tool
        
    def register_agent(self, agent):
        """Register a new agent with the MCP server."""
        self.agents[agent.name] = agent
        
    def get_app(self):
        """Get the FastAPI application instance."""
        return self.app 