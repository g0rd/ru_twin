from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from .mcp.client import MCPClient
from .a2a import AgentMessenger
from .third_party_gateway import ThirdPartyAgentGateway
from .tools.comet_tools import CometTools
import os
from typing import Dict, Any, List

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

MCP_BASE_URL = "http://mcp-server:8000"  # Example
THIRD_PARTY_REGISTRY = {
    "ExternalAgent1": "https://external-agent1.com/api/task",
    # Add more as needed
}

def create_crew(
    agents_config: Dict[str, Any],
    tasks_config: Dict[str, Any],
    task_name: str,
    tool_registry: Dict[str, Any],
    a2a_messenger: AgentMessenger,
    mcp_clients: List[MCPClient]
) -> Crew:
    """Create a RuTwin crew with the specified configuration.
    
    Args:
        agents_config: Configuration for the agents
        tasks_config: Configuration for the tasks
        task_name: Name of the task to execute
        tool_registry: Registry of available tools
        a2a_messenger: Agent-to-agent messenger instance
        mcp_clients: List of MCP clients
        
    Returns:
        A configured Crew instance
    """
    # Create RuTwin instance
    rutwin = RuTwin()
    
    # Override configurations
    rutwin.agents_config = agents_config
    rutwin.tasks_config = tasks_config
    
    # Set up tools and messengers
    rutwin.mcp = mcp_clients[0] if mcp_clients else MCPClient(MCP_BASE_URL)
    rutwin.messenger = a2a_messenger
    
    # Create and return the crew
    return rutwin.crew()

