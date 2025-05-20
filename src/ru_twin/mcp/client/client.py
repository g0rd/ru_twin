"""MCP Client implementation with enhanced functionality."""

import asyncio
import json
import logging
import os
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from contextlib import AsyncExitStack
import aiohttp
import yaml

from anthropic import Anthropic
from dotenv import load_dotenv
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from openinference.semconv.trace import SpanAttributes

# Local imports
from .session import ClientSession
from .enhanced_session import EnhancedMCPSession
from .sse import sse_client
from .config import ClientConfig

# Set up logging
logger = logging.getLogger(__name__)

# Import here to avoid circular imports
if TYPE_CHECKING:
    from .enhanced_session import EnhancedMCPSession  # noqa: F401

load_dotenv()

class MCPClient:
    """MCP Client with enhanced functionality for interacting with MCP servers."""
    
    def __init__(self, name: str = "default", config: Optional[ClientConfig] = None):
        """Initialize the MCP client.
        
        Args:
            name: A name for this client instance (used for logging and tracing)
            config: Configuration for the client. If not provided, defaults will be used.
        """
        self.name = name
        self.config = config or ClientConfig()
        self.tracer = trace.get_tracer("mcp_client")
        self.propagator = TraceContextTextMapPropagator()
        
        # Async context management
        self._exit_stack = AsyncExitStack()
        
        # Session management
        self._http_session: Optional[aiohttp.ClientSession] = None
        self._session: Optional[ClientSession] = None
        self._enhanced_session: Optional[EnhancedMCPSession] = None
        
        # State tracking
        self._initialized = False
        self._initializing = False
        self._init_lock = asyncio.Lock()
        
        # Initialize Anthropic client if API key is available
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            self.anthropic = Anthropic(api_key=api_key)
        else:
            self.anthropic = None
            logger.warning(
                "ANTHROPIC_API_KEY environment variable not set. "
                "Some features may not be available."
            )
        
        # Default system prompt
        self.system_prompt = (
            "You are a helpful assistant that can help with various tasks. "
            "You carefully explain any action you have taken. "
            "When using tools, describe what you're doing and why."
        )
        
        # Conversation history
        self.messages: List[Dict[str, str]] = []
        
        logger.info(f"Initialized MCPClient '{name}'")

    async def __aenter__(self):
        """Enter the async context manager.
        
        This will initialize the client and ensure all resources are properly set up.
        
        Returns:
            The initialized MCPClient instance.
        """
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc, tb):
        """Exit the async context manager and clean up resources.
        
        Args:
            exc_type: Exception type if an exception was raised
            exc: Exception instance if an exception was raised
            tb: Traceback if an exception was raised
        """
        await self.cleanup()
        
    async def initialize(self):
        """Initialize the MCP client session.
        
        This method is idempotent and thread-safe.
        """
        if self._initialized:
            return
            
        async with self._init_lock:
            if self._initialized:  # Double-checked locking pattern
                return
                
            if self._initializing:  # Prevent reentrant initialization
                raise RuntimeError("Initialization already in progress")
                
            self._initializing = True
            
            # Create a tracing span for initialization
            with self.tracer.start_as_current_span("mcp_client_initialize") as span:
                try:
                    logger.info(f"Initializing MCP client '{self.name}'...")
                    
                    # Create HTTP session
                    timeout = aiohttp.ClientTimeout(total=self.config.timeout)
                    self._http_session = aiohttp.ClientSession(timeout=timeout)
                    await self._exit_stack.enter_async_context(self._http_session)
                    
                    # Create base session
                    self._session = ClientSession()
                    await self._exit_stack.enter_async_context(self._session)
                    
                    # Create enhanced session
                    self._enhanced_session = EnhancedMCPSession(self._session)
                    await self._enhanced_session.initialize()
                    
                    # Mark as initialized
                    self._initialized = True
                    logger.info(f"MCP client '{self.name}' initialized successfully")
                    
                    # Set span attributes
                    span.set_attribute("mcp.client_name", self.name)
                    span.set_status(Status(StatusCode.OK))
                    
                except Exception as e:
                    error_msg = f"Failed to initialize MCP client: {e}"
                    logger.error(error_msg)
                    if 'span' in locals():
                        span.record_exception(e)
                        span.set_status(Status(StatusCode.ERROR, error_msg))
                    await self.cleanup()
                    raise
                    
                finally:
                    self._initializing = False

    async def cleanup(self):
        """Clean up resources.
        
        This method is idempotent and can be called multiple times safely.
        """
        if not self._initialized and not self._initializing:
            return
            
        async with self._init_lock:
            if not self._initialized and not self._initializing:
                return
                
            # Create a tracing span for cleanup
            with self.tracer.start_as_current_span("mcp_client_cleanup") as span:
                try:
                    logger.info(f"Cleaning up MCP client '{self.name}'...")
                    
                    # Clean up enhanced session
                    if self._enhanced_session is not None:
                        try:
                            if hasattr(self._enhanced_session, 'close') and callable(self._enhanced_session.close):
                                await self._enhanced_session.close()
                        except Exception as e:
                            logger.warning(f"Error closing enhanced session: {e}")
                        finally:
                            self._enhanced_session = None
                    
                    # Clean up base session
                    if self._session is not None:
                        try:
                            if hasattr(self._session, '__aexit__'):
                                await self._session.__aexit__(None, None, None)
                        except Exception as e:
                            logger.warning(f"Error closing base session: {e}")
                        finally:
                            self._session = None
                    
                    # Clean up HTTP session
                    if self._http_session is not None:
                        try:
                            if not self._http_session.closed:
                                await self._http_session.close()
                        except Exception as e:
                            logger.warning(f"Error closing HTTP session: {e}")
                        finally:
                            self._http_session = None
                    
                    # Clean up exit stack
                    try:
                        await self._exit_stack.aclose()
                    except Exception as e:
                        logger.warning(f"Error cleaning up exit stack: {e}")
                    
                    # Reset state
                    self._initialized = False
                    self._initializing = False
                    
                    logger.info(f"MCP client '{self.name}' cleaned up successfully")
                    span.set_status(Status(StatusCode.OK))
                    
                except Exception as e:
                    error_msg = f"Error during MCP client cleanup: {e}"
                    logger.error(error_msg)
                    if 'span' in locals():
                        span.record_exception(e)
                        span.set_status(Status(StatusCode.ERROR, error_msg))
                    raise

    async def _ensure_initialized(self):
        """Ensure the client is initialized before making requests.
        
        This method will automatically initialize the client if it's not already initialized.
        
        Raises:
            RuntimeError: If the client fails to initialize.
        """
        if not self._initialized:
            if self._initializing:
                # If we're already initializing, wait a bit and check again
                await asyncio.sleep(0.1)
                if not self._initialized:
                    raise RuntimeError("MCPClient initialization is in progress")
            else:
                # Try to initialize
                try:
                    await self.initialize()
                except Exception as e:
                    raise RuntimeError(
                        f"Failed to initialize MCP client '{self.name}': {str(e)}"
                    ) from e
        
        # Verify that all required components are properly initialized
        if not self._initialized or self._session is None or self._enhanced_session is None:
            raise RuntimeError("MCPClient is not properly initialized. Please check your configuration and network connection.")

    async def _http_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an HTTP request to the MCP server.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            **kwargs: Additional arguments for aiohttp.ClientSession.request()
                - headers: Optional dict of headers
                - json: Optional JSON-serializable data for the request body
                - data: Optional form data for the request body
                - params: Optional query parameters
                - timeout: Optional timeout in seconds
                
        Returns:
            Dict or List containing the parsed JSON response, or str for non-JSON responses
            
        Raises:
            RuntimeError: If client is not properly initialized or session is closed
            aiohttp.ClientError: For HTTP/network related errors
            ValueError: If the response cannot be parsed as JSON
        """
        await self._ensure_initialized()
        
        if self._http_session is None or self._http_session.closed:
            raise RuntimeError(
                f"HTTP client session not available or closed for client '{self.name}'. "
                "This may happen if the client was not properly initialized or was already closed."
            )

        # Ensure endpoint is properly formatted
        endpoint = endpoint.strip('/')
        url = f"{self.config.base_url.rstrip('/')}/api/{self.config.api_version}/{endpoint}"
        
        # Set up headers
        headers = kwargs.pop('headers', {})
        if 'Content-Type' not in headers and 'json' in kwargs:
            headers['Content-Type'] = 'application/json'
        if 'Accept' not in headers:
            headers['Accept'] = 'application/json'
        
        # Add tracing headers if enabled
        if self.config.use_tracing:
            carrier = {}
            self.propagator.inject(carrier)
            headers.update(carrier)
        
        # Add timeout if not provided
        if 'timeout' not in kwargs:
            kwargs['timeout'] = aiohttp.ClientTimeout(total=self.config.timeout)
        
        # Create a tracing span for the request
        with self.tracer.start_as_current_span(f"mcp_http_{method.lower()}") as span:
            span.set_attributes({
                "http.method": method,
                "http.url": url,
                "http.request_headers": json.dumps(headers, default=str)
            })
            
            try:
                # Make the request
                async with self._http_session.request(
                    method, url, headers=headers, **kwargs
                ) as response:
                    # Log response status
                    response_headers = dict(response.headers)
                    span.set_attributes({
                        "http.status_code": response.status,
                        "http.response_headers": json.dumps(response_headers, default=str)
                    })
                    
                    # Read response content
                    content_type = response_headers.get('Content-Type', '').lower()
                    is_json = 'application/json' in content_type
                    
                    try:
                        if is_json:
                            result = await response.json()
                        else:
                            result = await response.text()
                    except (json.JSONDecodeError, aiohttp.ContentTypeError) as e:
                        error_msg = f"Failed to parse response as JSON: {str(e)}"
                        logger.warning(f"{error_msg}. Response content type: {content_type}")
                        result = await response.text()
                    
                    # Handle error responses
                    if response.status >= 400:
                        error_msg = f"HTTP {response.status}: {result if isinstance(result, str) else str(result)}"
                        logger.error(f"Request failed: {error_msg}")
                        span.record_exception(
                            Exception(error_msg),
                            attributes={"http.status_code": response.status}
                        )
                        span.set_status(Status(StatusCode.ERROR, error_msg))
                        raise aiohttp.ClientError(error_msg) from None
                    
                    span.set_status(Status(StatusCode.OK))
                    return result
                    
            except aiohttp.ClientError as e:
                error_msg = f"HTTP request failed: {str(e)}"
                logger.error(f"{error_msg} (URL: {url})")
                if 'span' in locals():
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, error_msg))
                raise
            except Exception as e:
                error_msg = f"Unexpected error during HTTP request: {str(e)}"
                logger.error(error_msg, exc_info=True)
                if 'span' in locals():
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, error_msg))
        
                raise

    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get all available tools with their schemas.
        
        This method retrieves the list of available tools from the MCP server.
        
        Returns:
            List[Dict[str, Any]]: A list of tool definitions, where each definition contains:
                - name (str): The name of the tool
                - description (str): A description of what the tool does
                - parameters (Dict): JSON Schema definition of the tool's parameters
                - required (List[str], optional): List of required parameter names
                
        Raises:
            RuntimeError: If the client is not properly initialized
            aiohttp.ClientError: For HTTP/network related errors
            ValueError: If the response cannot be parsed or is invalid
            
        Example:
            >>> tools = await client.get_available_tools()
            >>> for tool in tools:
            ...     print(f"Tool: {tool['name']}")
            ...     print(f"Description: {tool['description']}")
        """
        await self._ensure_initialized()
        
        # Use the enhanced session if available, otherwise fall back to HTTP
        if self._enhanced_session is not None:
            try:
                return await self._enhanced_session.list_tools()
            except Exception as e:
                logger.warning(
                    f"Failed to get tools from enhanced session: {e}. "
                    "Falling back to HTTP request.",
                    exc_info=True
                )
        
        # Fall back to HTTP request if enhanced session is not available or fails
        try:
            response = await self._http_request('GET', 'tools')
            
            # Validate the response format
            if not isinstance(response, list):
                raise ValueError("Invalid response format: expected a list of tools")
                
            # Validate each tool in the response
            for tool in response:
                if not isinstance(tool, dict):
                    raise ValueError(f"Invalid tool format: expected dict, got {type(tool).__name__}")
                if 'name' not in tool or not isinstance(tool['name'], str):
                    raise ValueError("Invalid tool: missing or invalid 'name' field")
                if 'description' not in tool or not isinstance(tool['description'], str):
                    raise ValueError(f"Tool '{tool.get('name', 'unknown')}' is missing or has an invalid 'description'")
            
            return response
            
        except aiohttp.ClientError:
            raise  # Re-raise HTTP/network errors
        except Exception as e:
            logger.error(f"Failed to parse tools response: {e}", exc_info=True)
            raise ValueError(f"Failed to parse tools response: {e}") from e

