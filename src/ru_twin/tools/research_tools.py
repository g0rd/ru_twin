from crewai.tools import BaseTool
from typing import Type, List, Dict
from pydantic import BaseModel, Field

class MarketAnalysisInput(BaseModel):
    """Input schema for MarketAnalysis tool."""
    industry: str = Field(..., description="Industry to analyze")
    metrics: List[str] = Field(..., description="Metrics to analyze")
    timeframe: str = Field(default="1y", description="Analysis timeframe")

class MarketAnalysis(BaseTool):
    name: str = "MarketAnalysis"
    description: str = "Analyze market trends, competition, and opportunities in specific industries"
    args_schema: Type[BaseModel] = MarketAnalysisInput

    def _run(self, industry: str, metrics: List[str], timeframe: str = "1y") -> str:
        prompt = f"""
        Analyze {industry} market for:
        Metrics: {', '.join(metrics)}
        Timeframe: {timeframe}
        
        Provide:
        1. Market size and growth
        2. Key competitors
        3. Market trends
        4. Opportunities and threats
        5. Consumer behavior analysis
        """
        return self.llm(prompt)

class CompetitorAnalysisInput(BaseModel):
    """Input schema for CompetitorAnalysis tool."""
    competitors: List[str] = Field(..., description="List of competitors to analyze")
    aspects: List[str] = Field(..., description="Aspects to analyze")

class CompetitorAnalysis(BaseTool):
    name: str = "CompetitorAnalysis"
    description: str = "Detailed analysis of competitors' strategies and performance"
    args_schema: Type[BaseModel] = CompetitorAnalysisInput

    def _run(self, competitors: List[str], aspects: List[str]) -> str:
        prompt = f"""
        Analyze competitors:
        Companies: {', '.join(competitors)}
        Aspects: {', '.join(aspects)}
        
        Provide:
        1. Competitive positioning
        2. SWOT analysis
        3. Market share
        4. Strategic initiatives
        5. Comparative analysis
        """
        return self.llm(prompt) 