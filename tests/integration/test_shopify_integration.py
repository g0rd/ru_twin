"""
Integration tests for Shopify API interaction with RuTwin Crew.

These tests verify the integration between the RuTwin system and Shopify's GraphQL Admin API.
They test both the ShopifyClient and the shopify_tools functionality.
"""

import json
import os
import pytest
import responses
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from ru_twin.mcp_clients.shopify import ShopifyClient
from ru_twin.tools.shopify_tools import (
    analyze_product_sales,
    identify_product_performance_gaps,
    analyze_customer_product_interactions,
    audit_product_listings_for_seo,
    generate_seo_product_descriptions,
    monitor_inventory_levels,
    predict_inventory_needs,
    generate_restock_recommendations,
    ProductAnalyticsInput,
    PerformanceGapInput,
    CustomerInteractionInput,
    SEOAuditInput,
    ContentGenerationInput,
    InventoryMonitorInput,
    InventoryForecastInput,
    RestockRecommendationInput
)
from ru_twin.third_party_gateway import ThirdPartyGateway


# Example test (to be expanded)
# This would typically require a live or mocked Shopify instance
@pytest.mark.skip(reason="Shopify integration test not yet implemented")
def test_shopify_get_products():
    assert True


# Fixtures for test setup
@pytest.fixture
def mock_shopify_client():
    """Create a ShopifyClient with mocked responses."""
    client = ShopifyClient(
        shop_url="test-store.myshopify.com",
        access_token="test_access_token",
        api_version="2025-04"
    )
    return client


@pytest.fixture
def mock_gateway():
    """Create a mocked ThirdPartyGateway."""
    return MagicMock(spec=ThirdPartyGateway)


@pytest.fixture
def mock_graphql_response():
    """Return a mock GraphQL response for product queries."""
    return {
        "data": {
            "products": {
                "edges": [
                    {
                        "cursor": "cursor1",
                        "node": {
                            "id": "gid://shopify/Product/1",
                            "title": "Test Product 1",
                            "description": "This is a test product",
                            "handle": "test-product-1",
                            "tags": "tag1, tag2",
                            "priceRangeV2": {
                                "minVariantPrice": {
                                    "amount": "10.0",
                                    "currencyCode": "USD"
                                },
                                "maxVariantPrice": {
                                    "amount": "20.0",
                                    "currencyCode": "USD"
                                }
                            },
                            "images": {
                                "edges": [
                                    {
                                        "node": {
                                            "url": "https://example.com/image1.jpg",
                                            "altText": "Product Image"
                                        }
                                    }
                                ]
                            },
                            "variants": {
                                "edges": [
                                    {
                                        "node": {
                                            "id": "gid://shopify/ProductVariant/1",
                                            "title": "Default",
                                            "sku": "SKU001",
                                            "price": "15.0",
                                            "inventoryQuantity": 10,
                                            "inventoryItem": {
                                                "id": "gid://shopify/InventoryItem/1",
                                                "tracked": True
                                            }
                                        }
                                    }
                                ]
                            },
                            "metafields": {
                                "edges": []
                            }
                        }
                    }
                ],
                "pageInfo": {
                    "hasNextPage": False,
                    "endCursor": "cursor1"
                }
            }
        }
    }


@pytest.fixture
def mock_orders_response():
    """Return a mock GraphQL response for order queries."""
    return {
        "data": {
            "orders": {
                "edges": [
                    {
                        "node": {
                            "id": "gid://shopify/Order/1",
                            "name": "#1001",
                            "createdAt": (datetime.now() - timedelta(days=5)).isoformat(),
                            "totalPriceSet": {
                                "shopMoney": {
                                    "amount": "100.0",
                                    "currencyCode": "USD"
                                }
                            },
                            "lineItems": {
                                "edges": [
                                    {
                                        "node": {
                                            "quantity": 2,
                                            "product": {
                                                "id": "gid://shopify/Product/1",
                                                "title": "Test Product 1"
                                            },
                                            "variant": {
                                                "id": "gid://shopify/ProductVariant/1",
                                                "sku": "SKU001",
                                                "price": "15.0"
                                            }
                                        }
                                    }
                                ]
                            }
                        }
                    }
                ]
            }
        }
    }


