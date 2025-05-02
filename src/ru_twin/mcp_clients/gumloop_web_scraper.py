import requests

class GumloopWebScraperMCP:
    def __init__(self, base_url, api_key=None):
        self.base_url = base_url
        self.api_key = api_key

    def scrape(self, url, selectors):
        endpoint = f"{self.base_url}/web_scraper/scrape"
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        payload = {"url": url, "selectors": selectors}
        response = requests.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        return response.json() 