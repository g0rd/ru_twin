from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.tools import BaseTool
from ru_twin.mcp.client import MCPClient
from ru_twin.a2a import AgentMessenger
from ru_twin.third_party_gateway import ThirdPartyAgentGateway
from ru_twin.tools.comet_tools import CometTools
import os
from typing import Dict, Any, List, Optional

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
    mcp_clients: Dict[str, MCPClient]
) -> Crew:
    """Create a RuTwin crew with the specified configuration.
    
    Args:
        agents_config: Configuration for the agents
        tasks_config: Configuration for the tasks
        task_name: Name of the task to execute
        tool_registry: Registry of available tools
        a2a_messenger: Agent-to-agent messenger instance
        mcp_clients: Dictionary of MCP clients
        
    Returns:
        A configured Crew instance
    """
    # Create RuTwin instance
    rutwin = RuTwin()
    
    # Override configurations
    rutwin.agents_config = agents_config  # This should be the loaded YAML content
    rutwin.tasks_config = tasks_config    # This should be the loaded YAML content
    
    # Set up tools and messengers
    # Use the first available MCP client or create a new one
    if mcp_clients:
        # Get the first client from the dictionary
        first_client = next(iter(mcp_clients.values()))
        rutwin.mcp = first_client
    else:
        rutwin.mcp = MCPClient(MCP_BASE_URL)
    
    rutwin.messenger = a2a_messenger
    
    # Create and return the crew
    return rutwin.crew()

