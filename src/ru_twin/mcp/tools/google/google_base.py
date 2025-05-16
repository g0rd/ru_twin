from typing import Dict, Any, Optional
from ru_twin.mcp.tools.base import BaseTool, ToolInputSchema
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle

class GoogleToolInputSchema(ToolInputSchema):
    """Base schema for Google tool inputs"""
    credentials_path: str
    token_path: str

class GoogleBaseTool(BaseTool):
    """Base class for all Google tools"""
    
    def __init__(self, name: str, description: str, scopes: list[str], version: str = "1.0.0"):
        super().__init__(name, description, GoogleToolInputSchema, version)
        self.scopes = scopes
        self.credentials = None

    def get_credentials(self, credentials_path: str, token_path: str) -> Credentials:
        """Get or refresh Google API credentials"""
        creds = None
        
        # Load existing token if available
        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)

        # Refresh or create new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, self.scopes)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for future use
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)

        return creds

    def validate_credentials(self, credentials_path: str, token_path: str) -> bool:
        """Validate that credentials exist and are valid"""
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"Credentials file not found at {credentials_path}")
        
        try:
            self.credentials = self.get_credentials(credentials_path, token_path)
            return True
        except Exception as e:
            raise Exception(f"Failed to validate credentials: {str(e)}")

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Base execute method that validates credentials before proceeding"""
        if not self.validate_credentials(input_data["credentials_path"], input_data["token_path"]):
            raise Exception("Invalid credentials")
        return await self._execute_google(input_data)

    async def _execute_google(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Abstract method to be implemented by specific Google tools"""
        raise NotImplementedError("Subclasses must implement _execute_google") 