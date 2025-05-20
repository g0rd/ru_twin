import logging
import os
from typing import Dict, Callable, Any, Optional

from pydantic import BaseModel

from ru_twin.mcp.client.shopify_client import ShopifyClient
from ru_twin.mcp.client.teller_client import TellerClient


class ToolRegistry:
    """
    A registry for tools that can be used by AI agents.

    This class manages the available tools, their descriptions, and input models.
    It allows agents to discover and use tools for various tasks.
    """

    def __init__(self):
        """Initialize the ToolRegistry with available tools."""
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)

        # Initialize Shopify MCP client if credentials are available
        shopify_shop_url = os.getenv("SHOPIFY_SHOP_URL")
        shopify_access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")

        if shopify_shop_url and shopify_access_token:
            self.shopify_mcp = ShopifyClient(
                shop_url=shopify_shop_url,
                access_token=shopify_access_token
            )
            self.logger.info("Shopify client initialized in ToolRegistry")
        else:
            self.shopify_mcp = None
            self.logger.warning(
                "Shopify client not initialized in ToolRegistry. "
                "Missing SHOPIFY_SHOP_URL or SHOPIFY_ACCESS_TOKEN environment variables."
            )

        # Initialize Teller MCP client (replace with actual initialization if needed)
        self.teller_mcp = None
        # Add Teller initialization logic here if needed

    def register_tool(self, name: str, function: Callable, description: str, input_model: BaseModel):
        """
        Register a new tool with the registry.

        Args:
            name: The name of the tool.
            function: The callable function that implements the tool.
            description: A description of what the tool does.
            input_model: A Pydantic model defining the tool's input parameters.
        """
        self.tools[name] = {
            "function": function,
            "description": description,
            "input_model": input_model
        }
        self.logger.info(f"Registered tool: {name}")

    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a tool from the registry by name.

        Args:
            name: The name of the tool.

        Returns:
            The tool's information (function, description, input model) or None if not found.
        """
        return self.tools.get(name)

    def get_all_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all registered tools.

        Returns:
            A dictionary of all registered tools.
        """
        return self.tools

    def is_tool_available(self, name: str) -> bool:
        """
        Check if a tool is available in the registry.

        Args:
            name: The name of the tool.

        Returns:
            True if the tool is available, False otherwise.
        """
        return name in self.tools
