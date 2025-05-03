import requests

class MCPClient:
    def __init__(self, base_url, api_key=None):
        self.base_url = base_url
        self.api_key = api_key

    def call_tool(self, tool_name, agent_name, payload):
        url = f"{self.base_url}/tools/{tool_name}/invoke"
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        data = {
            "agent": agent_name,
            "payload": payload
        }
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json() 