@CrewBase
class RuTwin():
    """RuTwin crew"""

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def digital_twin(self) -> Agent:
        return Agent(config=self.agents_config['Digital Twin'], verbose=True)

    @agent
    def cpg_researcher(self) -> Agent:
        return Agent(config=self.agents_config['CPG Researcher'], verbose=True)

    @agent
    def cpg_salesperson(self) -> Agent:
        return Agent(config=self.agents_config['CPG Salesperson'], verbose=True)

    @agent
    def executive_assistant(self) -> Agent:
        return Agent(config=self.agents_config['Executive Assistant'], verbose=True)

    @agent
    def accountability_buddy(self) -> Agent:
        return Agent(config=self.agents_config['Accountability Buddy'], verbose=True)

    @agent
    def cfo(self) -> Agent:
        return Agent(config=self.agents_config['CFO'], verbose=True)

    @agent
    def legal_advisor(self) -> Agent:
        return Agent(config=self.agents_config['Legal Advisor'], verbose=True)

    @agent
    def writer(self) -> Agent:
        return Agent(config=self.agents_config['Writer'], verbose=True)

    @agent
    def full_stack_ai_developer(self) -> Agent:
        return Agent(config=self.agents_config['Full Stack AI Developer'], verbose=True)

    @agent
    def pr_strategist(self) -> Agent:
        return Agent(config=self.agents_config['PR Strategist'], verbose=True)

    @agent
    def voice_assistant(self) -> Agent:
        return Agent(config=self.agents_config['Voice Assistant'], verbose=True)

    @agent
    def comet_opik_evaluator(self) -> Agent:
        """Create the Comet Opik evaluator agent."""
        return Agent(
            config=self.agents_config['Comet Opik Evaluator'],
            tools=[
                self.comet_tools.evaluate_agent_response,
                self.comet_tools.start_evaluation_session,
                self.comet_tools.end_evaluation_session
            ],
            verbose=True
        )

    @agent
    def goose_coding_agent(self) -> Agent:
        """Create the Goose Coding Agent."""
        return Agent(
            config=self.agents_config['Goose Coding Agent'],
            verbose=True
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def market_research(self) -> Task:
        return Task(config=self.tasks_config['market_research'])

    @task
    def sales_strategy(self) -> Task:
        return Task(config=self.tasks_config['sales_strategy'])

    @task
    def financial_planning(self) -> Task:
        return Task(config=self.tasks_config['financial_planning'])

    @task
    def legal_review(self) -> Task:
        return Task(config=self.tasks_config['legal_review'])

    @task
    def implementation_plan(self) -> Task:
        return Task(config=self.tasks_config['implementation_plan'])

    @task
    def progress_tracking(self) -> Task:
        return Task(config=self.tasks_config['progress_tracking'])

    @task
    def system_architecture(self) -> Task:
        return Task(config=self.tasks_config['system_architecture'])

    @task
    def development_implementation(self) -> Task:
        return Task(config=self.tasks_config['development_implementation'])

    @task
    def pr_strategy(self) -> Task:
        return Task(config=self.tasks_config['pr_strategy'])

    @task
    def media_outreach(self) -> Task:
        return Task(config=self.tasks_config['media_outreach'])

    @crew
    def crew(self) -> Crew:
        """Creates the RuTwin crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )

    def __init__(self):
        self.mcp = MCPClient(MCP_BASE_URL)
        self.third_party_gateway = ThirdPartyAgentGateway(THIRD_PARTY_REGISTRY)
        
        # Initialize Comet tools
        comet_api_key = os.getenv("COMET_API_KEY")
        if not comet_api_key:
            raise ValueError("COMET_API_KEY environment variable is required")
        self.comet_tools = CometTools(api_key=comet_api_key)
        
        # Register all agents
        self.agent_registry = {
            "Digital Twin": self.digital_twin(),
            "CPG Researcher": self.cpg_researcher(),
            "CPG Salesperson": self.cpg_salesperson(),
            "Executive Assistant": self.executive_assistant(),
            "Accountability Buddy": self.accountability_buddy(),
            "CFO": self.cfo(),
            "Legal Advisor": self.legal_advisor(),
            "Writer": self.writer(),
            "Full Stack AI Developer": self.full_stack_ai_developer(),
            "PR Strategist": self.pr_strategist(),
            "Voice Assistant": self.voice_assistant(),
            "Comet Opik Evaluator": self.comet_opik_evaluator(),
            "Goose Coding Agent": self.goose_coding_agent()
        }
        self.messenger = AgentMessenger(self.agent_registry)

    # Example: Overriding tool call to go through MCP
    def call_tool(self, tool_name, agent_name, payload):
        return self.mcp.call_tool(tool_name, agent_name, payload)

    # Example: Sending a message to another agent
    def send_agent_message(self, from_agent, to_agent, message):
        return self.messenger.send_message(from_agent, to_agent, message)

    # Example: Sending a task to a third-party agent
    def send_to_third_party(self, agent_name, task_payload):
        return self.third_party_gateway.send_task(agent_name, task_payload)

    def escalate_to_voice(self, to_phone_number, message, assistant_id):
        """
        Escalate an urgent matter to a voice call using the Voice Assistant and Vapi.
        """
        # Use MCP to invoke the VapiInitiateCall tool
        payload = {
            "phone_number": to_phone_number,
            "assistant_id": assistant_id
        }
        return self.call_tool("vapi_initiate_call", "Voice Assistant", payload)

    def evaluate_agent_performance(self, agent_name: str, task: str, response: str, context: Dict[str, Any] = None) -> Dict[str, float]:
        """
        Evaluate an agent's performance using the Comet Opik evaluator.
        
        Args:
            agent_name: Name of the agent to evaluate
            task: The task that was given to the agent
            response: The agent's response to evaluate
            context: Additional context for the evaluation
            
        Returns:
            Dictionary containing evaluation metrics
        """
        return self.comet_tools.evaluate_agent_response(
            agent_name=agent_name,
            task=task,
            response=response,
            context=context
        )

    def start_evaluation(self, session_name: str):
        """Start a new evaluation session."""
        self.comet_tools.start_evaluation_session(session_name)

    def end_evaluation(self):
        """End the current evaluation session."""
        self.comet_tools.end_evaluation_session()
