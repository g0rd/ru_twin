from typing import Dict, Any, Optional
from pydantic import BaseModel
import aiohttp
import json
import os

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from openinference.semconv.trace import SpanAttributes

class ClientConfig(BaseModel):
    """Client configuration schema"""
    base_url: str = "http://localhost:8000"
    api_version: str = "v1"
    timeout: int = 30
    use_tracing: bool = True


class MCPClient:
    """Mission Control Platform Client with integrated tracing"""
    
    def __init__(self, config: Optional[ClientConfig] = None):
        self.config = config or ClientConfig()
        self._session: Optional[aiohttp.ClientSession] = None
        self.tracer = trace.get_tracer("mcp_client")
        self.propagator = TraceContextTextMapPropagator()
    
    async def __aenter__(self):
        with self.tracer.start_as_current_span("initialize_client") as span:
            self._session = aiohttp.ClientSession()
            span.set_attribute("base_url", self.config.base_url)
            span.set_status(Status(StatusCode.OK))
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        with self.tracer.start_as_current_span("close_client"):
            if self._session:
                await self._session.close()
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to MCP server with tracing"""
        if not self._session:
            raise RuntimeError("Client session not initialized. Use async with context.")
        
        url = f"{self.config.base_url}/api/{self.config.api_version}/{endpoint}"
        
        with self.tracer.start_as_current_span(f"{method.lower()}_{endpoint}") as span:
            span.set_attribute("http.method", method)
            span.set_attribute("http.url", url)
            
            # Inject trace context into HTTP headers if not present
            if "headers" not in kwargs:
                kwargs["headers"] = {}
            
            carrier = {}
            if self.config.use_tracing:
                self.propagator.inject(carrier)
                kwargs["headers"].update(carrier)
            
            try:
                async with self._session.request(method, url, **kwargs) as response:
                    span.set_attribute("http.status_code", response.status)
                    
                    if response.status >= 400:
                        error_data = await response.json()
                        error_message = error_data.get('message', str(response.status))
                        span.set_status(Status(StatusCode.ERROR, error_message))
                        raise Exception(f"Request failed: {error_message}")
                    
                    response_data = await response.json()
                    span.set_status(Status(StatusCode.OK))
                    return response_data
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Check server health with tracing"""
        with self.tracer.start_as_current_span("health_check") as span:
            try:
                result = await self._request("GET", "health")
                span.set_attribute("health_status", result.get("status", "unknown"))
                return result
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    async def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool on the server with tracing"""
        with self.tracer.start_as_current_span("execute_tool") as span:
            span.set_attribute("tool.name", tool_name)
            span.set_attribute("tool.input", json.dumps(tool_input))
            span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, "tool")
            
            try:
                result = await self._request(
                    "POST",
                    f"tools/{tool_name}/execute",
                    json=tool_input
                )
                span.set_status(Status(StatusCode.OK))
                return result
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise


def initialize_tracing(service_name="mcp_client"):
    """
    Helper function to initialize OpenTelemetry tracing with Phoenix
    
    This should be called before using the client if tracing is desired
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

__all__ = ['MCPClient', 'ClientConfig', 'client', 'initialize_tracing']