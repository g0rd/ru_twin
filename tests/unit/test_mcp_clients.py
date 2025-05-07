"""
Unit tests for MCP Clients in RuTwin Crew

This module contains tests for the various MCP (Master Control Program) clients
used to interact with external services like Shopify and Teller.
"""

import json
import pytest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime

# Import the MCP clients
from ru_twin.mcp_clients.shopify import ShopifyClient
from ru_twin.mcp_clients.teller import TellerClient
from ru_twin.third_party_gateway import ThirdPartyGateway


# Fixtures for common test setup
@pytest.fixture
def mock_gateway():
    """Create a mock ThirdPartyGateway for testing."""
    return MagicMock(spec=ThirdPartyGateway)


@pytest.fixture
def shopify_client(mock_gateway):
    """Create a ShopifyClient instance for testing."""
    client = ShopifyClient(
        shop_url="test-store.myshopify.com",
        access_token="test_access_token",
        api_version="2025-04",
        gateway=mock_gateway
    )
    # Mock the _execute_graphql_query method to avoid actual API calls
    client._execute_graphql_query = MagicMock(return_value={})
    return client


@pytest.fixture
def teller_client(mock_gateway):
    """Create a TellerClient instance for testing."""
    client = TellerClient(
        access_token="test_access_token",
        environment="sandbox",
        gateway=mock_gateway
    )
    # Mock the _make_request method to avoid actual API calls
    client._make_request = MagicMock(return_value={})
    return client


# ShopifyClient Tests
class TestShopifyClient:
    """Tests for the ShopifyClient."""

    def test_initialization(self, mock_gateway):
        """Test that the ShopifyClient initializes correctly."""
        client = ShopifyClient(
            shop_url="test-store.myshopify.com",
            access_token="test_access_token",
            api_version="2025-04",
            gateway=mock_gateway
        )
        
        assert client.shop_url == "test-store.myshopify.com"
        assert client.access_token == "test_access_token"
        assert client.api_version == "2025-04"
        assert client.gateway == mock_gateway
        assert client.endpoint == "https://test-store.myshopify.com/admin/api/2025-04/graphql.json"
        assert "X-Shopify-Access-Token" in client.headers

    def test_extract_id_from_gid(self, shopify_client):
        """Test the extraction of IDs from Shopify's global IDs."""
        gid = "gid://shopify/Product/12345"
        extracted_id = shopify_client._extract_id_from_gid(gid)
        assert extracted_id == "12345"
        
        # Test with empty or invalid GID
        assert shopify_client._extract_id_from_gid("") == ""
        assert shopify_client._extract_id_from_gid("invalid") == "invalid"

    def test_create_gid(self, shopify_client):
        """Test the creation of Shopify's global IDs."""
        gid = shopify_client._create_gid("Product", "12345")
        assert gid == "gid://shopify/Product/12345"

    @patch('requests.post')
    def test_handle_rate_limiting(self, mock_post, shopify_client):
        """Test that rate limiting is handled correctly."""
        # Mock response with rate limit headers
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'X-Shopify-Shop-Api-Call-Limit': '10/40'}
        mock_response.json.return_value = {'data': {}}
        mock_post.return_value = mock_response
        
        # Reset the mocked _execute_graphql_query to use the real method
        shopify_client._execute_graphql_query = ShopifyClient._execute_graphql_query.__get__(shopify_client)
        
        # Call a method that uses _execute_graphql_query
        with patch.object(shopify_client, '_handle_rate_limiting') as mock_handle_rate_limiting:
            shopify_client._execute_graphql_query("query { shop { name } }", {}, 5)
            
            # Verify that rate limiting was handled
            mock_handle_rate_limiting.assert_called_once()

    @patch('requests.post')
    def test_error_handling(self, mock_post, shopify_client):
        """Test that GraphQL errors are handled correctly."""
        # Mock response with GraphQL error
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'errors': [{
                'message': 'Test error message',
                'extensions': {'code': 'THROTTLED'}
            }]
        }
        mock_post.return_value = mock_response
        
        # Reset the mocked _execute_graphql_query to use the real method
        shopify_client._execute_graphql_query = ShopifyClient._execute_graphql_query.__get__(shopify_client)
        
        # Test with retry logic mocked to avoid actual retries
        with patch.object(shopify_client, '_handle_rate_limiting'):
            with pytest.raises(Exception) as excinfo:
                shopify_client._execute_graphql_query("query { shop { name } }", {}, 5)
            
            assert "GraphQL error" in str(excinfo.value)

    def test_get_product_list(self, shopify_client):
        """Test the get_product_list method."""
        # Mock the response from _execute_graphql_query
        mock_products_response = {
            'products': {
                'edges': [
                    {
                        'cursor': 'cursor1',
                        'node': {
                            'id': 'gid://shopify/Product/1',
                            'title': 'Test Product 1',
                            'description': 'Description 1',
                            'handle': 'test-product-1',
                            'tags': 'tag1, tag2',
                            'variants': {'edges': []},
                            'images': {'edges': []}
                        }
                    },
                    {
                        'cursor': 'cursor2',
                        'node': {
                            'id': 'gid://shopify/Product/2',
                            'title': 'Test Product 2',
                            'description': 'Description 2',
                            'handle': 'test-product-2',
                            'tags': 'tag3, tag4',
                            'variants': {'edges': []},
                            'images': {'edges': []}
                        }
                    }
                ],
                'pageInfo': {
                    'hasNextPage': False,
                    'endCursor': 'cursor2'
                }
            }
        }
        shopify_client._execute_graphql_query.return_value = mock_products_response
        
        # Call the method
        products = shopify_client.get_product_list(limit=2)
        
        # Verify the results
        assert len(products) == 2
        assert products[0]['id'] == '1'
        assert products[0]['title'] == 'Test Product 1'
        assert products[1]['id'] == '2'
        assert products[1]['title'] == 'Test Product 2'


