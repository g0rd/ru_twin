from fastapi import APIRouter, HTTPException, Header, Depends, Request
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# Define Pydantic models for request bodies
class ToolInvocationRequest(BaseModel):
    agent: str
    payload: Optional[Dict[str, Any]] = Field(default_factory=dict)

class AuthRequest(BaseModel):
    username: str
    password: str

class ConfigUpdateRequest(BaseModel):
    key: str
    value: Any

class ToolRegistrationRequest(BaseModel):
    name: str = Field(description="Name of the tool")
    description: str = Field(description="Description of the tool's functionality")
    input_schema: Dict[str, Any] = Field(description="JSON Schema defining the tool's input parameters")
    # Add other necessary fields for defining a tool

class AgentRegistrationRequest(BaseModel):
    name: str = Field(description="Name of the agent")
    capabilities: List[str] = Field(description="List of capabilities this agent has")
    # Add other necessary fields for defining an agent

# Define Pydantic models for responses
class ToolInfo(BaseModel):
    name: str = Field(description="Name of the tool")
    description: str = Field(description="Description of the tool's functionality")
    input_schema: Dict[str, Any] = Field(description="JSON Schema defining the tool's input parameters")

class AgentInfo(BaseModel):
    name: str = Field(description="Name of the agent")
    capabilities: List[str] = Field(description="List of capabilities this agent has")

class InvocationResponse(BaseModel):
    result: Any = Field(description="Result of the tool invocation")

# Create routers
tools_router = APIRouter()
auth_router = APIRouter()
config_router = APIRouter()

# Tools endpoints
@tools_router.get("/")
async def list_tools(request: Request):
    """List all available tools."""
    try:
        # Get the MCP server from app state
        mcp_server = getattr(request.app.state, 'mcp_server', None)
        if not mcp_server:
            # If MCP server is not available, return a basic response
            return {
                "status": "success",
                "message": "MCP server not initialized",
                "tools": []
            }
        
        # If MCP server is available, get the tools
        tools = mcp_server.list_tools()
        return {
            "status": "success",
            "tools": [
                {
                    "name": name,
                    "description": tool.get("description", ""),
                    "input_schema": tool.get("input_schema", {}).model_json_schema() if hasattr(tool.get("input_schema", {}), "model_json_schema") else {}
                }
                for name, tool in tools.items()
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing tools: {str(e)}"
        )

@tools_router.post("/invoke")
async def invoke_tool(
    tool_name: str,
    request_body: ToolInvocationRequest,
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """Invoke a tool with the given name and payload."""
    try:
        # Get the MCP server from app state
        mcp_server = getattr(request.app.state, 'mcp_server', None)
        if not mcp_server:
            raise HTTPException(
                status_code=503,
                detail="MCP server not initialized"
            )

        # Get the tool
        tool = mcp_server.get_tool(tool_name)
        if not tool:
            raise HTTPException(
                status_code=404,
                detail=f"Tool {tool_name} not found"
            )

        # Validate authorization if required
        if mcp_server.config.get("server_config", {}).get("auth", {}).get("enabled", False):
            if not authorization:
                raise HTTPException(
                    status_code=401,
                    detail="Authorization header required"
                )
            if not mcp_server.validate_authorization(authorization):
                raise HTTPException(
                    status_code=403,
                    detail="Invalid authorization"
                )

        # Invoke the tool
        result = await mcp_server.invoke_tool(
            tool_name,
            request_body.agent,
            request_body.payload
        )
        
        return {
            "status": "success",
            "result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error invoking tool: {str(e)}"
        )

@tools_router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@tools_router.post("/tools/register")
async def register_tool(tool_data: ToolRegistrationRequest, request: Request):
    """Register a new tool with the MCP server."""
    try:
        # Get the MCP server from app state
        mcp_server = getattr(request.app.state, 'mcp_server', None)
        if not mcp_server:
            raise HTTPException(
                status_code=503,
                detail="MCP server not initialized"
            )

        if tool_data.name in mcp_server.list_tools():
            raise HTTPException(
                status_code=409,
                detail=f"Tool {tool_data.name} already exists"
            )

        mcp_server.register_tool(tool_data)
        return {
            "status": "success",
            "message": "Tool registered successfully",
            "tool": tool_data.name
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error registering tool: {str(e)}"
        )

@tools_router.get("/agents")
async def list_agents(request: Request):
    """List all registered agents."""
    try:
        # Get the MCP server from app state
        mcp_server = getattr(request.app.state, 'mcp_server', None)
        if not mcp_server:
            return {
                "status": "success",
                "message": "MCP server not initialized",
                "agents": []
            }

        agents = mcp_server.list_agents()
        return {
            "status": "success",
            "agents": [
                AgentInfo(
                    name=name,
                    capabilities=agent.get("capabilities", [])
                ).dict()
                for name, agent in agents.items()
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing agents: {str(e)}"
        )

@tools_router.post("/agents/register")
async def register_agent(agent_data: AgentRegistrationRequest, request: Request):
    """Register a new agent with the MCP server."""
    try:
        # Get the MCP server from app state
        mcp_server = getattr(request.app.state, 'mcp_server', None)
        if not mcp_server:
            raise HTTPException(
                status_code=503,
                detail="MCP server not initialized"
            )

        if agent_data.name in mcp_server.list_agents():
            raise HTTPException(
                status_code=409,
                detail=f"Agent {agent_data.name} already exists"
            )

        mcp_server.register_agent(agent_data)
        return {
            "status": "success",
            "message": "Agent registered successfully",
            "agent": agent_data.name
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error registering agent: {str(e)}"
        )

# Auth endpoints
@auth_router.post("/login")
async def login(request: AuthRequest):
    """Authenticate a user."""
    return {"status": "success", "token": "dummy_token"}

@auth_router.post("/logout")
async def logout():
    """Logout the current user."""
    return {"status": "success"}

# Config endpoints
@config_router.get("/")
async def get_config():
    """Get current configuration."""
    return {"config": {"key": "value"}}

@config_router.post("/update")
async def update_config(request: ConfigUpdateRequest):
    """Update configuration."""
    return {"status": "success", "updated": request.dict()}
