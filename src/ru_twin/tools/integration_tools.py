from crewai.tools import BaseTool
from typing import Type, Dict
from pydantic import BaseModel, Field

class APIDesignerInput(BaseModel):
    """Input schema for APIDesigner tool."""
    requirements: str = Field(..., description="API requirements and specifications")
    auth_type: str = Field(default="oauth2", description="Authentication type for the API")
    version: str = Field(default="1.0.0", description="API version")

class APIDesigner(BaseTool):
    name: str = "APIDesigner"
    description: str = (
        "Design RESTful APIs with comprehensive documentation. "
        "Includes endpoint specifications, authentication, and integration guidelines."
    )
    args_schema: Type[BaseModel] = APIDesignerInput

    def _run(self, requirements: str, auth_type: str, version: str) -> str:
        prompt = f"""
        Design an API based on:
        Requirements: {requirements}
        Authentication: {auth_type}
        Version: {version}
        
        Please provide:
        1. API specification
        2. Endpoint documentation
        3. Authentication flow
        4. Example requests/responses
        5. Integration guide
        """
        return self.llm(prompt) 