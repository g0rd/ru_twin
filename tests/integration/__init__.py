"""
Integration Tests for RuTwin Crew

This package contains integration tests for RuTwin's external service integrations,
including Shopify and Teller API clients, tools, and tasks.

Integration tests verify that our components work correctly with external services
or with multiple components working together.
"""

import os
import pytest
from typing import Dict, Any, Callable, Generator
from unittest.mock import MagicMock, patch

# Constants for testing
TEST_ENVIRONMENT = os.environ.get("TEST_ENVIRONMENT", "test")
MOCK_EXTERNAL_SERVICES = os.environ.get("MOCK_EXTERNAL_SERVICES", "true").lower() == "true"

# Shared test utilities
def get_test_config() -> Dict[str, Any]:
    """
    Get configuration for integration tests based on environment.
    
    Returns:
        Dictionary containing test configuration
    """
    if TEST_ENVIRONMENT == "test":
        return {
            "shopify": {
                "shop_url": "test-store.myshopify.com",
                "access_token": "test_token",
                "api_version": "2025-04"
            },
            "teller": {
                "access_token": "test_token",
                "environment": "sandbox"
            }
        }
    elif TEST_ENVIRONMENT == "integration":
        # For actual integration testing against real (sandbox) services
        return {
            "shopify": {
                "shop_url": os.environ.get("SHOPIFY_SHOP_URL", ""),
                "access_token": os.environ.get("SHOPIFY_ACCESS_TOKEN", ""),
                "api_version": os.environ.get("SHOPIFY_API_VERSION", "2025-04")
            },
            "teller": {
                "access_token": os.environ.get("TELLER_ACCESS_TOKEN", ""),
                "environment": os.environ.get("TELLER_ENVIRONMENT", "sandbox")
            }
        }
    else:
        raise ValueError(f"Unknown test environment: {TEST_ENVIRONMENT}")

# Pytest fixtures will be defined in conftest.py
