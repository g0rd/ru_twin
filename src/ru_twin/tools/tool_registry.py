from typing import Dict, Type, List
from crewai.tools import BaseTool
from .development_tools import CodeGenerator, ArchitectureDesigner
from .pr_tools import MediaMonitor, ContentStrategist
from .integration_tools import APIDesigner
from .research_tools import MarketAnalysis, CompetitorAnalysis
from .financial_tools import FinancialAnalysis, BudgetPlanner
from .legal_tools import LegalAnalysis, ComplianceChecker
from .assistant_tools import TaskManager, ProgressTracker
from .vapi_tools import ListCallsTool, InitiateCallTool
from .mcp_clients.gumloop_google_sheets import GumloopGoogleSheetsMCP
from .mcp_clients.gumloop_gmail import GumloopGmailMCP
from .mcp_clients.gumloop_slack import GumloopSlackMCP
from .mcp_clients.senso import SensoMCP
from .mcp_clients.goose import GooseMCP
from .mcp_clients.shopify_mcp import ShopifyMCPClient

class ToolRegistry:
    """Registry for managing custom tools."""
    
    def __init__(self):
        self.tools: Dict[str, callable] = {
            "code_generator": CodeGenerator,
            "architecture_designer": ArchitectureDesigner,
            "media_monitor": MediaMonitor,
            "content_strategist": ContentStrategist,
            "api_designer": APIDesigner,
            "market_analysis": MarketAnalysis,
            "competitor_analysis": CompetitorAnalysis,
            "financial_analysis": FinancialAnalysis,
            "budget_planner": BudgetPlanner,
            "legal_analysis": LegalAnalysis,
            "compliance_checker": ComplianceChecker,
            "task_manager": TaskManager,
            "progress_tracker": ProgressTracker,
            "vapi_list_calls": ListCallsTool,
            "vapi_initiate_call": InitiateCallTool,
            "google_sheets_read": GumloopGoogleSheetsMCP(base_url="https://api.gumloop.com", api_key="YOUR_KEY").read_sheet,
            "google_sheets_write": GumloopGoogleSheetsMCP(base_url="https://api.gumloop.com", api_key="YOUR_KEY").write_sheet,
            "gmail_read": GumloopGmailMCP(base_url="https://api.gumloop.com", api_key="YOUR_KEY").read_emails,
            "gmail_send": GumloopGmailMCP(base_url="https://api.gumloop.com", api_key="YOUR_KEY").send_email,
            "slack_send_message": GumloopSlackMCP(base_url="https://api.gumloop.com", api_key="YOUR_KEY").send_message,
        }
        self.senso = SensoMCP(api_key="YOUR_SENSO_API_KEY")
        self.goose = GooseMCP(goose_cli_path="goose")
        self.shopify_mcp = ShopifyMCPClient(base_url="http://shopify_mcp:5005")
        self.tools.update({
            "senso_upload_content": self.senso.upload_content,
            "senso_list_content": self.senso.list_content,
            "senso_search": self.senso.search,
            "senso_generate": self.senso.generate,
            "goose_code": self.goose.run_prompt,
            "goose_project": self.goose.create_project,
            "shopify_search_dev_docs": self.shopify_mcp.search_dev_docs,
            "shopify_introspect_admin_schema": self.shopify_mcp.introspect_admin_schema,
            "shopify_admin_graphql": self.shopify_mcp.shopify_admin_graphql,
        })
    
    def get_tool(self, tool_name: str) -> callable:
        """Get a tool by name."""
        return self.tools.get(tool_name)
    
    def get_tools_for_agent(self, agent_name: str) -> List[callable]:
        """Get all tools for a specific agent."""
        agent_tool_mapping = {
            "Digital Twin": [
                "task_manager",
                "progress_tracker",
                "market_analysis"
            ],
            "CPG Researcher": [
                "market_analysis",
                "competitor_analysis"
            ],
            "CPG Salesperson": [
                "competitor_analysis",
                "market_analysis"
            ],
            "Executive Assistant": [
                "task_manager",
                "progress_tracker"
            ],
            "Accountability Buddy": [
                "progress_tracker",
                "task_manager"
            ],
            "CFO": [
                "financial_analysis",
                "budget_planner"
            ],
            "Legal Advisor": [
                "legal_analysis",
                "compliance_checker"
            ],
            "PR Strategist": [
                "media_monitor",
                "content_strategist"
            ]
        }
        
        tool_names = agent_tool_mapping.get(agent_name, [])
        return [self.get_tool(tool_name) for tool_name in tool_names if self.get_tool(tool_name)] 