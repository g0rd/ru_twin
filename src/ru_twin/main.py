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
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

import yaml
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import structlog
import uvicorn
import phoenix as px

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

def init_opentelemetry() -> None:
    """Initialize OpenTelemetry for tracing and metrics."""
    # Get OTLP endpoint from environment or use default Phoenix endpoint
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://phoenix:4317")
    service_name = os.getenv("OTEL_SERVICE_NAME", "ru_twin")
    
    # Create a resource to identify the service
    resource = Resource.create({"service.name": service_name})
    
    # Initialize TracerProvider with the resource
    tracer_provider = TracerProvider(resource=resource)
    
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

# Initialize OpenTelemetry at module level
init_opentelemetry()

# Global variables
tool_registry = None
third_party_gateway = None
a2a_messenger = None
phoenix_client = None



def init_phoenix() -> Optional[Any]:
    """
    Initialize the Arize Phoenix client.
    
    Returns:
        Optional[px.Client]: Phoenix client instance or None if initialization fails
    """
    try:
        # Get Phoenix endpoint from environment or use default
        phoenix_endpoint = os.getenv("PHOENIX_CLIENT_ENDPOINT", "https://app.phoenix.arize.com")
        
        # Get Phoenix headers from environment
        phoenix_headers_str = os.getenv("PHOENIX_CLIENT_HEADERS")
        phoenix_headers = {}
        
        # Parse headers if provided
        if phoenix_headers_str:
            # Split by comma to get key=value pairs
            header_pairs = phoenix_headers_str.split(",")
            for pair in header_pairs:
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    phoenix_headers[key.strip()] = value.strip()
        
        if not phoenix_headers:
            logger.warning("No Phoenix headers found. Phoenix client may not authenticate properly.")
        
        # Initialize Phoenix client
        client = px.Client(endpoint=phoenix_endpoint, headers=phoenix_headers)
        logger.info("Phoenix client initialized", endpoint=phoenix_endpoint)
        return client
    except ImportError:
        logger.warning("Arize Phoenix library not installed. Phoenix client not initialized.")
        return None
    except Exception as e:
        logger.error(f"Error initializing Phoenix client: {e}")
        return None


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
    
    # Register any additional tools here
    
    logger.info(f"Tool registry initialized with {len(registry.get_all_tools())} tools")
    return registry


def init_third_party_gateway(registry: ToolRegistry) -> ThirdPartyAgentGateway:
    """Initialize the third-party gateway."""
    return ThirdPartyAgentGateway(registry=registry)


def init_a2a_messenger(registry: ToolRegistry) -> AgentMessenger:
    """Initialize the Agent-to-Agent messenger."""
    return AgentMessenger(agent_registry=registry)


def init_mcp_clients() -> Dict[str, Any]:
    """Initialize MCP clients for external services."""
    clients = {}
    
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
        logger.info("Teller client initialized")
    
    return clients


def run_crew(task_name: str, config_dir: str = "src/ru_twin/config") -> Any:
    """
    Run a specific task with the CrewAI crew.
    
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
    
    # Get MCP clients
    mcp_clients = init_mcp_clients()
    
    # Create and run the crew
    with trace.get_tracer(__name__).start_as_current_span("run_crew"):
        crew = create_crew(
            agents_config=agents_config,
            tasks_config=tasks_config,
            task_name=task_name,
            tool_registry=tool_registry,
            a2a_messenger=a2a_messenger,
            mcp_clients=mcp_clients
        )
        
        # Log the crew execution with Phoenix
        if phoenix_client:
            # Create a trace for Phoenix
            with phoenix_client.start_trace(
                name=f"RuTwin Task: {task_name}",
                metadata={
                    "task_name": task_name,
                    "agents": list(agents_config.keys()),
                }
            ) as trace_context:
                result = crew.kickoff()
                
                # Log the result
                trace_context.add_event(
                    name="task_result",
                    metadata={"result": str(result)[:1000]}  # Truncate if too long
                )
                
                return result
        else:
            # Run without Phoenix tracing
            return crew.kickoff()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application startup and shutdown."""
    global tool_registry, third_party_gateway, a2a_messenger, phoenix_client
    
    # Initialize Phoenix client
    phoenix_client = init_phoenix()

    # Initialize core components
    tool_registry = init_tool_registry()
    third_party_gateway = init_third_party_gateway(tool_registry)
    a2a_messenger = init_a2a_messenger(tool_registry)
    
    logger.info("Application startup complete")
    
    yield
    
    # Cleanup logic
    if phoenix_client and hasattr(phoenix_client, 'close'):
        try:
            await phoenix_client.close()
            logger.info("Phoenix client closed")
        except Exception as e:
            logger.error(f"Error closing Phoenix client: {e}")
    
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
async def run_task_endpoint(task_name: str, request: Request):
    """API endpoint to run a specific task."""
    try:
        result = run_crew(task_name)
        return {"task": task_name, "status": "completed", "result": result}
    except Exception as e:
        logger.exception(f"Error running task {task_name}", exc_info=e)
        return JSONResponse(
            status_code=500,
            content={"task": task_name, "status": "failed", "error": str(e)}
        )




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
    
    if not args.server:
        # For non-server mode, initialize components directly
        init_opentelemetry() 
        
        global tool_registry, third_party_gateway, a2a_messenger, phoenix_client
        phoenix_client = init_phoenix()  # Initialize Phoenix for CLI mode
        tool_registry = init_tool_registry()
        third_party_gateway = init_third_party_gateway(tool_registry)
        a2a_messenger = init_a2a_messenger(tool_registry)
   
    
    # Run the application
    if args.server:
        # Run as a FastAPI server
        uvicorn.run(app, host=args.host, port=args.port)
    elif args.task:
        # Run a specific task
        result = run_crew(args.task)
        print(f"Task '{args.task}' completed with result: {result}")
    elif args.test:
        # Run in test mode
        print("Running in test mode")
        # Add test logic here
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
