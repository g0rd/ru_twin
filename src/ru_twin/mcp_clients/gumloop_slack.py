import requests

class GumloopSlackMCP:
    def __init__(self, base_url, api_key=None):
        self.base_url = base_url
        self.api_key = api_key

    def send_message(self, channel, message):
        url = f"{self.base_url}/slack/send_message"
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        payload = {"channel": channel, "message": message}
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json() 