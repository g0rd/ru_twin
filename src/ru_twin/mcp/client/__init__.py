"""MCP Client implementation with enhanced functionality."""

# Import here to make these available when importing from mcp.client
from .client import MCPClient
from .config import ClientConfig
from .session import ClientSession
from .enhanced_session import EnhancedMCPSession, format_tools_for_anthropic, parse_tool_result
from .sse import sse_client

def initialize_tracing(service_name: str = "mcp_client") -> bool:
    """
    Helper function to initialize OpenTelemetry tracing with Phoenix.
    
    Args:
        service_name: Name of the service for tracing purposes.
        
    Returns:
        bool: True if tracing was initialized successfully, False otherwise.
    """
    try:
        # Import Phoenix and register it
        import phoenix as px
        from phoenix.otel import register
        from openinference.instrumentation.aiohttp import AioHttpClientInstrumentor
        
        # Launch Phoenix app
        session = px.launch_app().view()
        
        # Register the tracer provider
        tracer_provider = register(endpoint="http://localhost:6006/v1/traces")
        
        # Instrument aiohttp client
        AioHttpClientInstrumentor().instrument(tracer_provider=tracer_provider)
        
        return True
    except ImportError:
        print("Phoenix or related libraries not installed. Tracing will not be available.")
        return False
    except Exception as e:
        print(f"Error initializing tracing: {e}")
        return False

# Create default client instance
client = MCPClient()

__all__ = [
    'MCPClient',
    'ClientConfig',
    'ClientSession',
    'EnhancedMCPSession',
    'format_tools_for_anthropic',
    'parse_tool_result',
    'client',
    'initialize_tracing',
    'sse_client',
]