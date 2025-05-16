import asyncio
import json
import os
from typing import Optional, Dict, Any, List
from contextlib import AsyncExitStack
import yaml
from .session import ClientSession
from .sse import sse_client

from anthropic import Anthropic
from dotenv import load_dotenv

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from openinference.semconv.trace import SpanAttributes

# Load environment variables
load_dotenv()

class MCPClient:
    def __init__(self, name: str, use_tracing: bool = True):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.messages = []
        self.name = name
        self.system_prompt = "You are a helpful assistant that can help with a users personal finances. You carefully explain any action you have taken."
        self.use_tracing = use_tracing
        self.tracer = trace.get_tracer("mcp_client")
        self._streams_context = None
        self._session_context = None
        
    async def connect_to_sse_server(self, server_url: str):
        """Connect to an MCP server running with SSE transport"""
        with self.tracer.start_as_current_span("connect_to_sse_server") as span:
            span.set_attribute("server_url", server_url)
            
            self._streams_context = sse_client(url=server_url)
            streams = await self._streams_context.__aenter__()

            self._session_context = ClientSession(*streams)
            self.session: ClientSession = await self._session_context.__aenter__()

            await self.session.initialize()
            
            span.set_status(Status(StatusCode.OK))
            print("Initialized SSE client...")

    async def cleanup(self):
        """Properly clean up the session and streams"""
        with self.tracer.start_as_current_span("cleanup"):
            if self._session_context:
                await self._session_context.__aexit__(None, None, None)
            if self._streams_context:
                await self._streams_context.__aexit__(None, None, None)
    
    async def get_current_tool_names(self) -> List[str]:
        """Get available tool names from the server"""
        with self.tracer.start_as_current_span("get_current_tool_names") as span:
            response = await self.session.list_tools()
            available_tool_names = [tool.name for tool in response.tools]
            span.set_attribute("tool_count", len(available_tool_names))
            return available_tool_names
    
    async def call_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Any:
        """Call a specific tool with arguments"""
        with self.tracer.start_as_current_span("call_tool") as span:
            span.set_attribute("tool.name", tool_name)
            span.set_attribute("tool.args", json.dumps(tool_args))
            span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, "tool")
            
            try:
                result = await self.session.call_tool(tool_name, tool_args)
                span.set_status(Status(StatusCode.OK))
                return result
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    async def chat_loop(self):
        """Main interactive chat loop with tracing"""
        while True:
            with self.tracer.start_as_current_span("chat_interaction") as chat_span:
                # Get user input
                user_question = input("Enter a question: ")
                chat_span.set_attribute("user_input", user_question)
                self.messages.append({
                    "role": "user",
                    "content": user_question
                })
                
                # Get available tools
                with self.tracer.start_as_current_span("fetch_available_tools") as tools_span:
                    response = await self.session.list_tools()
                    available_tools = [{ 
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema
                    } for tool in response.tools]
                    tools_span.set_attribute("tool_count", len(available_tools))
                
                # Initial LLM call
                with self.tracer.start_as_current_span("llm_call") as llm_span:
                    llm_span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, "llm")
                    llm_span.set_attribute("model", "claude-3-7-sonnet-20250219")
                    
                    response = self.anthropic.messages.create(
                        model="claude-3-7-sonnet-20250219",
                        max_tokens=1000,
                        system=self.system_prompt,
                        messages=self.messages,
                        tools=available_tools
                    )
                    llm_span.set_attribute("tokens_used", response.usage.output_tokens + response.usage.input_tokens)

                tool_results = []
                final_text = []

                # Process response content
                for content in response.content:
                    if content.type == 'text':
                        final_text.append(content.text)
                    elif content.type == 'tool_use':
                        tool_name = content.name
                        tool_args = content.input
                        
                        # Tool usage tracing
                        with self.tracer.start_as_current_span(f"tool_execution_{tool_name}") as tool_span:
                            tool_span.set_attribute("tool.name", tool_name)
                            tool_span.set_attribute("tool.args", json.dumps(tool_args))
                            tool_span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, "tool")
                            
                            result = await self.session.call_tool(tool_name, tool_args)
                            tool_results.append({"call": tool_name, "result": result})
                            final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                            self.messages.append({
                                "role": "assistant", 
                                "content": f"Calling tool {tool_name} with args {tool_args}, the result is: " + "\n".join([x.text for x in result.content])
                            })

                        # Follow-up LLM call after tool use
                        with self.tracer.start_as_current_span("llm_call_after_tool") as follow_llm_span:
                            follow_llm_span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, "llm")
                            follow_llm_span.set_attribute("model", "claude-3-7-sonnet-20250219")
                            follow_llm_span.set_attribute("after_tool", tool_name)
                            
                            response = self.anthropic.messages.create(
                                model="claude-3-7-sonnet-20250219",
                                max_tokens=1000,
                                system=self.system_prompt,
                                messages=self.messages,
                            )
                            
                            try:
                                final_text.append(response.content[0].text)
                                print(final_text[-1])
                                follow_llm_span.set_attribute("success", True)
                                follow_llm_span.set_attribute("tokens_used", response.usage.output_tokens + response.usage.input_tokens)
                            except Exception as e:
                                print(e)
                                follow_llm_span.record_exception(e)
                                follow_llm_span.set_attribute("success", False)
                
                # Set overall metrics for this interaction
                chat_span.set_attribute("tool_calls_count", len(tool_results))
                chat_span.set_attribute("total_responses", len(final_text))


async def main(name, server_url):
    """Main entry point with proper tracing setup"""
    # Set up a parent span for the entire session
    tracer = trace.get_tracer("mcp_session")
    
    with tracer.start_as_current_span(f"mcp_session_{name}") as session_span:
        session_span.set_attribute("client_name", name)
        session_span.set_attribute("server_url", server_url)
        
        client = MCPClient(name=name)
        try:
            await client.connect_to_sse_server(server_url=server_url)
            await client.chat_loop()
            session_span.set_status(Status(StatusCode.OK))
        except Exception as e:
            session_span.set_status(Status(StatusCode.ERROR, str(e)))
            session_span.record_exception(e)
            raise
        finally:
            await client.cleanup()


if __name__ == "__main__":
    import sys
    asyncio.run(main(name=sys.argv[1], server_url=sys.argv[2]))