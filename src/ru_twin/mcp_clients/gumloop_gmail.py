import requests

class GumloopGmailMCP:
    def __init__(self, base_url, api_key=None):
        self.base_url = base_url
        self.api_key = api_key

    def read_emails(self, label=None, max_results=10):
        url = f"{self.base_url}/gmail/read"
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        payload = {"label": label, "max_results": max_results}
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    def send_email(self, to, subject, body):
        url = f"{self.base_url}/gmail/send"
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        payload = {"to": to, "subject": subject, "body": body}
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json() 