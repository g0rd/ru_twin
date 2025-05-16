import asyncio
import json
from typing import AsyncGenerator, Tuple, Any
import aiohttp
from contextlib import asynccontextmanager

class SSEStream:
    def __init__(self, response: aiohttp.ClientResponse):
        self.response = response
        self._buffer = asyncio.Queue()

    async def receive(self) -> dict:
        """Receive a message from the SSE stream."""
        return await self._buffer.get()

    async def _process_stream(self):
        """Process the SSE stream and put messages in the buffer."""
        async for line in self.response.content:
            line = line.decode('utf-8').strip()
            if line.startswith('data: '):
                try:
                    data = json.loads(line[6:])
                    await self._buffer.put(data)
                except json.JSONDecodeError:
                    continue

class SSEOutput:
    def __init__(self, session: aiohttp.ClientSession, url: str):
        self.session = session
        self.url = url

    async def send(self, data: dict):
        """Send data to the server."""
        async with self.session.post(self.url, json=data) as response:
            if response.status != 200:
                raise Exception(f"Failed to send data: {response.status}")

@asynccontextmanager
async def sse_client(url: str) -> AsyncGenerator[Tuple[SSEStream, SSEOutput], None]:
    """Create an SSE client connection.
    
    Args:
        url: The URL of the SSE endpoint
        
    Yields:
        A tuple of (input_stream, output_stream)
    """
    async with aiohttp.ClientSession() as session:
        # Connect to SSE endpoint
        async with session.get(url) as response:
            if response.status != 200:
                raise Exception(f"Failed to connect to SSE endpoint: {response.status}")
            
            # Create streams
            input_stream = SSEStream(response)
            output_stream = SSEOutput(session, url)
            
            # Start processing the input stream
            asyncio.create_task(input_stream._process_stream())
            
            try:
                yield input_stream, output_stream
            finally:
                # Cleanup
                if not response.closed:
                    response.close() 