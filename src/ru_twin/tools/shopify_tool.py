from crewai_tools import BaseTool
import httpx

class ShopifyMCPTool(BaseTool):
    name = "Shopify MCP Server"
    description = "Queries the guMCP server for Shopify-related tasks."

    def _run(self, input: str) -> str:
        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": input}],
            "stream": False
        }
        url = "http://localhost:8000/invoke"
        headers = {"Content-Type": "application/json"}

        response = httpx.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
