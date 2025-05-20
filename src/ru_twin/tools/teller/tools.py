from typing import Dict, Any, List
from crewai_tools import BaseTool
from .client import TellerToolClient
import os

class TellerGetAccountsTool(BaseTool):
    name: str = "teller_get_accounts"
    description: str = "Get all accounts from Teller"

    def __init__(self, client: TellerToolClient):
        super().__init__()
        self.client = client

    async def _run(self) -> Dict[str, Any]:
        return await self.client.get_accounts()

class TellerGetTransactionsTool(BaseTool):
    name: str = "teller_get_transactions"
    description: str = "Get transactions for a specific account from Teller"

    def __init__(self, client: TellerToolClient):
        super().__init__()
        self.client = client

    async def _run(self, account_id: str) -> Dict[str, Any]:
        return await self.client.get_transactions(account_id)

def register_teller_tools(tool_registry) -> None:
    """
    Register all Teller tools with the tool registry.
    """
    client = TellerToolClient(
        access_token=os.getenv("TELLER_ACCESS_TOKEN"),
        environment=os.getenv("TELLER_ENVIRONMENT", "sandbox")
    )

    tools = [
        TellerGetAccountsTool(client),
        TellerGetTransactionsTool(client)
    ]

    for tool in tools:
        tool_registry.register_tool(tool) 