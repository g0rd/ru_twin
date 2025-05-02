import requests
from crewai.tools import BaseTool
from typing import Type, Optional
from pydantic import BaseModel, Field

class ListCallsInput(BaseModel):
    limit: Optional[int] = Field(default=10, description="Max number of calls to return")

class ListCallsTool(BaseTool):
    name: str = "VapiListCalls"
    description: str = "List recent Vapi calls for the organization"
    args_schema: Type[BaseModel] = ListCallsInput

    def _run(self, limit: int = 10) -> dict:
        # You should store your Vapi API token securely (e.g., env var)
        token = "YOUR_VAPI_TOKEN"
        url = f"https://api.vapi.ai/call?limit={limit}"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

class InitiateCallInput(BaseModel):
    phone_number: str = Field(..., description="Phone number to call")
    assistant_id: str = Field(..., description="Vapi Assistant ID to use for the call")

class InitiateCallTool(BaseTool):
    name: str = "VapiInitiateCall"
    description: str = "Initiate a phone call via Vapi"
    args_schema: Type[BaseModel] = InitiateCallInput

    def _run(self, phone_number: str, assistant_id: str) -> dict:
        token = "YOUR_VAPI_TOKEN"
        url = "https://api.vapi.ai/call"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "phoneNumber": phone_number,
            "assistantId": assistant_id
        }
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json() 