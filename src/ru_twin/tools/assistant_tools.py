from crewai.tools import BaseTool
from typing import Type, List, Dict
from pydantic import BaseModel, Field
from datetime import datetime

class TaskManagerInput(BaseModel):
    """Input schema for TaskManager tool."""
    tasks: List[Dict] = Field(..., description="Tasks to manage")
    priorities: List[str] = Field(..., description="Priority levels")
    deadline: datetime = Field(..., description="Task deadline")

class TaskManager(BaseTool):
    name: str = "TaskManager"
    description: str = "Manage and prioritize tasks effectively"
    args_schema: Type[BaseModel] = TaskManagerInput

    def _run(self, tasks: List[Dict], priorities: List[str], deadline: datetime) -> str:
        prompt = f"""
        Organize tasks due by {deadline}:
        Tasks: {tasks}
        Priorities: {priorities}
        
        Provide:
        1. Prioritized task list
        2. Time estimates
        3. Dependencies
        4. Resource allocation
        5. Progress tracking
        """
        return self.llm(prompt)

class ProgressTrackerInput(BaseModel):
    """Input schema for ProgressTracker tool."""
    goals: List[str] = Field(..., description="Goals to track")
    metrics: List[str] = Field(..., description="Success metrics")
    frequency: str = Field(default="weekly", description="Tracking frequency")

class ProgressTracker(BaseTool):
    name: str = "ProgressTracker"
    description: str = "Track progress towards goals and provide accountability"
    args_schema: Type[BaseModel] = ProgressTrackerInput

    def _run(self, goals: List[str], metrics: List[str], frequency: str) -> str:
        prompt = f"""
        Track progress for {frequency} review:
        Goals: {', '.join(goals)}
        Metrics: {', '.join(metrics)}
        
        Provide:
        1. Progress status
        2. Achievement metrics
        3. Blockers/challenges
        4. Next actions
        5. Recommendations
        """
        return self.llm(prompt) 