async def _ensure_initialized(self):
    """Ensure the client is initialized before making requests.
    
    This method will automatically initialize the client if it's not already initialized.
    
    Raises:
        RuntimeError: If the client fails to initialize.
    """
    if not self._initialized:
        if self._initializing:
            # If we're already initializing, wait a bit and check again
            await asyncio.sleep(0.1)
            if not self._initialized:
                raise RuntimeError("MCPClient initialization is in progress")
        else:
            # Try to initialize
            try:
                await self.initialize()
            except Exception as e:
                raise RuntimeError(
                    f"Failed to initialize MCP client '{self.name}': {str(e)}"
                ) from e
        
    # Verify that all required components are properly initialized
    if not self._initialized or self._session is None or self._enhanced_session is None:
        raise RuntimeError("MCPClient is not properly initialized. Please check your configuration and network connection.")

async def _http_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
    """Make an HTTP request to the MCP server.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint (without base URL)
        **kwargs: Additional arguments for aiohttp.ClientSession.request()
            - headers: Optional dict of headers
            - json: Optional JSON-serializable data for the request body
            - data: Optional form data for the request body
            - params: Optional query parameters
            - timeout: Optional timeout in seconds
            
    Returns:
        Dict or List containing the parsed JSON response, or str for non-JSON responses
            
    Raises:
        RuntimeError: If client is not properly initialized or session is closed
        aiohttp.ClientError: For HTTP/network related errors
        ValueError: If the response cannot be parsed as JSON
    """
    await self._ensure_initialized()
    
    if self._http_session is None or self._http_session.closed:
        raise RuntimeError(
            f"HTTP client session not available or closed for client '{self.name}'. "
            "This may happen if the client was not properly initialized or was already closed."
        )

    # Ensure endpoint is properly formatted
    endpoint = endpoint.strip('/')
    url = f"{self.config.base_url.rstrip('/')}/api/{self.config.api_version}/{endpoint}"
    
    # Set up headers
    headers = kwargs.pop('headers', {})
    if 'Content-Type' not in headers and 'json' in kwargs:
        headers['Content-Type'] = 'application/json'
    if 'Accept' not in headers:
        headers['Accept'] = 'application/json'
    
    # Add tracing headers if enabled
    if self.config.use_tracing:
        carrier = {}
        self.propagator.inject(carrier)
        headers.update(carrier)
    
    # Add timeout if not provided
    if 'timeout' not in kwargs:
        kwargs['timeout'] = aiohttp.ClientTimeout(total=self.config.timeout)
    
        # Create a tracing span for the request
        with self.tracer.start_as_current_span(f"mcp_http_{method.lower()}") as span:
            span.set_attributes({
                "http.method": method,
                "http.url": url,
                "http.request_headers": json.dumps(headers, default=str)
            })
            
            try:
                # Make the request
                async with self._http_session.request(
                    method, url, headers=headers, **kwargs
                ) as response:
                    # Log response status
                    response_headers = dict(response.headers)
                    span.set_attributes({
                        "http.status_code": response.status,
                        "http.response_headers": json.dumps(response_headers, default=str)
                    })
                    
                    # Read response content
                    content_type = response_headers.get('Content-Type', '').lower()
                    is_json = 'application/json' in content_type
                    
                    try:
                        if is_json:
                            result = await response.json()
                        else:
                            result = await response.text()
                    except (json.JSONDecodeError, aiohttp.ContentTypeError) as e:
                        error_msg = f"Failed to parse response as JSON: {str(e)}"
                        logger.warning(f"{error_msg}. Response content type: {content_type}")
                        result = await response.text()
                    
                    # Handle error responses
                    if response.status >= 400:
                        error_msg = f"HTTP {response.status}: {result if isinstance(result, str) else str(result)}"
                        logger.error(f"Request failed: {error_msg}")
                        span.record_exception(
                            Exception(error_msg),
                            attributes={"http.status_code": response.status}
                        )
                        span.set_status(Status(StatusCode.ERROR, error_msg))
                        raise aiohttp.ClientError(error_msg) from None
                    
                    span.set_status(Status(StatusCode.OK))
                    return result
                    
            except asyncio.TimeoutError as e:
                error_msg = f"Request to {url} timed out after {self.config.timeout} seconds"
                logger.error(error_msg)
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, error_msg))
                raise aiohttp.ClientError(error_msg) from e
                
            except aiohttp.ClientError as e:
                error_msg = f"HTTP request failed: {str(e)}"
                logger.error(f"{error_msg} (URL: {url})")
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, error_msg))
                raise
                
            except Exception as e:
                error_msg = f"Unexpected error during HTTP request: {str(e)}"
                logger.error(error_msg, exc_info=True)
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, error_msg))
                raise RuntimeError(error_msg) from e

    async def get_tool_names(self) -> List[str]:
        """Get list of available tool names."""
        tools = await self.get_available_tools()
        return [tool["name"] for tool in tools]

    async def call_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Any:
        """Call a specific tool with the given arguments."""
        with self.tracer.start_as_current_span("call_tool") as span:
            span.set_attribute("mcp.tool_name", tool_name)
            span.set_attribute("mcp.tool_args", json.dumps(tool_args))
            
            try:
                if self.config.use_sse and self._mcp_session:
                    # Validate arguments first
                    if not await self._mcp_session.validate_tool_args(tool_name, tool_args):
                        raise ValueError(f"Invalid arguments for tool '{tool_name}'")
                    
                    # Use the enhanced session's safe call method
                    result = await self._mcp_session.call_tool_safe(tool_name, tool_args)
                    span.set_attribute("mcp.result_type", "enhanced_session")
                    return result
                else:
                    result = await self._http_request("POST", f"tools/{tool_name}/execute", json=tool_args)
                    span.set_attribute("mcp.result_type", "http")
                    return result
                    
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise

    def _format_tools_for_anthropic(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format tools for the Anthropic API."""
        from ru_twin.mcp.client.enhanced_session import format_tools_for_anthropic
        return format_tools_for_anthropic(tools)

    async def process_user_message(self, user_input: str) -> str:
        """Process a single user message and return the response.
        
        This method handles the complete flow of processing a user message,
        including tool calls and response generation.
        
        Args:
            user_input: The user's message to process
            
        Returns:
            str: The assistant's response to the user
            
        Raises:
            RuntimeError: If the Anthropic client is not initialized
            aiohttp.ClientError: For network-related errors
            ValueError: If the response cannot be processed
        """
        if not self.anthropic:
            raise RuntimeError("Anthropic client is not initialized. Please check your API key.")
            
        # Add user message to conversation history
        self.messages.append({"role": "user", "content": user_input})
        
        with self.tracer.start_as_current_span("process_user_message") as span:
            try:
                # Get available tools
                tools = await self.get_available_tools()
                formatted_tools = self._format_tools_for_anthropic(tools)
                
                span.set_attributes({
                    "anthropic.model": "claude-3-7-sonnet-20250219",
                    "anthropic.tools_count": len(formatted_tools),
                    "user_message_length": len(user_input)
                })
                
                # Make the API call to Anthropic
                with self.tracer.start_as_current_span("anthropic_api_call"):
                    response = self.anthropic.messages.create(
                        model="claude-3-7-sonnet-20250219",
                        max_tokens=1000,
                        system=self.system_prompt,
                        messages=self.messages,
                        tools=formatted_tools if formatted_tools else None,
                    )
                
                # Handle tool calls if present
                if hasattr(response, 'content') and any(
                    isinstance(item, dict) and item.get('type') == 'tool_use'
                    for item in response.content
                ):
                    return await self._handle_tool_calls(response)
                
                # Extract and return the assistant's response
                assistant_response = next(
                    (item.text for item in response.content if hasattr(item, 'text') and item.text),
                    "I don't have a response for that."
                )
                
                # Add assistant's response to conversation history
                self.messages.append({"role": "assistant", "content": assistant_response})
                
                span.set_status(Status(StatusCode.OK))
                return assistant_response
                
            except Exception as e:
                error_msg = f"Failed to process user message: {str(e)}"
                logger.error(error_msg, exc_info=True)
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, error_msg))
                raise RuntimeError(error_msg) from e

    async def _handle_tool_calls(self, response: Any) -> str:
        """Handle tool calls in the assistant's response.
        
        Args:
            response: The response from the Anthropic API containing tool calls
            
        Returns:
            str: The final response after processing all tool calls
            
        Raises:
            RuntimeError: If there's an error processing tool calls
        """
        with self.tracer.start_as_current_span("handle_tool_calls") as span:
            try:
                if not hasattr(response, 'content') or not response.content:
                    return "I couldn't process that request. Please try again."
                
                tool_calls = [
                    item for item in response.content 
                    if hasattr(item, 'type') and item.type == 'tool_use'
                ]
                
                if not tool_calls:
                    return "I couldn't determine what action to take. Please try rephrasing your request."
                
                span.set_attribute("tool_calls.count", len(tool_calls))
                
                # Process each tool call
                tool_results = []
                for tool_call in tool_calls:
                    tool_name = getattr(tool_call, 'name', 'unknown')
                    tool_id = getattr(tool_call, 'id', 'unknown')
                    tool_args = getattr(tool_call, 'input', {})
                    
                    with self.tracer.start_as_current_span(f"tool_call.{tool_name}") as tool_span:
                        tool_span.set_attributes({
                            "tool_name": tool_name,
                            "tool_id": tool_id,
                            "tool_args": json.dumps(tool_args, default=str)
                        })
                        
                        try:
                            # Call the tool
                            result = await self.call_tool(tool_name, tool_args)
                            tool_results.append({
                                "tool_use_id": tool_id,
                                "content": result
                            })
                            tool_span.set_status(Status(StatusCode.OK))
                            
                        except Exception as e:
                            error_msg = f"Error calling tool {tool_name}: {str(e)}"
                            logger.error(error_msg, exc_info=True)
                            tool_span.record_exception(e)
                            tool_span.set_status(Status(StatusCode.ERROR, error_msg))
                            tool_results.append({
                                "tool_use_id": tool_id,
                                "is_error": True,
                                "content": f"Error: {str(e)}"
                            })
                
                # Add tool results to conversation history
                self.messages.append({
                    "role": "user",
                    "content": [{"type": "tool_result", "tool_use_id": tr["tool_use_id"], "content": tr["content"]} for tr in tool_results]
                })
                
                # Get the assistant's response to the tool results
                return await self.process_user_message("Here are the results of the tool calls:" + "\n".join(
                    f"- {tr['tool_use_id']}: {tr['content']}" for tr in tool_results
                ))
                
            except Exception as e:
                error_msg = f"Failed to handle tool calls: {str(e)}"
                logger.error(error_msg, exc_info=True)
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, error_msg))
                return f"I encountered an error while processing your request: {str(e)}"

        response_text = ""
        tool_results = []

        # Process response content
        for content in response.content:
            if content.type == "text":
                response_text += content.text
                self.messages.append({"role": "assistant", "content": content.text})
            elif content.type == "tool_use":
                # Call the tool
                try:
                    result = await self.call_tool(content.name, content.input)
                    from .enhanced_session import parse_tool_result
                    tool_result_text = f"Tool '{content.name}' returned: {parse_tool_result(result)}"
                    tool_results.append(tool_result_text)
                    
                    # Add tool result to conversation
                    self.messages.append({
                        "role": "tool",
                        "tool_use_id": content.id,
                        "content": json.dumps(result)
                    })
                except Exception as e:
                    error_text = f"Error calling tool '{content.name}': {str(e)}"
                    tool_results.append(error_text)
                    self.messages.append({
                        "role": "tool",
                        "tool_use_id": content.id,
                        "content": f"Error: {str(e)}"
                    })

        # If tools were used, get a follow-up response
        if tool_results:
            with self.tracer.start_as_current_span("anthropic_followup"):
                try:
                    follow_up = self.anthropic.messages.create(
                        model="claude-3-7-sonnet-20250219",
                        max_tokens=1000,
                        system=self.system_prompt,
                        messages=self.messages,
                    )

                    if follow_up.content and follow_up.content[0].type == "text":
                        follow_up_text = follow_up.content[0].text
                        response_text += "\n\n" + follow_up_text
                        self.messages.append({"role": "assistant", "content": follow_up_text})
                except Exception as e:
                    error_msg = f"Error in follow-up: {str(e)}"
                    response_text += f"\n\n{error_msg}"

        return response_text

    async def chat_loop(self):
        """Run an interactive chat loop."""
        print(f"MCP Client '{self.name}' initialized. Type 'quit' to exit.")
        print(f"Available tools: {await self.get_tool_names()}")
        print("-" * 50)

        try:
            while True:
                try:
                    user_input = input("\nYou: ").strip()
                    if user_input.lower() in ['quit', 'exit', 'q']:
                        break
                    
                    if not user_input:
                        continue

                    response = await self.process_user_message(user_input)
                    print(f"\nAssistant: {response}")
                    
                except KeyboardInterrupt:
                    print("\nExiting...")
                    break
                except Exception as e:
                    print(f"\nError: {str(e)}")
                    
        except Exception as e:
            print(f"Chat loop error: {str(e)}")

    async def reset_conversation(self):
        """Reset the conversation history."""
        self.messages = []

    async def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific tool."""
        if self.config.use_sse and self._mcp_session:
            return self._mcp_session.get_tool_by_name(tool_name)
        else:
            tools = await self.get_available_tools()
            for tool in tools:
                if tool["name"] == tool_name:
                    return tool
            return None

    async def validate_tool_call(self, tool_name: str, tool_args: Dict[str, Any]) -> bool:
        """Validate if a tool call has the correct arguments."""
        if self.config.use_sse and self._mcp_session:
            return await self._mcp_session.validate_tool_args(tool_name, tool_args)
        else:
            # Basic validation for HTTP mode
            tool_info = await self.get_tool_info(tool_name)
            if not tool_info:
                return False
            
            required_props = tool_info["input_schema"].get("required", [])
            provided_props = set(tool_args.keys())
            required_props_set = set(required_props)
            
            return required_props_set.issubset(provided_props)

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the current conversation history."""
        return self.messages.copy()

    async def get_current_tool_names(self) -> List[str]:
        """Get available tool names from the server"""
        await self._ensure_initialized()
        with self.tracer.start_as_current_span("get_current_tool_names") as span:
            try:
                if self.config.use_sse:
                    tools = await self._mcp_session.get_tools_cached()
                    available_tool_names = [tool["name"] for tool in tools]
                else:
                    response = await self._http_request("GET", "tools")
                    available_tool_names = [tool["name"] for tool in response.get("tools", [])]
                
                span.set_attribute("tool_count", len(available_tool_names))
                return available_tool_names
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise


async def main(name: str = "default", server_url: str = "http://localhost:8000"):
    """Main entry point for the MCP client."""
    tracer = trace.get_tracer("mcp_session")
    
    with tracer.start_as_current_span(f"mcp_session_{name}"):
        config = ClientConfig(base_url=server_url)
        
        try:
            async with MCPClient(name=name, config=config) as client:
                await client.chat_loop()
        except Exception as e:
            print(f"Failed to start MCP client: {str(e)}")
            raise


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    name = sys.argv[1] if len(sys.argv) > 1 else "default"
    server_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8000"
    
    asyncio.run(main(name, server_url))