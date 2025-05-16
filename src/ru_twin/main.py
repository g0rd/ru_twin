#!/usr/bin/env python3
"""
RuTwin Crew - Main Application Entry Point

This module initializes the RuTwin Crew system, including:
- CrewAI orchestration
- MCP and A2A architecture
- Tool registration
- OpenTelemetry and Arize Phoenix observability
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

import yaml
from dotenv import load_dotenv
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
import structlog
import uvicorn
import phoenix as px
import uuid

# OpenTelemetry imports
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.trace import Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from openinference.instrumentation import using_session
from openinference.semconv.trace import SpanAttributes
from openinference.instrumentation.crewai import CrewAIInstrumentor
from openinference.instrumentation.litellm import LiteLLMInstrumentor
from crewai_tools import SerperDevTool

# RuTwin imports
from ru_twin.crew import create_crew
from ru_twin.a2a import AgentMessenger
from ru_twin.third_party_gateway import ThirdPartyAgentGateway
from ru_twin.tools.tool_registry import ToolRegistry

# Import tool registration functions
from ru_twin.tools.shopify_tools import register_tools as register_shopify_tools
from ru_twin.tools.teller_tools import register_tools as register_teller_tools

# Import MCP clients
from ru_twin.mcp.tools.shopify import ShopifyClient
from ru_twin.mcp.tools.teller import TellerClient

# Import MCP Client base class
from ru_twin.mcp.client import MCPClient
from ru_twin.mcp.session import ClientSession
from ru_twin.mcp.sse import sse_client

# Anthropic import
from anthropic import Anthropic

def init_opentelemetry() -> TracerProvider:
    """Initialize OpenTelemetry for tracing and metrics."""
    # Get OTLP endpoint from environment or use default Phoenix endpoint
    
    session = px.launch_app().view()
    tracer_provider = register(endpoint="http://localhost:6006/v1/traces")
    CrewAIInstrumentor().instrument(skip_dep_check=True, tracer_provider=tracer_provider)
    LiteLLMInstrumentor().instrument(tracer_provider=tracer_provider)

    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://phoenix:4317")
    service_name = os.getenv("OTEL_SERVICE_NAME", "ru_twin")
    
    # Create a resource to identify the service
    resource = Resource.create({"service.name": service_name})
    
    # Create OTLP exporter for traces
    otlp_span_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
    
    # Add span processor to the tracer provider
    tracer_provider.add_span_processor(BatchSpanProcessor(otlp_span_exporter))
    
    # Set the global tracer provider
    if not isinstance(trace.get_tracer_provider(), TracerProvider) or isinstance(trace.get_tracer_provider(), trace.NoOpTracerProvider):
        trace.set_tracer_provider(tracer_provider)
    
    # Initialize MeterProvider with the resource
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=otlp_endpoint)
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    
    # Set the global meter provider
    if not isinstance(metrics.get_meter_provider(), MeterProvider) or isinstance(metrics.get_meter_provider(), metrics.NoOpMeterProvider):
        metrics.set_meter_provider(meter_provider)
    
    logger.info("OpenTelemetry initialized", 
                otlp_endpoint=otlp_endpoint, 
                service_name=service_name)
    
    return tracer_provider

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Initialize Phoenix function
def register(endpoint="http://localhost:6006/v1/traces"):
    """Register Phoenix for OpenTelemetry."""
    # This is a simplified version of what was in the original code
    resource = Resource.create({"service.name": "ru_twin"})
    tracer_provider = TracerProvider(resource=resource)
    return tracer_provider

# Global variables
tool_registry = None
third_party_gateway = None
a2a_messenger = None
mcp_clients = {}

def load_config(config_path: str) -> Dict:
    """Load configuration from YAML file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def init_tool_registry() -> ToolRegistry:
    """Initialize and populate the tool registry."""
    registry = ToolRegistry()
    
    # Register tools from different modules
    register_shopify_tools(registry)
    register_teller_tools(registry)
    
    logger.info(f"Tool registry initialized with {len(registry.get_all_tools())} tools")
    return registry

