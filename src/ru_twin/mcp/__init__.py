# Use lazy imports to avoid circular imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .server.server import MCPServer
    from .client.client import MCPClient
    from .utils.base import BaseTool, ToolInputSchema

__all__ = ['MCPServer', 'MCPClient', 'BaseTool', 'ToolInputSchema']

def __getattr__(name):
    if name == 'MCPServer':
        from .server.server import MCPServer
        return MCPServer
    elif name == 'MCPClient':
        from .client.client import MCPClient
        return MCPClient
    elif name in ('BaseTool', 'ToolInputSchema'):
        from .utils.base import BaseTool, ToolInputSchema
        return {'BaseTool': BaseTool, 'ToolInputSchema': ToolInputSchema}[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")