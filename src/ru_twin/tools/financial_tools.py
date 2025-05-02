from crewai.tools import BaseTool
from typing import Type, Dict, List
from pydantic import BaseModel, Field

class FinancialAnalysisInput(BaseModel):
    """Input schema for FinancialAnalysis tool."""
    data: Dict = Field(..., description="Financial data to analyze")
    metrics: List[str] = Field(..., description="Financial metrics to calculate")
    period: str = Field(default="quarterly", description="Analysis period")

class FinancialAnalysis(BaseTool):
    name: str = "FinancialAnalysis"
    description: "Analyze financial data and provide insights"
    args_schema: Type[BaseModel] = FinancialAnalysisInput

    def _run(self, data: Dict, metrics: List[str], period: str) -> str:
        prompt = f"""
        Analyze financial data for period: {period}
        Metrics: {', '.join(metrics)}
        
        Provide:
        1. Key financial indicators
        2. Trend analysis
        3. Risk assessment
        4. Recommendations
        5. Future projections
        """
        return self.llm(prompt)

class BudgetPlannerInput(BaseModel):
    """Input schema for BudgetPlanner tool."""
    budget_data: Dict = Field(..., description="Budget information")
    timeframe: str = Field(..., description="Budget planning timeframe")
    constraints: Dict = Field(default={}, description="Budget constraints")

class BudgetPlanner(BaseTool):
    name: str = "BudgetPlanner"
    description: "Create and optimize budget plans"
    args_schema: Type[BaseModel] = BudgetPlannerInput

    def _run(self, budget_data: Dict, timeframe: str, constraints: Dict) -> str:
        prompt = f"""
        Create budget plan for {timeframe}:
        Constraints: {constraints}
        
        Provide:
        1. Budget allocation
        2. Cost optimization
        3. Revenue projections
        4. Cash flow analysis
        5. Risk mitigation
        """
        return self.llm(prompt) 