# TellerClient Tests
class TestTellerClient:
    """Tests for the TellerClient."""

    def test_initialization(self, mock_gateway):
        """Test that the TellerClient initializes correctly."""
        client = TellerClient(
            access_token="test_access_token",
            environment="sandbox",
            gateway=mock_gateway
        )
        
        assert client.access_token == "test_access_token"
        assert client.environment == "sandbox"
        assert client.gateway == mock_gateway
        assert client.base_url == "https://api.teller.io"
        assert "Authorization" in client.headers
        assert client.headers["Authorization"] == "Bearer test_access_token"

    @patch('requests.get')
    def test_handle_rate_limiting(self, mock_get, teller_client):
        """Test that rate limiting is handled correctly."""
        # First response hits rate limit, second succeeds
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {'Retry-After': '1'}
        
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {'id': '123', 'name': 'Test Account'}
        
        mock_get.side_effect = [rate_limit_response, success_response]
        
        # Reset the mocked _make_request to use the real method
        teller_client._make_request = TellerClient._make_request.__get__(teller_client)
        
        # Patch sleep to avoid actual waiting
        with patch('time.sleep'):
            result = teller_client._make_request('/accounts/123')
            
            # Verify the result is from the second (successful) call
            assert result == {'id': '123', 'name': 'Test Account'}
            
            # Verify get was called twice (once for rate limit, once for success)
            assert mock_get.call_count == 2

    @patch('requests.get')
    def test_error_handling(self, mock_get, teller_client):
        """Test that API errors are handled correctly."""
        # Mock response with error
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            'error': 'NOT_FOUND',
            'message': 'Account not found'
        }
        mock_get.return_value = mock_response
        
        # Reset the mocked _make_request to use the real method
        teller_client._make_request = TellerClient._make_request.__get__(teller_client)
        
        # Test error handling
        with pytest.raises(Exception) as excinfo:
            teller_client._make_request('/accounts/nonexistent')
            
        assert "Teller API error" in str(excinfo.value)
        assert "NOT_FOUND" in str(excinfo.value)

    def test_get_accounts(self, teller_client):
        """Test the get_accounts method."""
        # Mock the response from _make_request
        mock_accounts_response = [
            {
                'id': 'acc_123',
                'institution': {'name': 'Test Bank'},
                'last_four': '1234',
                'name': 'Checking Account',
                'subtype': 'checking',
                'type': 'depository',
                'status': 'open'
            },
            {
                'id': 'acc_456',
                'institution': {'name': 'Test Bank'},
                'last_four': '5678',
                'name': 'Savings Account',
                'subtype': 'savings',
                'type': 'depository',
                'status': 'open'
            }
        ]
        teller_client._make_request.return_value = mock_accounts_response
        
        # Call the method
        accounts = teller_client.get_accounts()
        
        # Verify the results
        assert len(accounts) == 2
        assert accounts[0].id == 'acc_123'
        assert accounts[0].name == 'Checking Account'
        assert accounts[0].type.value == 'depository'
        assert accounts[1].id == 'acc_456'
        assert accounts[1].name == 'Savings Account'

    def test_categorize_transactions(self, teller_client):
        """Test the categorize_transactions method."""
        # Create test transactions
        from ru_twin.mcp_clients.teller import Transaction, TransactionStatus, TransactionType
        
        transactions = [
            Transaction(
                id='txn_1',
                account_id='acc_123',
                amount=50.0,
                date='2023-05-01',
                description='Grocery Store',
                status=TransactionStatus.POSTED,
                type=TransactionType.PURCHASE
            ),
            Transaction(
                id='txn_2',
                account_id='acc_123',
                amount=1000.0,
                date='2023-05-02',
                description='Salary',
                status=TransactionStatus.POSTED,
                type=TransactionType.DEPOSIT
            ),
            Transaction(
                id='txn_3',
                account_id='acc_123',
                amount=25.0,
                date='2023-05-03',
                description='Restaurant',
                status=TransactionStatus.POSTED,
                type=TransactionType.PURCHASE
            )
        ]
        
        # Call the method
        categorized = teller_client.categorize_transactions(transactions)
        
        # Verify the results
        assert 'purchase' in categorized
        assert 'deposit' in categorized
        assert len(categorized['purchase']) == 2
        assert len(categorized['deposit']) == 1
        assert categorized['purchase'][0].description == 'Grocery Store'
        assert categorized['purchase'][1].description == 'Restaurant'
        assert categorized['deposit'][0].description == 'Salary'


# General MCP Client Tests
def test_example_mcp_client():
    """Example test as specified in the instructions."""
    assert True
