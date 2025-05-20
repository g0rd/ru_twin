from fastapi import FastAPI
from typing import Dict, Any, Optional, List
import yaml
import os
from pathlib import Path
from .routes import tools_router, auth_router, config_router
from ru_twin.mcp.utils.google import (
    GmailSendTool, GmailReadTool, GmailDraftTool, GmailLabelsTool, GmailSearchTool,
    SheetsReadTool, SheetsWriteTool, SheetsFormatTool, SheetsCreateTool, SheetsShareTool, SheetsFormulasTool,
    DocsCreateTool, DocsEditTool, DocsFormatTool, DocsInsertTool, DocsExportTool, DocsShareTool
)
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

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
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading config from {config_path}: {str(e)}")
            return {
                "server_config": {
                    "auth": {
                        "enabled": False
                    }
                }
            }
    
    def _register_google_tools(self):
        """Register all Google tools with the server."""
        try:
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
        except Exception as e:
            logger.error(f"Error registering Google tools: {str(e)}")
        
    def register_tool(self, tool):
        """Register a new tool with the MCP server."""
        try:
            self._tools[tool.name] = {
                "description": tool.description,
                "input_schema": tool.input_schema
            }
            logger.info(f"Registered tool: {tool.name}")
        except Exception as e:
            logger.error(f"Error registering tool {getattr(tool, 'name', 'unknown')}: {str(e)}")
            raise
        
    def register_agent(self, agent):
        """Register a new agent with the MCP server."""
        try:
            self._agents[agent.name] = {
                "capabilities": agent.capabilities
            }
            logger.info(f"Registered agent: {agent.name}")
        except Exception as e:
            logger.error(f"Error registering agent {getattr(agent, 'name', 'unknown')}: {str(e)}")
            raise

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
    
    def validate_authorization(self, auth_token: str) -> bool:
        """Validate an authorization token."""
        # Implement your authorization logic here
        return True  # For now, always return True

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