from crewai.tools import BaseTool
from typing import Type, List
from pydantic import BaseModel, Field
from datetime import datetime

class MediaMonitorInput(BaseModel):
    """Input schema for MediaMonitor tool."""
    keywords: List[str] = Field(..., description="Keywords to monitor")
    sources: List[str] = Field(default=["news", "social", "blogs"], description="Media sources to monitor")
    timeframe: str = Field(default="7d", description="Timeframe for monitoring")

class MediaMonitor(BaseTool):
    name: str = "MediaMonitor"
    description: str = (
        "Monitor media mentions and opportunities across various sources. "
        "Tracks keywords and provides insights on media coverage and opportunities."
    )
    args_schema: Type[BaseModel] = MediaMonitorInput

    def _run(self, keywords: List[str], sources: List[str], timeframe: str) -> str:
        prompt = f"""
        Analyze media coverage for:
        Keywords: {', '.join(keywords)}
        Sources: {', '.join(sources)}
        Timeframe: {timeframe}
        
        Please provide:
        1. Recent mentions analysis
        2. Sentiment overview
        3. Opportunity identification
        4. Trending topics
        """
        return self.llm(prompt)

class ContentStrategistInput(BaseModel):
    """Input schema for ContentStrategist tool."""
    business_goals: str = Field(..., description="Business objectives for the content strategy")
    target_audience: str = Field(..., description="Target audience description")
    content_types: List[str] = Field(default=["blog", "social", "press"], description="Types of content to create")

class ContentStrategist(BaseTool):
    name: str = "ContentStrategist"
    description: str = (
        "Develop comprehensive content strategies aligned with business goals. "
        "Creates content plans, calendars, and guidelines."
    )
    args_schema: Type[BaseModel] = ContentStrategistInput

    def _run(self, business_goals: str, target_audience: str, content_types: List[str]) -> str:
        prompt = f"""
        Develop a content strategy based on:
        Business Goals: {business_goals}
        Target Audience: {target_audience}
        Content Types: {', '.join(content_types)}
        
        Please provide:
        1. Content strategy overview
        2. Content themes and topics
        3. Content calendar
        4. Distribution channels
        5. Success metrics
        """
        return self.llm(prompt) 