@pytest.fixture
def mock_inventory_response():
    """Return a mock GraphQL response for inventory queries."""
    return {
        "data": {
            "product": {
                "id": "gid://shopify/Product/1",
                "title": "Test Product 1",
                "variants": {
                    "edges": [
                        {
                            "node": {
                                "id": "gid://shopify/ProductVariant/1",
                                "inventoryQuantity": 10,
                                "inventoryItem": {
                                    "id": "gid://shopify/InventoryItem/1",
                                    "tracked": True,
                                    "inventoryLevels": {
                                        "edges": [
                                            {
                                                "node": {
                                                    "available": 10,
                                                    "location": {
                                                        "name": "Main Location"
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                }
                            }
                        }
                    ]
                }
            }
        }
    }


# Client Integration Tests
@responses.activate
def test_get_product_list(mock_shopify_client, mock_graphql_response):
    """Test fetching product list from Shopify."""
    # Setup mock response
    responses.add(
        responses.POST,
        f"https://{mock_shopify_client.shop_url}/admin/api/{mock_shopify_client.api_version}/graphql.json",
        json=mock_graphql_response,
        status=200
    )
    
    # Execute the method
    products = mock_shopify_client.get_product_list(limit=10)
    
    # Assertions
    assert len(products) == 1
    assert products[0]["id"] == "1"  # ID should be extracted from GID
    assert products[0]["title"] == "Test Product 1"
    assert len(products[0]["variants"]) == 1
    assert products[0]["variants"][0]["sku"] == "SKU001"


@responses.activate
def test_get_product_by_id(mock_shopify_client, mock_graphql_response):
    """Test fetching a specific product by ID."""
    # Modify the response for a single product query
    single_product_response = {
        "data": {
            "product": mock_graphql_response["data"]["products"]["edges"][0]["node"]
        }
    }
    
    # Setup mock response
    responses.add(
        responses.POST,
        f"https://{mock_shopify_client.shop_url}/admin/api/{mock_shopify_client.api_version}/graphql.json",
        json=single_product_response,
        status=200
    )
    
    # Execute the method
    product = mock_shopify_client.get_product_by_id(1)
    
    # Assertions
    assert product["id"] == "1"
    assert product["title"] == "Test Product 1"
    assert product["handle"] == "test-product-1"


@responses.activate
def test_get_product_performance(mock_shopify_client, mock_orders_response):
    """Test getting product performance metrics."""
    # Setup mock responses
    responses.add(
        responses.POST,
        f"https://{mock_shopify_client.shop_url}/admin/api/{mock_shopify_client.api_version}/graphql.json",
        json=mock_orders_response,
        status=200
    )
    
    # For the product details lookup
    product_response = {
        "data": {
            "product": {
                "id": "gid://shopify/Product/1",
                "title": "Test Product 1"
            }
        }
    }
    
    responses.add(
        responses.POST,
        f"https://{mock_shopify_client.shop_url}/admin/api/{mock_shopify_client.api_version}/graphql.json",
        json=product_response,
        status=200
    )
    
    # Execute the method
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
    performance = mock_shopify_client.get_product_performance(
        product_ids=[1],
        start_date=start_date,
        end_date=end_date
    )
    
    # Assertions
    assert len(performance) > 0
    assert performance[0].product_id == "1"
    assert performance[0].title == "Test Product 1"
    assert performance[0].units_sold == 2  # From our mock data


@responses.activate
def test_identify_underperforming_products(mock_shopify_client, mock_orders_response, mock_graphql_response):
    """Test identifying underperforming products."""
    # Setup mock responses for orders
    responses.add(
        responses.POST,
        f"https://{mock_shopify_client.shop_url}/admin/api/{mock_shopify_client.api_version}/graphql.json",
        json=mock_orders_response,
        status=200
    )
    
    # For product details
    responses.add(
        responses.POST,
        f"https://{mock_shopify_client.shop_url}/admin/api/{mock_shopify_client.api_version}/graphql.json",
        json=mock_graphql_response,
        status=200
    )
    
    # For collections (categories)
    collections_response = {
        "data": {
            "collections": {
                "edges": [
                    {
                        "node": {
                            "id": "gid://shopify/Collection/1",
                            "title": "Test Category"
                        }
                    }
                ]
            }
        }
    }
    
    responses.add(
        responses.POST,
        f"https://{mock_shopify_client.shop_url}/admin/api/{mock_shopify_client.api_version}/graphql.json",
        json=collections_response,
        status=200
    )
    
    # Execute the method
    underperforming = mock_shopify_client.identify_underperforming_products(
        benchmark_type="category_average",
        performance_threshold=0.75,
        time_period="last_30_days"
    )
    
    # We can't make specific assertions about the results since they depend on the mock data
    # and the internal logic of the method, but we can check the general structure
    assert isinstance(underperforming, list)


# Tool Integration Tests
@patch('ru_twin.mcp_clients.shopify.ShopifyClient')
def test_analyze_product_sales_tool(mock_client_class):
    """Test the analyze_product_sales tool."""
    # Setup mock client
    mock_client = mock_client_class.return_value
    
    # Mock the get_product_performance method
    mock_client.get_product_performance.return_value = [
        MagicMock(
            product_id="1",
            title="Test Product 1",
            revenue=100.0,
            units_sold=10,
            profit_margin=0.4,
            conversion_rate=5.0,
            views=200,
            add_to_carts=20,
            checkout_initiations=15,
            dict=lambda: {
                "product_id": "1",
                "title": "Test Product 1",
                "revenue": 100.0,
                "units_sold": 10,
                "profit_margin": 0.4,
                "conversion_rate": 5.0,
                "views": 200,
                "add_to_carts": 20,
                "checkout_initiations": 15
            }
        )
    ]
    
    # Execute the tool
    result = analyze_product_sales(
        client=mock_client,
        input_data=ProductAnalyticsInput(
            time_period="last_30_days",
            metrics=["revenue", "units_sold", "profit_margin", "conversion_rate"]
        )
    )
    
    # Assertions
    assert "overall_metrics" in result
    assert "top_performers" in result
    assert result["overall_metrics"]["total_revenue"] == 100.0
    assert result["overall_metrics"]["total_units_sold"] == 10


@patch('ru_twin.mcp_clients.shopify.ShopifyClient')
def test_identify_product_performance_gaps_tool(mock_client_class):
    """Test the identify_product_performance_gaps tool."""
    # Setup mock client
    mock_client = mock_client_class.return_value
    
    # Mock the identify_underperforming_products method
    mock_client.identify_underperforming_products.return_value = [
        {
            "product_id": "1",
            "title": "Test Product 1",
            "reasons": ["Revenue is 50.0 vs category average 100.0", "Units sold is 5 vs category average 10"],
            "metrics": {
                "revenue": 50.0,
                "units_sold": 5,
                "profit_margin": 0.3,
                "conversion_rate": 2.5
            },
            "category_averages": {
                "revenue": 100.0,
                "units_sold": 10,
                "profit_margin": 0.4,
                "conversion_rate": 5.0
            }
        }
    ]
    
    # Execute the tool
    result = identify_product_performance_gaps(
        client=mock_client,
        input_data=PerformanceGapInput(
            benchmark_type="category_average",
            performance_threshold=0.75,
            time_period="last_30_days"
        )
    )
    
    # Assertions
    assert "summary" in result
    assert "underperforming_products" in result
    assert result["summary"]["total_underperforming"] == 1
    assert len(result["underperforming_products"]) == 1
    assert result["underperforming_products"][0]["product_id"] == "1"


@patch('ru_twin.mcp_clients.shopify.ShopifyClient')
def test_monitor_inventory_levels_tool(mock_client_class):
    """Test the monitor_inventory_levels tool."""
    # Setup mock client
    mock_client = mock_client_class.return_value
    
    # Mock the get_inventory_status method
    mock_client.get_inventory_status.return_value = [
        MagicMock(
            product_id="1",
            variant_id="1",
            sku="SKU001",
            title="Test Product 1 - Default",
            quantity=10,
            available=8,
            committed=2,
            reorder_point=5,
            is_low_stock=False,
            days_until_stockout=20,
            dict=lambda: {
                "product_id": "1",
                "variant_id": "1",
                "sku": "SKU001",
                "title": "Test Product 1 - Default",
                "quantity": 10,
                "available": 8,
                "committed": 2,
                "reorder_point": 5,
                "is_low_stock": False,
                "days_until_stockout": 20
            }
        ),
        MagicMock(
            product_id="2",
            variant_id="2",
            sku="SKU002",
            title="Test Product 2 - Default",
            quantity=3,
            available=2,
            committed=1,
            reorder_point=5,
            is_low_stock=True,
            days_until_stockout=5,
            dict=lambda: {
                "product_id": "2",
                "variant_id": "2",
                "sku": "SKU002",
                "title": "Test Product 2 - Default",
                "quantity": 3,
                "available": 2,
                "committed": 1,
                "reorder_point": 5,
                "is_low_stock": True,
                "days_until_stockout": 5
            }
        )
    ]
    
    # Execute the tool
    result = monitor_inventory_levels(
        client=mock_client,
        input_data=InventoryMonitorInput(
            check_frequency="daily",
            low_stock_threshold=0.2
        )
    )
    
    # Assertions
    assert "inventory_summary" in result
    assert "alerts" in result
    assert result["inventory_summary"]["total_items"] == 2
    assert result["inventory_summary"]["low_stock"] == 1
    assert len(result["alerts"]) >= 1


# Error Handling Tests
@responses.activate
def test_client_handles_rate_limiting(mock_shopify_client):
    """Test that the client properly handles rate limiting responses."""
    # Setup mock rate limit response
    responses.add(
        responses.POST,
        f"https://{mock_shopify_client.shop_url}/admin/api/{mock_shopify_client.api_version}/graphql.json",
        json={"errors": [{"message": "Rate limited", "extensions": {"code": "THROTTLED"}}]},
        status=200
    )
    
    # Setup success response after rate limit
    responses.add(
        responses.POST,
        f"https://{mock_shopify_client.shop_url}/admin/api/{mock_shopify_client.api_version}/graphql.json",
        json={"data": {"products": {"edges": []}}},
        status=200
    )
    
    # Set a short retry delay for testing
    mock_shopify_client.retry_delay = 0.1
    
    # Execute the method - it should retry and eventually succeed
    products = mock_shopify_client.get_product_list(limit=10)
    
    # Assertions
    assert isinstance(products, list)
    assert len(responses.calls) == 2  # Should have made two calls


@responses.activate
def test_client_handles_graphql_errors(mock_shopify_client):
    """Test that the client properly handles GraphQL errors."""
    # Setup mock error response
    responses.add(
        responses.POST,
        f"https://{mock_shopify_client.shop_url}/admin/api/{mock_shopify_client.api_version}/graphql.json",
        json={"errors": [{"message": "Invalid query", "extensions": {"code": "GRAPHQL_VALIDATION_ERROR"}}]},
        status=200
    )
    
    # Execute the method - it should raise an exception
    with pytest.raises(Exception) as excinfo:
        mock_shopify_client.get_product_list(limit=10)
    
    # Assertions
    assert "GraphQL error" in str(excinfo.value)


@responses.activate
def test_client_handles_http_errors(mock_shopify_client):
    """Test that the client properly handles HTTP errors."""
    # Setup mock HTTP error response
    responses.add(
        responses.POST,
        f"https://{mock_shopify_client.shop_url}/admin/api/{mock_shopify_client.api_version}/graphql.json",
        json={"error": "Unauthorized"},
        status=401
    )
    
    # Execute the method - it should raise an exception
    with pytest.raises(Exception) as excinfo:
        mock_shopify_client.get_product_list(limit=10)
    
    # Assertions
    assert "HTTP error 401" in str(excinfo.value)


# Gateway Integration Tests
def test_client_uses_gateway(mock_gateway):
    """Test that the client properly uses the gateway if provided."""
    # Setup mock gateway response
    mock_gateway.make_request.return_value = {
        "data": {
            "products": {
                "edges": []
            }
        }
    }
    
    # Create client with gateway
    client = ShopifyClient(
        shop_url="test-store.myshopify.com",
        access_token="test_access_token",
        api_version="2025-04",
        gateway=mock_gateway
    )
    
    # Execute a method
    client.get_product_list(limit=10)
    
    # Assertions
    mock_gateway.make_request.assert_called_once()
    args, kwargs = mock_gateway.make_request.call_args
    assert kwargs["endpoint"] == f"https://test-store.myshopify.com/admin/api/2025-04/graphql.json"
    assert kwargs["method"] == "POST"
    assert "headers" in kwargs
    assert "json" in kwargs
