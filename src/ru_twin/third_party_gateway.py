import requests

class ThirdPartyAgentGateway:
    def __init__(self, registry):
        self.registry = registry  # {agent_name: endpoint_url}

    def send_task(self, agent_name, task_payload):
        endpoint = self.registry.get(agent_name)
        if not endpoint:
            raise Exception(f"No endpoint registered for {agent_name}")
        response = requests.post(endpoint, json=task_payload)
        response.raise_for_status()
        return response.json() 