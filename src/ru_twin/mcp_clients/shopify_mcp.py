import requests

class ShopifyMCPClient:
    def __init__(self, base_url="http://shopify_mcp:5005"):
        self.base_url = base_url

    def search_dev_docs(self, query):
        # Example endpoint, adjust as per actual MCP API
        response = requests.post(f"{self.base_url}/tool/search_dev_docs", json={"query": query})
        response.raise_for_status()
        return response.json()

    def introspect_admin_schema(self, query):
        response = requests.post(f"{self.base_url}/tool/introspect_admin_schema", json={"query": query})
        response.raise_for_status()
        return response.json()

    def shopify_admin_graphql(self, graphql_query):
        response = requests.post(f"{self.base_url}/prompt/shopify_admin_graphql", json={"query": graphql_query})
        response.raise_for_status()
        return response.json() 