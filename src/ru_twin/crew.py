from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from .mcp_client import MCPClient
from .a2a import AgentMessenger
from .third_party_gateway import ThirdPartyAgentGateway

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

MCP_BASE_URL = "http://mcp-server:8000"  # Example
THIRD_PARTY_REGISTRY = {
    "ExternalAgent1": "https://external-agent1.com/api/task",
    # Add more as needed
}

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
        self.agent_registry = {
            "Digital Twin": self.digital_twin(),
            "CPG Researcher": self.cpg_researcher(),
            # ... all other local agents ...
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
