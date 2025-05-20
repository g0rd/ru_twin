"""Test client for MCP server."""

import asyncio
import json
import logging
import sys
from typing import Optional, Dict, Any, List

# Local imports
from .session import ClientSession
from .enhanced_session import EnhancedMCPSession
from .sse import sse_client

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestClient:
    """Test client for MCP server."""
    
    def __init__(self) -> None:
        """Initialize the test client."""
        self.session: Optional[ClientSession] = None
        self.enhanced_session: Optional[EnhancedMCPSession] = None
        self._streams_context = None
        self._session_context = None

    async def connect(self, url: str) -> None:
        """Connect to the MCP server.
        
        Args:
            url: URL of the MCP server's SSE endpoint.
        """
        logger.info(f"Connecting to MCP server at {url}")
        
        try:
            # Set up SSE client
            self._streams_context = sse_client(url=url)
            streams = await self._streams_context.__aenter__()
            
            # Create and initialize the base session
            self._session_context = ClientSession()
            self.session = await self._session_context.__aenter__()
            
            # Create and initialize the enhanced session
            self.enhanced_session = EnhancedMCPSession(self.session)
            await self.enhanced_session.initialize()
            
            logger.info("Successfully connected to MCP server")
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            await self.cleanup()
            raise

    async def cleanup(self) -> None:
        """Properly clean up the session and streams."""
        logger.info("Cleaning up test client...")
        
        try:
            # Clean up enhanced session
            if hasattr(self.enhanced_session, 'close') and callable(self.enhanced_session.close):
                await self.enhanced_session.close()
                
            # Clean up base session
            if self._session_context:
                await self._session_context.__aexit__(None, None, None)
                
            # Clean up SSE streams
            if self._streams_context:
                await self._streams_context.__aexit__(None, None, None)
                
            logger.info("Test client cleanup complete")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            raise


async def main() -> None:
    """Run the test client."""
    client = TestClient()
    try:
        # Connect to the MCP server
        await client.connect(url="http://localhost:8010/sse")
        
        # List available tools
        if client.enhanced_session:
            try:
                tools = await client.enhanced_session.list_tools()
                print("\nAvailable tools:")
                for tool in tools:
                    print(f"- {tool.get('name', 'Unnamed tool')}")
                    if 'description' in tool:
                        print(f"  {tool['description']}")
                    print()
            except Exception as e:
                print(f"Error listing tools: {e}")
        
        # Example tool call (uncomment and modify as needed)
        # if client.enhanced_session:
        #     try:
        #         result = await client.enhanced_session.call_tool(
        #             tool_name="example_tool",
        #             arguments={"param1": "value1"}
        #         )
        #         print(f"Tool result: {result}")
        #     except Exception as e:
        #         print(f"Error calling tool: {e}")
        
    except Exception as e:
        logger.error(f"Error in test client: {e}")
    finally:
        await client.cleanup()
        logger.info("Test client shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())