def init_third_party_gateway(registry: ToolRegistry) -> ThirdPartyAgentGateway:
    """Initialize the third-party gateway."""
    return ThirdPartyAgentGateway(registry=registry)

def init_a2a_messenger(registry: ToolRegistry) -> AgentMessenger:
    """Initialize the Agent-to-Agent messenger."""
    return AgentMessenger(agent_registry=registry)

async def init_mcp_clients() -> Dict[str, MCPClient]:
    """Initialize MCP clients for external services."""
    clients = {}
    tracer = trace.get_tracer("ru_twin_mcp")
    
    with tracer.start_as_current_span("init_mcp_clients") as span:
        # Initialize configuration for MCP clients
        mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8080/events")
        
        # Initialize Financial MCP client
        finance_client = MCPClient(name="finance_client")
        try:
            await finance_client.connect_to_sse_server(server_url=f"{mcp_server_url}/finance")
            clients["finance"] = finance_client
            span.set_attribute("finance_client_initialized", True)
            logger.info("Finance MCP client initialized")
        except Exception as e:
            span.record_exception(e)
            logger.error(f"Failed to initialize Finance MCP client: {e}")
        
        # Initialize E-commerce MCP client
        ecommerce_client = MCPClient(name="ecommerce_client")
        try:
            await ecommerce_client.connect_to_sse_server(server_url=f"{mcp_server_url}/ecommerce")
            clients["ecommerce"] = ecommerce_client
            span.set_attribute("ecommerce_client_initialized", True)
            logger.info("E-commerce MCP client initialized")
        except Exception as e:
            span.record_exception(e)
            logger.error(f"Failed to initialize E-commerce MCP client: {e}")
        
        # Initialize Shopify client if credentials are available
        shopify_shop_url = os.getenv("SHOPIFY_SHOP_URL")
        shopify_access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")
        shopify_api_version = os.getenv("SHOPIFY_API_VERSION", "2025-04")
        
        if shopify_shop_url and shopify_access_token:
            clients["shopify"] = ShopifyClient(
                shop_url=shopify_shop_url,
                access_token=shopify_access_token,
                api_version=shopify_api_version,
                gateway=third_party_gateway
            )
            span.set_attribute("shopify_client_initialized", True)
            logger.info("Shopify client initialized")
        
        # Initialize Teller client if credentials are available
        teller_access_token = os.getenv("TELLER_ACCESS_TOKEN")
        teller_environment = os.getenv("TELLER_ENVIRONMENT", "sandbox")
        
        if teller_access_token:
            clients["teller"] = TellerClient(
                access_token=teller_access_token,
                environment=teller_environment,
                gateway=third_party_gateway
            )
            span.set_attribute("teller_client_initialized", True)
            logger.info("Teller client initialized")
        
        span.set_status(Status(StatusCode.OK))
        
    return clients

async def cleanup_mcp_clients():
    """Clean up all MCP clients properly."""
    tracer = trace.get_tracer("ru_twin_mcp")
    
    with tracer.start_as_current_span("cleanup_mcp_clients") as span:
        for client_name, client in mcp_clients.items():
            # Only call cleanup for MCPClient instances
            if isinstance(client, MCPClient):
                try:
                    await client.cleanup()
                    logger.info(f"MCP client {client_name} cleaned up")
                except Exception as e:
                    span.record_exception(e)
                    logger.error(f"Error cleaning up MCP client {client_name}: {e}")

