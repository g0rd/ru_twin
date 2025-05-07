import os
import pytest
from unittest.mock import MagicMock, patch
import yaml
from pathlib import Path

# Base URL for integration tests
@pytest.fixture(scope="session")
def base_url():
    """Return the base URL for integration tests."""
    return "http://localhost:8000"  # Assuming your app runs here for integration tests

# Mock clients for external services
@pytest.fixture
def mock_shopify_client():
    """Return a mock Shopify client for testing."""
    from ru_twin.mcp_clients.shopify import ShopifyClient
    mock_client = MagicMock(spec=ShopifyClient)
    return mock_client

@pytest.fixture
def mock_teller_client():
    """Return a mock Teller client for testing."""
    from ru_twin.mcp_clients.teller import TellerClient
    mock_client = MagicMock(spec=TellerClient)
    return mock_client

# Test configuration fixtures
@pytest.fixture
def test_config_dir():
    """Return the path to the test configuration directory."""
    return Path(__file__).parent / "test_configs"

@pytest.fixture
def test_agents_config(test_config_dir):
    """Return a test agents configuration."""
    config_path = test_config_dir / "agents.yaml"
    if config_path.exists():
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "role": "For testing purposes",
                "goal": "Complete test tasks successfully",
                "backstory": "A test agent created for unit testing",
                "tools": ["test_tool"]
            }
        }
    }

@pytest.fixture
def test_tasks_config(test_config_dir):
    """Return a test tasks configuration."""
    config_path = test_config_dir / "tasks.yaml"
    if config_path.exists():
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return {
        "tasks": {
            "test_task": {
                "name": "Test Task",
                "description": "A task for testing",
                "expected_output": "Test output",
                "required_tools": ["test_tool"],
                "dependencies": [],
                "agent": "test_agent",
                "priority": "medium"
            }
        }
    }

# Mock for the third party gateway
@pytest.fixture
def mock_third_party_gateway():
    """Return a mock third party gateway."""
    from ru_twin.third_party_gateway import ThirdPartyGateway
    mock_gateway = MagicMock(spec=ThirdPartyGateway)
    return mock_gateway

# Environment variable fixture
@pytest.fixture
def test_env_vars():
    """Set up test environment variables and restore them after the test."""
    original_env = os.environ.copy()
    
    # Set test environment variables
    test_vars = {
        "SHOPIFY_API_KEY": "test_api_key",
        "SHOPIFY_API_SECRET": "test_api_secret",
        "SHOPIFY_API_VERSION": "2023-07",
        "TELLER_ACCESS_TOKEN": "test_access_token",
        "TELLER_ENVIRONMENT": "sandbox"
    }
    
    for key, value in test_vars.items():
        os.environ[key] = value
    
    yield test_vars
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)

# Tool registry fixture
@pytest.fixture
def mock_tool_registry():
    """Return a mock tool registry."""
    from ru_twin.tools.tool_registry import ToolRegistry
    mock_registry = MagicMock(spec=ToolRegistry)
    return mock_registry

# Arize Phoenix fixture for observability testing
@pytest.fixture
def mock_phoenix_client():
    """Return a mock Arize Phoenix client for testing observability."""
    mock_client = MagicMock()
    mock_client.log_trace.return_value = None
    with patch("arize.phoenix.Client", return_value=mock_client):
        yield mock_client

# CrewAI fixtures
@pytest.fixture
def mock_crew():
    """Return a mock CrewAI Crew object."""
    mock_crew_obj = MagicMock()
    mock_crew_obj.kickoff.return_value = "Task completed successfully"
    
    with patch("crewai.Crew", return_value=mock_crew_obj):
        yield mock_crew_obj

@pytest.fixture
def mock_agent():
    """Return a mock CrewAI Agent object."""
    mock_agent_obj = MagicMock()
    
    with patch("crewai.Agent", return_value=mock_agent_obj):
        yield mock_agent_obj

@pytest.fixture
def mock_task():
    """Return a mock CrewAI Task object."""
    mock_task_obj = MagicMock()
    
    with patch("crewai.Task", return_value=mock_task_obj):
        yield mock_task_obj
