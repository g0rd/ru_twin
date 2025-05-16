from fastapi import APIRouter, HTTPException, Header, Depends, Request
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# Define Pydantic models for request bodies
class ToolInvocationRequest(BaseModel):
    agent: str
    payload: Optional[Dict[str, Any]] = Field(default_factory=dict)

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

# Dependency function to get the MCPServer instance
async def get_mcp_server(request: Request):
    return request.app.state.mcp_server

tools_router = APIRouter()

@tools_router.post("/tools/{tool_name}/invoke", response_model=InvocationResponse)
async def invoke_tool(
    tool_name: str,
    request_body: ToolInvocationRequest,
    mcp_server = Depends(get_mcp_server),
    authorization: Optional[str] = Header(None)
):
    """Invoke a tool with the given name and payload."""
    tool = mcp_server.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")

    # Validate authorization if required
    if mcp_server.config.get("server_config", {}).get("auth", {}).get("enabled", False):
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header required")
        if not mcp_server.validate_authorization(authorization):
            raise HTTPException(status_code=403, detail="Invalid authorization")

    try:
        result = await mcp_server.invoke_tool(tool_name, request_body.agent, request_body.payload)
        return InvocationResponse(result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@tools_router.get("/tools", response_model=List[ToolInfo])
async def list_tools(mcp_server = Depends(get_mcp_server)):
    """List all available tools."""
    tools = mcp_server.list_tools()
    return [ToolInfo(name=name, description=tool["description"], input_schema=tool["input_schema"]) for name, tool in tools.items()]

@tools_router.get("/agents", response_model=List[AgentInfo])
async def list_agents(mcp_server = Depends(get_mcp_server)):
    """List all registered agents."""
    agents = mcp_server.list_agents()
    return [AgentInfo(name=name, capabilities=agent["capabilities"]) for name, agent in agents.items()]

@tools_router.get("/health")
async def tools_health_check():
    """Health check endpoint for tools subsystem."""
    return {"status": "healthy", "message": "Tools subsystem is operational"}

@tools_router.post("/tools/register")
async def register_tool(tool_data: ToolRegistrationRequest, mcp_server = Depends(get_mcp_server)):
    """Register a new tool with the MCP server."""
    try:
        if tool_data.name in mcp_server.list_tools():
            raise HTTPException(status_code=409, detail=f"Tool {tool_data.name} already exists")

        mcp_server.register_tool(tool_data) # Placeholder for actual registration logic
        return {"status": "registered", "tool": tool_data.name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@tools_router.post("/agents/register")
async def register_agent(agent_data: AgentRegistrationRequest, mcp_server = Depends(get_mcp_server)):
    """Register a new agent with the MCP server."""
    try:
        if agent_data.name in mcp_server.list_agents():
            raise HTTPException(status_code=409, detail=f"Agent {agent_data.name} already exists")

        mcp_server.register_agent(agent_data)  # Placeholder for actual registration logic
        return {"status": "registered", "agent": agent_data.name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

auth_router = APIRouter()
config_router = APIRouter()
