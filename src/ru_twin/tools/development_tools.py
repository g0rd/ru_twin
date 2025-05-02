from crewai.tools import BaseTool
from typing import Type, List, Dict
from pydantic import BaseModel, Field
import json

class CodeGeneratorInput(BaseModel):
    """Input schema for CodeGenerator tool."""
    requirements: str = Field(..., description="Detailed requirements for the code to be generated")
    tech_stack: List[str] = Field(..., description="List of technologies to be used")
    context: str = Field(default="", description="Additional context about the existing codebase")

class CodeGenerator(BaseTool):
    name: str = "CodeGenerator"
    description: str = (
        "Generate code based on requirements and specified tech stack. "
        "Provides well-structured, documented code that follows best practices."
    )
    args_schema: Type[BaseModel] = CodeGeneratorInput

    def _run(self, requirements: str, tech_stack: List[str], context: str = "") -> str:
        # Use LLM to generate code based on requirements
        prompt = f"""
        Generate code based on the following:
        Requirements: {requirements}
        Tech Stack: {', '.join(tech_stack)}
        Context: {context}
        
        Please provide:
        1. File structure
        2. Code with comments
        3. Setup instructions
        """
        # Return structured response
        return self.llm(prompt)

class ArchitectureDesignerInput(BaseModel):
    """Input schema for ArchitectureDesigner tool."""
    requirements: str = Field(..., description="System requirements")
    constraints: Dict = Field(default={}, description="Technical constraints and limitations")
    existing_architecture: str = Field(default="", description="Description of existing architecture")

class ArchitectureDesigner(BaseTool):
    name: str = "ArchitectureDesigner"
    description: str = (
        "Design system architecture based on requirements and constraints. "
        "Produces detailed architecture documentation including diagrams and technical specifications."
    )
    args_schema: Type[BaseModel] = ArchitectureDesignerInput

    def _run(self, requirements: str, constraints: Dict = {}, existing_architecture: str = "") -> str:
        prompt = f"""
        Design a system architecture based on:
        Requirements: {requirements}
        Constraints: {json.dumps(constraints, indent=2)}
        Existing Architecture: {existing_architecture}
        
        Please provide:
        1. Architecture overview
        2. Component diagram
        3. Data flow
        4. Integration points
        5. Technical considerations
        """
        return self.llm(prompt) 