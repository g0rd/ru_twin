import requests

class SensoClient:
    def __init__(self, api_key, base_url="https://sdk.senso.ai/api/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def upload_content(self, text, category_id=None, topic_id=None):
        url = f"{self.base_url}/content"
        payload = {
            "text": text,
            "categoryId": category_id,
            "topicId": topic_id
        }
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def list_content(self, limit=10, offset=0):
        url = f"{self.base_url}/content?limit={limit}&offset={offset}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def search(self, question):
        url = f"{self.base_url}/search"
        payload = {"question": question}
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def generate(self, content_id, prompt):
        url = f"{self.base_url}/generate"
        payload = {"contentId": content_id, "prompt": prompt}
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json() 