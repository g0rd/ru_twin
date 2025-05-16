from fastapi import FastAPI
from typing import Dict, Any, Optional, List
import yaml
import os
from pathlib import Path
from .routes import tools_router, auth_router, config_router
from ..tools.google import (
    GmailSendTool, GmailReadTool, GmailDraftTool, GmailLabelsTool, GmailSearchTool,
    SheetsReadTool, SheetsWriteTool, SheetsFormatTool, SheetsCreateTool, SheetsShareTool, SheetsFormulasTool,
    DocsCreateTool, DocsEditTool, DocsFormatTool, DocsInsertTool, DocsExportTool, DocsShareTool
)
from pydantic import BaseModel

class MCPServer:
    """Message Control Protocol Server implementation."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the MCP server with configuration."""
        self.app = FastAPI(title="MCP Server", version="1.0.0")
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._agents: Dict[str, Dict[str, Any]] = {}
        self.config = self._load_config(config_path) if config_path else {
            "server_config": {
                "auth": {
                    "enabled": False
                }
            }
        }
        
        # Include routers
        self.app.include_router(tools_router, prefix="/api/v1/tools", tags=["tools"])
        self.app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
        self.app.include_router(config_router, prefix="/api/v1/config", tags=["config"])
        
        # Register Google tools
        self._register_google_tools()
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load server configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _register_google_tools(self):
        """Register all Google tools with the server."""
        # Gmail tools
        self.register_tool(GmailSendTool())
        self.register_tool(GmailReadTool())
        self.register_tool(GmailDraftTool())
        self.register_tool(GmailLabelsTool())
        self.register_tool(GmailSearchTool())
        
        # Google Sheets tools
        self.register_tool(SheetsReadTool())
        self.register_tool(SheetsWriteTool())
        self.register_tool(SheetsFormatTool())
        self.register_tool(SheetsCreateTool())
        self.register_tool(SheetsShareTool())
        self.register_tool(SheetsFormulasTool())
        
        # Google Docs tools
        self.register_tool(DocsCreateTool())
        self.register_tool(DocsEditTool())
        self.register_tool(DocsFormatTool())
        self.register_tool(DocsInsertTool())
        self.register_tool(DocsExportTool())
        self.register_tool(DocsShareTool())
        
    def register_tool(self, tool):
        """Register a new tool with the MCP server."""
        self._tools[tool.name] = {
            "description": tool.description,
            "input_schema": tool.input_schema
        }
        
    def register_agent(self, agent):
        """Register a new agent with the MCP server."""
        self._agents[agent.name] = {
            "capabilities": agent.capabilities
        }
        
    def get_app(self):
        """Get the FastAPI application instance."""
        return self.app 

    def get_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get a tool by name."""
        return self._tools.get(tool_name)
    
    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        """List all registered tools."""
        return self._tools
    
    def list_agents(self) -> Dict[str, Dict[str, Any]]:
        """List all registered agents."""
        return self._agents
    
    async def invoke_tool(self, tool_name: str, agent: str, payload: Dict[str, Any]) -> Any:
        """Invoke a tool with the given payload."""
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool {tool_name} not found")
        # Implement actual tool invocation logic here
        return {"status": "invoked", "tool": tool_name, "agent": agent}
    
    def validate_authorization(self, auth_header: str) -> bool:
        """Validate authorization header."""
        # Implement actual authorization logic here
        return True

    def register_tool(self, tool_data: Any) -> None:
        """Register a new tool."""
        self._tools[tool_data.name] = {
            "description": tool_data.description,
            "input_schema": tool_data.input_schema
        }
    
    def register_agent(self, agent_data: Any) -> None:
        """Register a new agent."""
        self._agents[agent_data.name] = {
            "capabilities": agent_data.capabilities
        } 