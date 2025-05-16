__all__ = ['AgentMessenger']

class AgentMessenger:
    def __init__(self, agent_registry):
        self.agent_registry = agent_registry

    def send_message(self, from_agent, to_agent, message):
        # This could be a direct method call, or a message queue, etc.
        agent = self.agent_registry.get(to_agent)
        if agent:
            return agent.receive_message(from_agent, message)
        else:
            raise Exception(f"Agent {to_agent} not found.")

# Each agent class can implement a receive_message method if needed. 