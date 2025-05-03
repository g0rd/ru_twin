from crewai.tools import BaseTool
from typing import Type, List
from pydantic import BaseModel, Field

class LegalAnalysisInput(BaseModel):
    """Input schema for LegalAnalysis tool."""
    document: str = Field(..., description="Legal document to analyze")
    focus_areas: List[str] = Field(..., description="Areas to focus analysis on")
    jurisdiction: str = Field(default="US", description="Legal jurisdiction")

class LegalAnalysis(BaseTool):
    name = "LegalAnalysis"
    description = "Analyze legal documents and provide insights"
    args_schema: Type[BaseModel] = LegalAnalysisInput

    def _run(self, document: str, focus_areas: List[str], jurisdiction: str) -> str:
        prompt = f"""
        Analyze legal document for jurisdiction {jurisdiction}
        Focus areas: {', '.join(focus_areas)}
        
        Provide:
        1. Legal implications
        2. Risk assessment
        3. Compliance requirements
        4. Recommended actions
        5. Potential issues
        """
        return self.llm(prompt)

class ComplianceCheckerInput(BaseModel):
    """Input schema for ComplianceChecker tool."""
    requirements: List[str] = Field(..., description="Compliance requirements to check")
    context: str = Field(..., description="Business context")
    region: str = Field(default="US", description="Geographic region")

class ComplianceChecker(BaseTool):
    name = "ComplianceChecker"
    description = "Check compliance with legal and regulatory requirements"
    args_schema: Type[BaseModel] = ComplianceCheckerInput

    def _run(self, requirements: List[str], context: str, region: str) -> str:
        prompt = f"""
        Check compliance for region {region}:
        Requirements: {', '.join(requirements)}
        Context: {context}
        
        Provide:
        1. Compliance status
        2. Gap analysis
        3. Required actions
        4. Documentation needs
        5. Monitoring plan
        """
        return self.llm(prompt) 