async def run_crew_async(task_name: str, config_dir: str = "src/ru_twin/config") -> Any:
    """
    Run a specific task with the CrewAI crew asynchronously.
    
    Args:
        task_name: Name of the task to run
        config_dir: Directory containing configuration files
        
    Returns:
        Result of the task execution
    """
    # Load configurations
    agents_config = load_config(f"{config_dir}/agents.yaml")
    tasks_config = load_config(f"{config_dir}/tasks.yaml")
    
    # Load additional task configurations if they exist
    shopify_tasks_path = f"{config_dir}/shopify_tasks.yaml"
    teller_tasks_path = f"{config_dir}/teller_tasks.yaml"
    
    if os.path.exists(shopify_tasks_path):
        shopify_tasks = load_config(shopify_tasks_path)
        tasks_config.update(shopify_tasks)
        
    if os.path.exists(teller_tasks_path):
        teller_tasks = load_config(teller_tasks_path)
        tasks_config.update(teller_tasks)
    
    # Get MCP clients if not already initialized
    global mcp_clients
    if not mcp_clients:
        mcp_clients = await init_mcp_clients()
    
    # Create and run the crew
    search_tool = SerperDevTool()
    session_id = str(uuid.uuid4())
    tracer = trace.get_tracer(__name__)

    with tracer.start_as_current_span(
        name=f"run_crew_{task_name}", 
        attributes={
            SpanAttributes.OPENINFERENCE_SPAN_KIND: "agent",
            "task_name": task_name,
            "session_id": session_id
        }
    ) as span:
        try:
            crew = create_crew(
                agents_config=agents_config,
                tasks_config=tasks_config,
                task_name=task_name,
                tool_registry=tool_registry,
                a2a_messenger=a2a_messenger,
                mcp_clients=mcp_clients
            )
            
            result = crew.kickoff()
            span.set_status(Status(StatusCode.OK))
            return result
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            logger.exception(f"Error running crew task {task_name}", exc_info=e)
            raise

