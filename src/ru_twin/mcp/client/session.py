from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class Tool(BaseModel):
    name: str
    description: str
    inputSchema: Dict[str, Any]

class ToolResponse(BaseModel):
    content: List[Dict[str, Any]]

class ClientSession:
    def __init__(self, input_stream, output_stream):
        self.input_stream = input_stream
        self.output_stream = output_stream
        self._initialized = False

    async def initialize(self):
        """Initialize the session."""
        if not self._initialized:
            await self.output_stream.send({"type": "initialize"})
            response = await self.input_stream.receive()
            if response.get("type") != "initialized":
                raise Exception("Failed to initialize session")
            self._initialized = True

    async def list_tools(self) -> List[Tool]:
        """List available tools."""
        await self.output_stream.send({"type": "list_tools"})
        response = await self.input_stream.receive()
        if response.get("type") != "tools_list":
            raise Exception("Failed to list tools")
        return [Tool(**tool) for tool in response.get("tools", [])]

    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> ToolResponse:
        """Call a tool with the given arguments."""
        await self.output_stream.send({
            "type": "call_tool",
            "tool": tool_name,
            "args": args
        })
        response = await self.input_stream.receive()
        if response.get("type") != "tool_result":
            raise Exception("Failed to call tool")
        return ToolResponse(content=response.get("content", [])) 