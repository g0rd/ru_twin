from typing import Dict, Any
import comet_ml
from comet_ml import Experiment
from comet_ml.integration.opik import OpikEvaluator

class CometTools:
    def __init__(self, api_key: str, project_name: str = "ru_twin_evaluations"):
        """Initialize Comet ML tools with API key and project name."""
        self.api_key = api_key
        self.project_name = project_name
        self.experiment = None
        self.evaluator = None
        
    def initialize_evaluator(self):
        """Initialize the Opik evaluator."""
        self.evaluator = OpikEvaluator(
            api_key=self.api_key,
            project_name=self.project_name
        )
        
    def evaluate_agent_response(
        self,
        agent_name: str,
        task: str,
        response: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, float]:
        """
        Evaluate an agent's response using Comet Opik.
        
        Args:
            agent_name: Name of the agent being evaluated
            task: The task that was given to the agent
            response: The agent's response to evaluate
            context: Additional context for the evaluation
            
        Returns:
            Dictionary containing evaluation metrics
        """
        if not self.evaluator:
            self.initialize_evaluator()
            
        metrics = self.evaluator.evaluate(
            task=task,
            response=response,
            context=context or {}
        )
        
        # Log the evaluation results
        if self.experiment:
            self.experiment.log_metrics(metrics)
            self.experiment.log_parameters({
                "agent_name": agent_name,
                "task": task
            })
            
        return metrics
        
    def start_evaluation_session(self, session_name: str):
        """Start a new evaluation session."""
        self.experiment = Experiment(
            api_key=self.api_key,
            project_name=self.project_name,
            workspace="ru_twin"
        )
        self.experiment.set_name(session_name)
        
    def end_evaluation_session(self):
        """End the current evaluation session."""
        if self.experiment:
            self.experiment.end()
            self.experiment = None 