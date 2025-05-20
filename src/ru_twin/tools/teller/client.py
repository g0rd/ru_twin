from typing import Dict, Any, Optional
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

class TellerToolClient:
    """
    Client implementation for Teller API tools.
    Handles the tool-specific functionality for Teller.
    """
    def __init__(self, access_token: str, environment: str = "sandbox"):
        self.access_token = access_token
        self.environment = environment
        self.base_url = f"https://api.teller.io"
        self.session = None

    async def initialize(self):
        """
        Initialize the client session.
        """
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
        )

    async def cleanup(self):
        """
        Clean up resources.
        """
        if self.session:
            await self.session.close()

    async def handle_webhook(self, payload: Dict[str, Any]):
        """
        Handle incoming webhook events.
        """
        event_type = payload.get("type")
        if event_type == "enrollment.disconnected":
            await self._handle_enrollment_disconnected(payload["payload"])
        elif event_type == "transactions.processed":
            await self._handle_transactions_processed(payload["payload"])
        elif event_type == "account.number_verification.processed":
            await self._handle_account_verification(payload["payload"])

    async def _handle_enrollment_disconnected(self, payload: Dict[str, Any]):
        """
        Handle enrollment disconnection events.
        """
        enrollment_id = payload["enrollment_id"]
        reason = payload["reason"]
        # Implement your enrollment disconnection handling logic here
        print(f"Enrollment {enrollment_id} disconnected. Reason: {reason}")

    async def _handle_transactions_processed(self, payload: Dict[str, Any]):
        """
        Handle processed transactions events.
        """
        transactions = payload["transactions"]
        # Implement your transaction processing logic here
        print(f"Processed {len(transactions)} transactions")

    async def _handle_account_verification(self, payload: Dict[str, Any]):
        """
        Handle account verification events.
        """
        account_id = payload["account_id"]
        status = payload["status"]
        # Implement your account verification handling logic here
        print(f"Account {account_id} verification status: {status}")

    # Add other Teller API methods here
    async def get_accounts(self) -> Dict[str, Any]:
        """
        Get all accounts.
        """
        if not self.session:
            await self.initialize()
        
        async with self.session.get(f"{self.base_url}/accounts") as response:
            return await response.json()

    async def get_transactions(self, account_id: str) -> Dict[str, Any]:
        """
        Get transactions for an account.
        """
        if not self.session:
            await self.initialize()
        
        async with self.session.get(f"{self.base_url}/accounts/{account_id}/transactions") as response:
            return await response.json() 