from crewai.tools import BaseTool
from typing import Type, Optional
from pydantic import BaseModel, Field
from ..mcp_clients.gumloop_gmail import GumloopGmailMCP

class GmailReadInput(BaseModel):
    label: Optional[str] = Field(default=None, description="Gmail label to filter")
    max_results: int = Field(default=10, description="Max emails to fetch")

class GmailReadTool(BaseTool):
    name: str = "GmailRead"
    description: str = "Read emails from Gmail via Gumloop MCP"
    args_schema: Type[BaseModel] = GmailReadInput

    def _run(self, label: Optional[str] = None, max_results: int = 10) -> dict:
        mcp = GumloopGmailMCP(base_url="https://api.gumloop.com", api_key="YOUR_KEY")
        return mcp.read_emails(label=label, max_results=max_results) 