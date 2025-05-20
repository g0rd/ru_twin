from pydantic import BaseModel

class ClientConfig(BaseModel):
    """Configuration for the MCP client."""
    base_url: str = "http://localhost:8000"
    api_version: str = "v1"
    timeout: int = 30
    use_tracing: bool = True
    use_sse: bool = True