def run_crew(task_name: str, config_dir: str = "src/ru_twin/config") -> Any:
    """
    Synchronous wrapper for running a CrewAI task.
    
    Args:
        task_name: Name of the task to run
        config_dir: Directory containing configuration files
        
    Returns:
        Result of the task execution
    """
    return asyncio.run(run_crew_async(task_name, config_dir))

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application startup and shutdown."""
    global tool_registry, third_party_gateway, a2a_messenger, mcp_clients
    
    # Initialize OpenTelemetry
    init_opentelemetry()

    # Initialize core components
    tool_registry = init_tool_registry()
    third_party_gateway = init_third_party_gateway(tool_registry)
    a2a_messenger = init_a2a_messenger(tool_registry)
    
    # Initialize MCP clients
    mcp_clients = await init_mcp_clients()
    
    logger.info("Application startup complete")
    
    yield
    
    # Cleanup logic
    await cleanup_mcp_clients()
    
    logger.info("Application shutdown complete")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="RuTwin Crew API",
    description="API for RuTwin Crew, an AI-powered task management system",
    version="0.1.0",
    lifespan=lifespan
)

# Instrument the FastAPI app right after creation
FastAPIInstrumentor.instrument_app(app)
logger.info("FastAPI app instrumented with OpenTelemetry")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.post("/run_task/{task_name}")
async def run_task_endpoint(task_name: str, request: Request, background_tasks: BackgroundTasks):
    """API endpoint to run a specific task."""
    try:
        # Run the task asynchronously to not block the API response
        result = await run_crew_async(task_name)
        return {"task": task_name, "status": "completed", "result": result}
    except Exception as e:
        logger.exception(f"Error running task {task_name}", exc_info=e)
        return JSONResponse(
            status_code=500,
            content={"task": task_name, "status": "failed", "error": str(e)}
        )

@app.post("/mcp/{client_name}/call_tool")
async def call_mcp_tool(client_name: str, request: Request):
    """API endpoint to call a specific tool on an MCP client."""
    try:
        body = await request.json()
        tool_name = body.get("tool_name")
        tool_args = body.get("tool_args", {})
        
        if not tool_name:
            return JSONResponse(
                status_code=400,
                content={"status": "failed", "error": "tool_name is required"}
            )
        
        if client_name not in mcp_clients:
            return JSONResponse(
                status_code=404,
                content={"status": "failed", "error": f"MCP client '{client_name}' not found"}
            )
        
        client = mcp_clients[client_name]
        
        # Only call on MCPClient instances
        if isinstance(client, MCPClient):
            tracer = trace.get_tracer("ru_twin_api")
            with tracer.start_as_current_span(f"api_call_tool_{client_name}_{tool_name}") as span:
                span.set_attribute("client_name", client_name)
                span.set_attribute("tool_name", tool_name)
                span.set_attribute("tool_args", json.dumps(tool_args))
                
                result = await client.call_tool(tool_name, tool_args)
                return {"status": "success", "result": result}
        else:
            # For non-MCPClient instances, use a different approach
            return JSONResponse(
                status_code=400,
                content={"status": "failed", "error": f"Client '{client_name}' is not an MCP client"}
            )
            
    except Exception as e:
        logger.exception(f"Error calling tool on MCP client {client_name}", exc_info=e)
        return JSONResponse(
            status_code=500,
            content={"status": "failed", "error": str(e)}
        )

@app.get("/mcp/{client_name}/tools")
async def list_mcp_tools(client_name: str):
    """API endpoint to list available tools for an MCP client."""
    try:
        if client_name not in mcp_clients:
            return JSONResponse(
                status_code=404,
                content={"status": "failed", "error": f"MCP client '{client_name}' not found"}
            )
        
        client = mcp_clients[client_name]
        
        # Only call on MCPClient instances
        if isinstance(client, MCPClient):
            tool_names = await client.get_current_tool_names()
            return {"status": "success", "tools": tool_names}
        else:
            # For non-MCPClient instances, use a different approach
            return JSONResponse(
                status_code=400,
                content={"status": "failed", "error": f"Client '{client_name}' is not an MCP client"}
            )
            
    except Exception as e:
        logger.exception(f"Error listing tools for MCP client {client_name}", exc_info=e)
        return JSONResponse(
            status_code=500,
            content={"status": "failed", "error": str(e)}
        )

@app.post("/chat/{client_name}")
async def chat_with_mcp(client_name: str, request: Request):
    """API endpoint to have a single chat interaction with an MCP client."""
    try:
        body = await request.json()
        user_question = body.get("question")
        
        if not user_question:
            return JSONResponse(
                status_code=400,
                content={"status": "failed", "error": "question is required"}
            )
        
        if client_name not in mcp_clients:
            return JSONResponse(
                status_code=404,
                content={"status": "failed", "error": f"MCP client '{client_name}' not found"}
            )
        
        client = mcp_clients[client_name]
        
        # Only process chat for MCPClient instances
        if isinstance(client, MCPClient):
            tracer = trace.get_tracer("ru_twin_chat")
            
            with tracer.start_as_current_span("chat_interaction") as chat_span:
                chat_span.set_attribute("client_name", client_name)
                chat_span.set_attribute("user_input", user_question)
                
                # Add the user message to the client's message history
                client.messages.append({
                    "role": "user",
                    "content": user_question
                })
                
                # Get available tools
                response = await client.session.list_tools()
                available_tools = [{ 
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                } for tool in response.tools]
                
                # Make LLM call
                with tracer.start_as_current_span("llm_call") as llm_span:
                    llm_span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, "llm")
                    llm_span.set_attribute("model", "claude-3-7-sonnet-20250219")
                    
                    response = client.anthropic.messages.create(
                        model="claude-3-7-sonnet-20250219",
                        max_tokens=1000,
                        system=client.system_prompt,
                        messages=client.messages,
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
                        with tracer.start_as_current_span(f"tool_execution_{tool_name}") as tool_span:
                            tool_span.set_attribute("tool.name", tool_name)
                            tool_span.set_attribute("tool.args", json.dumps(tool_args))
                            tool_span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, "tool")
                            
                            result = await client.session.call_tool(tool_name, tool_args)
                            tool_results.append({"call": tool_name, "result": result})
                            
                            # Add the tool call and result to the message history
                            client.messages.append({
                                "role": "assistant", 
                                "content": f"Calling tool {tool_name} with args {tool_args}, the result is: " + "\n".join([x.text for x in result.content])
                            })

                        # Follow-up LLM call after tool use
                        with tracer.start_as_current_span("llm_call_after_tool") as follow_llm_span:
                            follow_llm_span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, "llm")
                            follow_llm_span.set_attribute("model", "claude-3-7-sonnet-20250219")
                            follow_llm_span.set_attribute("after_tool", tool_name)
                            
                            follow_response = client.anthropic.messages.create(
                                model="claude-3-7-sonnet-20250219",
                                max_tokens=1000,
                                system=client.system_prompt,
                                messages=client.messages,
                            )
                            
                            final_text.append(follow_response.content[0].text)
                            follow_llm_span.set_attribute("tokens_used", follow_response.usage.output_tokens + follow_response.usage.input_tokens)
                
                # Add the final response to the client's message history
                if final_text:
                    client.messages.append({
                        "role": "assistant",
                        "content": "\n".join(final_text)
                    })
                
                # Set overall metrics for this interaction
                chat_span.set_attribute("tool_calls_count", len(tool_results))
                chat_span.set_attribute("total_responses", len(final_text))
                
                return {
                    "status": "success", 
                    "response": "\n".join(final_text),
                    "tool_calls": len(tool_results)
                }
        else:
            return JSONResponse(
                status_code=400,
                content={"status": "failed", "error": f"Client '{client_name}' is not an MCP client"}
            )
            
    except Exception as e:
        logger.exception(f"Error in chat with MCP client {client_name}", exc_info=e)
        return JSONResponse(
            status_code=500,
            content={"status": "failed", "error": str(e)}
        )
    
async def process_natural_language_request(message: str, tracer) -> JSONResponse:
    """
    Process a natural language request by:
    1. Determining the user's intent
    2. Selecting the appropriate client
    3. Executing the relevant action
    
    Args:
        message: Natural language message from the user
        tracer: OpenTelemetry tracer for observability
        
    Returns:
        JSON response with the result of the operation
    """
    with tracer.start_as_current_span("process_natural_language") as nlp_span:
        nlp_span.set_attribute("user_message", message)
        
        # Initialize Anthropic client for intent classification
        # This assumes a global Anthropic client is already set up or use this pattern:
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        anthropic_client = Anthropic(api_key=anthropic_api_key)
        
        # Build a prompt to determine intent and extract parameters
        prompt = [
            {
                "role": "user",
                "content": f"""Analyze this user message and determine the most appropriate action and parameters:
                
                User message: "{message}"
                
                Available actions:
                1. "health_check" - Check system health
                2. "run_task" - Execute a specific CrewAI task
                3. "call_tool" - Call a specific tool on an MCP client
                4. "list_tools" - List available tools for an MCP client
                5. "chat" - Have a conversational interaction with an MCP client
                
                Available MCP clients: {list(mcp_clients.keys())}
                
                Provide your analysis in the following JSON format:
                {{
                  "action": [one of the actions above],
                  "client_name": [relevant MCP client name if applicable],
                  "task_name": [task name if action is run_task],
                  "tool_name": [tool name if action is call_tool],
                  "tool_args": [arguments as a JSON object if action is call_tool],
                  "question": [reformulated question if action is chat]
                }}
                
                Only include fields that are relevant to the chosen action.
                """
            }
        ]
        
        with tracer.start_as_current_span("intent_classification") as intent_span:
            intent_span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, "llm")
            intent_span.set_attribute("model", "claude-3-7-sonnet-20250219")
            
            # Make LLM call to determine intent
            response = anthropic_client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=1000,
                messages=prompt
            )
            
            # Extract JSON from the response
            response_text = response.content[0].text
            
            # Find JSON structure in the response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            
            if json_match:
                try:
                    parsed_intent = json.loads(json_match.group(0))
                    
                    # Add intent classification results to the span
                    for key, value in parsed_intent.items():
                        if isinstance(value, (str, int, float, bool)) or value is None:
                            intent_span.set_attribute(f"intent.{key}", str(value))
                    
                    # Now use the parsed intent to route to the appropriate action
                    action = parsed_intent.get("action")
                    
                    if not action:
                        return JSONResponse(
                            status_code=400,
                            content={"status": "failed", "error": "Could not determine action from message"}
                        )
                    
                    # Create a synthetic request body with the parsed intent
                    synthetic_body = {
                        "action": action,
                        **{k: v for k, v in parsed_intent.items() if k != "action" and v is not None}
                    }
                    
                    # Recursively call the same function with the synthetic structured request
                    # This is done by creating a mock Request object with our synthetic body
                    from fastapi import Request
                    from fastapi.datastructures import Headers
                    
                    class MockRequest(Request):
                        async def json(self):
                            return synthetic_body
                    
                    mock_request = MockRequest(
                        scope={"type": "http", "headers": []},
                        receive=None,
                        send=None
                    )
                    
                    # Add the original message to the synthetic body for reference
                    synthetic_body["original_message"] = message
                    
                    nlp_span.set_attribute("routed_to_action", action)
                    return await unified_api_endpoint(mock_request)
                
                except json.JSONDecodeError as e:
                    intent_span.record_exception(e)
                    return JSONResponse(
                        status_code=500,
                        content={"status": "failed", "error": f"Failed to parse intent: {e}"}
                    )
            else:
                return JSONResponse(
                    status_code=500,
                    content={"status": "failed", "error": "Could not determine intent from message"}
                )@app.post("/api")
async def unified_api_endpoint(request: Request):
    """
    Unified API endpoint that consolidates all RuTwin functionality.
    
    The endpoint accepts two types of requests:
    
    1. Natural language request:
    {
        "message": "Show me the latest orders from Shopify"
    }
    
    2. Structured request:
    {
        "action": "call_tool",
        "client_name": "shopify",
        "tool_name": "list_orders",
        "tool_args": {"limit": 10}
    }
    
    For natural language requests, the system will:
    - Parse the intent
    - Identify the appropriate client
    - Route to relevant functionality
    - Process the request
    
    For structured requests, the following parameters are used:
    - action: The type of action to perform (run_task, call_tool, list_tools, chat, health_check)
    - client_name: Name of the MCP client to use (required for call_tool, list_tools, chat)
    - task_name: Name of the task to run (required for run_task)
    - tool_name: Name of the tool to call (required for call_tool)
    - tool_args: Arguments for the tool (required for call_tool)
    - question: User question for chat interaction (required for chat)
    
    Returns:
        JSON response with the result of the operation
    """
    tracer = trace.get_tracer("ru_twin_unified_api")
    
    try:
        body = await request.json()
        
        # Check if this is a natural language request
        if "message" in body and isinstance(body["message"], str):
            # Process natural language input
            return await process_natural_language_request(body["message"], tracer)
        
        # Otherwise, treat as structured request
        action = body.get("action")
        
        if not action:
            return JSONResponse(
                status_code=400,
                content={"status": "failed", "error": "Either 'message' or 'action' is required"}
            )
        
        # Extract common parameters
        client_name = body.get("client_name")
        
        # Create a span for this API call
        with tracer.start_as_current_span(f"unified_api_{action}") as span:
            span.set_attribute("action", action)
            span.set_attribute("client_name", client_name)
            
            # Route to appropriate functionality based on action
            if action == "health_check":
                return {"status": "healthy"}
                
            elif action == "run_task":
                task_name = body.get("task_name")
                if not task_name:
                    return JSONResponse(
                        status_code=400,
                        content={"status": "failed", "error": "task_name is required for run_task action"}
                    )
                
                span.set_attribute("task_name", task_name)
                result = await run_crew_async(task_name)
                return {"action": action, "task": task_name, "status": "completed", "result": result}
                
            elif action == "call_tool":
                tool_name = body.get("tool_name")
                tool_args = body.get("tool_args", {})
                
                if not client_name:
                    return JSONResponse(
                        status_code=400,
                        content={"status": "failed", "error": "client_name is required for call_tool action"}
                    )
                
                if not tool_name:
                    return JSONResponse(
                        status_code=400,
                        content={"status": "failed", "error": "tool_name is required for call_tool action"}
                    )
                
                if client_name not in mcp_clients:
                    return JSONResponse(
                        status_code=404,
                        content={"status": "failed", "error": f"MCP client '{client_name}' not found"}
                    )
                
                client = mcp_clients[client_name]
                
                span.set_attribute("tool_name", tool_name)
                span.set_attribute("tool_args", json.dumps(tool_args))
                
                # Only call on MCPClient instances
                if isinstance(client, MCPClient):
                    result = await client.call_tool(tool_name, tool_args)
                    return {"action": action, "status": "success", "result": result}
                else:
                    return JSONResponse(
                        status_code=400,
                        content={"status": "failed", "error": f"Client '{client_name}' is not an MCP client"}
                    )
                    
            elif action == "list_tools":
                if not client_name:
                    return JSONResponse(
                        status_code=400,
                        content={"status": "failed", "error": "client_name is required for list_tools action"}
                    )
                
                if client_name not in mcp_clients:
                    return JSONResponse(
                        status_code=404,
                        content={"status": "failed", "error": f"MCP client '{client_name}' not found"}
                    )
                
                client = mcp_clients[client_name]
                
                # Only call on MCPClient instances
                if isinstance(client, MCPClient):
                    tool_names = await client.get_current_tool_names()
                    return {"action": action, "status": "success", "tools": tool_names}
                else:
                    return JSONResponse(
                        status_code=400,
                        content={"status": "failed", "error": f"Client '{client_name}' is not an MCP client"}
                    )
                    
            elif action == "chat":
                user_question = body.get("question")
                
                if not client_name:
                    return JSONResponse(
                        status_code=400,
                        content={"status": "failed", "error": "client_name is required for chat action"}
                    )
                
                if not user_question:
                    return JSONResponse(
                        status_code=400,
                        content={"status": "failed", "error": "question is required for chat action"}
                    )
                
                if client_name not in mcp_clients:
                    return JSONResponse(
                        status_code=404,
                        content={"status": "failed", "error": f"MCP client '{client_name}' not found"}
                    )
                
                client = mcp_clients[client_name]
                span.set_attribute("user_input", user_question)
                
                # Only process chat for MCPClient instances
                if isinstance(client, MCPClient):                    
                    # Add the user message to the client's message history
                    client.messages.append({
                        "role": "user",
                        "content": user_question
                    })
                    
                    # Get available tools
                    response = await client.session.list_tools()
                    available_tools = [{ 
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema
                    } for tool in response.tools]
                    
                    # Make LLM call
                    with tracer.start_as_current_span("llm_call") as llm_span:
                        llm_span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, "llm")
                        llm_span.set_attribute("model", "claude-3-7-sonnet-20250219")
                        
                        # Check if this came from a natural language request
                        original_message = body.get("original_message")
                        if original_message:
                            # Add a hint to the system prompt when processing from natural language
                            enhanced_system_prompt = client.system_prompt + f"\nThe user's original request was: '{original_message}'. Try to address this request comprehensively."
                            
                            response = client.anthropic.messages.create(
                                model="claude-3-7-sonnet-20250219",
                                max_tokens=1000,
                                system=enhanced_system_prompt,
                                messages=client.messages,
                                tools=available_tools
                            )
                        else:
                            response = client.anthropic.messages.create(
                                model="claude-3-7-sonnet-20250219",
                                max_tokens=1000,
                                system=client.system_prompt,
                                messages=client.messages,
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
                            with tracer.start_as_current_span(f"tool_execution_{tool_name}") as tool_span:
                                tool_span.set_attribute("tool.name", tool_name)
                                tool_span.set_attribute("tool.args", json.dumps(tool_args))
                                tool_span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, "tool")
                                
                                result = await client.session.call_tool(tool_name, tool_args)
                                tool_results.append({"call": tool_name, "result": result})
                                
                                # Add the tool call and result to the message history
                                client.messages.append({
                                    "role": "assistant", 
                                    "content": f"Calling tool {tool_name} with args {tool_args}, the result is: " + "\n".join([x.text for x in result.content])
                                })

                            # Follow-up LLM call after tool use
                            with tracer.start_as_current_span("llm_call_after_tool") as follow_llm_span:
                                follow_llm_span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, "llm")
                                follow_llm_span.set_attribute("model", "claude-3-7-sonnet-20250219")
                                follow_llm_span.set_attribute("after_tool", tool_name)
                                
                                follow_response = client.anthropic.messages.create(
                                    model="claude-3-7-sonnet-20250219",
                                    max_tokens=1000,
                                    system=client.system_prompt,
                                    messages=client.messages,
                                )
                                
                                final_text.append(follow_response.content[0].text)
                                follow_llm_span.set_attribute("tokens_used", follow_response.usage.output_tokens + follow_response.usage.input_tokens)
                    
                    # Add the final response to the client's message history
                    if final_text:
                        client.messages.append({
                            "role": "assistant",
                            "content": "\n".join(final_text)
                        })
                    
                    # Set overall metrics for this interaction
                    span.set_attribute("tool_calls_count", len(tool_results))
                    span.set_attribute("total_responses", len(final_text))
                    
                    return {
                        "action": action,
                        "status": "success", 
                        "response": "\n".join(final_text),
                        "tool_calls": len(tool_results),
                        "tool_results": tool_results
                    }
                else:
                    return JSONResponse(
                        status_code=400,
                        content={"status": "failed", "error": f"Client '{client_name}' is not an MCP client"}
                    )
            
            # If action is not recognized
            else:
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "failed", 
                        "error": f"Unknown action '{action}'. Supported actions: run_task, call_tool, list_tools, chat, health_check"
                    }
                )
                
    except Exception as e:
        logger.exception(f"Error in unified API endpoint", exc_info=e)
        return JSONResponse(
            status_code=500,
            content={"status": "failed", "error": str(e)}
        )
    
async def run_main_async(args):
    """Asynchronous main function."""
    global tool_registry, third_party_gateway, a2a_messenger, mcp_clients
    
    # Initialize OpenTelemetry
    init_opentelemetry()
    
    # Initialize core components
    tool_registry = init_tool_registry()
    third_party_gateway = init_third_party_gateway(tool_registry)
    a2a_messenger = init_a2a_messenger(tool_registry)
    
    # Initialize MCP clients
    mcp_clients = await init_mcp_clients()
    
    if args.task:
        # Run a specific task
        result = await run_crew_async(args.task)
        print(f"Task '{args.task}' completed with result: {result}")

    # Only call cleanup if we've initialized clients
    await cleanup_mcp_clients()

def main():
    """Main entry point for the application."""
    # Load environment variables
    load_dotenv()
    parser = argparse.ArgumentParser(description="RuTwin Crew - AI Task Management System")
    parser.add_argument("--task", type=str, help="Name of the task to run")
    parser.add_argument("--server", action="store_true", help="Run as a FastAPI server")
    parser.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Server host (default: 0.0.0.0)")
    parser.add_argument("--test", action="store_true", help="Run in test mode")
    args = parser.parse_args()
    
    # Run the application
    if args.server:
        # Run as a FastAPI server
        uvicorn.run(app, host=args.host, port=args.port)
    elif args.task:
        # Run a specific task using async
        asyncio.run(run_main_async(args))
    elif args.test:
        # Run in test mode
        print("Running in test mode")
        # Add test logic here
    else:
        parser.print_help()

if __name__ == "__main__":
    main()