class CometEvaluateTool(BaseTool):
    name: str = "evaluate_agent_response"
    description: str = "Evaluate an agent's response using Comet Opik"

    def __init__(self, comet_tools: CometTools):
        super().__init__()
        self._comet_tools = comet_tools

    def _run(self, agent_name: str, task: str, response: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        return self._comet_tools.evaluate_agent_response(agent_name, task, response, context)

class CometStartSessionTool(BaseTool):
    name: str = "start_evaluation_session"
    description: str = "Start a new Comet Opik evaluation session"

    def __init__(self, comet_tools: CometTools):
        super().__init__()
        self._comet_tools = comet_tools

    def _run(self, session_name: str) -> None:
        return self._comet_tools.start_evaluation_session(session_name)

class CometEndSessionTool(BaseTool):
    name: str = "end_evaluation_session"
    description: str = "End the current Comet Opik evaluation session"

    def __init__(self, comet_tools: CometTools):
        super().__init__()
        self._comet_tools = comet_tools

    def _run(self) -> None:
        return self._comet_tools.end_evaluation_session()

@CrewBase
class RuTwin():
    """RuTwin crew"""

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    agents_config = None  # Will be set by create_crew
    tasks_config = None   # Will be set by create_crew

    def __init__(self):
        self.mcp = MCPClient(MCP_BASE_URL)
        self.third_party_gateway = ThirdPartyAgentGateway(THIRD_PARTY_REGISTRY)
        
        # Initialize Comet tools
        comet_api_key = os.getenv("COMET_API_KEY")
        
        if not comet_api_key:
            raise ValueError("COMET_API_KEY environment variable is required")
        self.comet_tools = CometTools(api_key=comet_api_key)
        
        # Initialize agent registry
        self.agent_registry = {}
        self.messenger = None  # Will be initialized after agents are created

    def _get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get agent configuration by name."""
        if not self.agents_config or 'agents' not in self.agents_config:
            raise ValueError(f"Invalid agents configuration: {self.agents_config}")
        
        agent_config = next((a for a in self.agents_config['agents'] if a['name'] == agent_name), None)
        if not agent_config:
            raise ValueError(f"Agent configuration not found for: {agent_name}")
        return agent_config

    @agent
    def digital_twin(self) -> Agent:
        agent_config = self._get_agent_config('Digital Twin')
        return Agent(config=agent_config, verbose=True)

    @agent
    def cpg_researcher(self) -> Agent:
        agent_config = self._get_agent_config('CPG Researcher')
        return Agent(config=agent_config, verbose=True)

    @agent
    def cpg_salesperson(self) -> Agent:
        agent_config = self._get_agent_config('CPG Salesperson')
        return Agent(config=agent_config, verbose=True)

    @agent
    def executive_assistant(self) -> Agent:
        agent_config = self._get_agent_config('Executive Assistant')
        return Agent(config=agent_config, verbose=True)

    @agent
    def accountability_buddy(self) -> Agent:
        agent_config = self._get_agent_config('Accountability Buddy')
        return Agent(config=agent_config, verbose=True)

    @agent
    def cfo(self) -> Agent:
        agent_config = self._get_agent_config('CFO')
        return Agent(config=agent_config, verbose=True)

    @agent
    def legal_advisor(self) -> Agent:
        agent_config = self._get_agent_config('Legal Advisor')
        return Agent(config=agent_config, verbose=True)

    @agent
    def writer(self) -> Agent:
        agent_config = self._get_agent_config('Writer')
        return Agent(config=agent_config, verbose=True)

    @agent
    def full_stack_ai_developer(self) -> Agent:
        """Create the AI Developer agent."""
        agent_config = self._get_agent_config('Goose Coding Agent')
        return Agent(
            config=agent_config,
            verbose=True
        )

    @agent
    def pr_strategist(self) -> Agent:
        agent_config = self._get_agent_config('PR Strategist')
        return Agent(config=agent_config, verbose=True)

    @agent
    def voice_assistant(self) -> Agent:
        agent_config = self._get_agent_config('Voice Assistant')
        return Agent(config=agent_config, verbose=True)

    @agent
    def comet_opik_evaluator(self) -> Agent:
        """Create the Comet Opik evaluator agent."""
        agent_config = self._get_agent_config('Comet Opik Evaluator')
        
        # Create tool instances
        evaluate_tool = CometEvaluateTool(self.comet_tools)
        start_session_tool = CometStartSessionTool(self.comet_tools)
        end_session_tool = CometEndSessionTool(self.comet_tools)
        
        return Agent(
            name=agent_config['name'],
            role=agent_config['role'],
            goal=agent_config['goal'],
            backstory=agent_config['backstory'],
            verbose=agent_config.get('verbose', True),
            allow_delegation=agent_config.get('allow_delegation', True),
            tools=[
                evaluate_tool,
                start_session_tool,
                end_session_tool
            ]
        )

    @agent
    def goose_coding_agent(self) -> Agent:
        """Create the Goose Coding Agent."""
        agent_config = self._get_agent_config('Goose Coding Agent')
        return Agent(
            name=agent_config['name'],
            role=agent_config['role'],
            goal=agent_config['goal'],
            backstory=agent_config['backstory'],
            verbose=agent_config.get('verbose', True),
            allow_delegation=agent_config.get('allow_delegation', True)
        )

    def _initialize_agents(self):
        """Initialize all agents and create the agent registry."""
        self.agent_registry = {
            "Digital Twin": self.digital_twin(),
            "CPG Researcher": self.cpg_researcher(),
            "CPG Salesperson": self.cpg_salesperson(),
            "Executive Assistant": self.executive_assistant(),
            "Accountability Buddy": self.accountability_buddy(),
            "CFO": self.cfo(),
            "Legal Advisor": self.legal_advisor(),
            "Writer": self.writer(),
            "AI Developer": self.full_stack_ai_developer(),
            "PR Strategist": self.pr_strategist(),
            "Voice Assistant": self.voice_assistant(),
            "Comet Opik Evaluator": self.comet_opik_evaluator(),
            "Goose Coding Agent": self.goose_coding_agent()
        }
        self.messenger = AgentMessenger(self.agent_registry)

    @crew
    def crew(self) -> Crew:
        """Creates the RuTwin crew"""
        # Initialize agents if not already done
        if not self.agent_registry:
            self._initialize_agents()

        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,    # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )

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
