"""
Shopify MCP Client for RuTwin Crew

This module provides a client for interacting with the Shopify GraphQL Admin API to perform
product analytics, SEO optimization, and inventory management tasks.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any

import requests
from pydantic import BaseModel, Field

from ru_twin.mcp_client import MCPClient
from ru_twin.third_party_gateway import ThirdPartyGateway


class ProductPerformanceMetrics(BaseModel):
    """Model for product performance metrics"""
    product_id: str
    title: str
    revenue: float = 0.0
    units_sold: int = 0
    profit_margin: float = 0.0
    conversion_rate: float = 0.0
    views: int = 0
    add_to_carts: int = 0
    checkout_initiations: int = 0


class InventoryStatus(BaseModel):
    """Model for inventory status"""
    product_id: str
    variant_id: str
    sku: str
    title: str
    quantity: int
    available: int
    committed: int
    reorder_point: Optional[int] = None
    is_low_stock: bool = False
    days_until_stockout: Optional[int] = None


class SEOMetadata(BaseModel):
    """Model for SEO metadata"""
    product_id: str
    title: str
    description: str
    url: str
    handle: str
    tags: List[str]
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    keyword_density: Optional[float] = None
    seo_score: Optional[float] = None


class ShopifyClient(MCPClient):
    """
    Client for interacting with Shopify GraphQL Admin API.
    
    This client handles authentication and provides methods for product analytics,
    SEO optimization, and inventory management using Shopify's GraphQL API.
    """
    
    def __init__(
        self,
        shop_url: str,
        access_token: str,
        api_version: str = "2025-04",
        gateway: Optional[ThirdPartyGateway] = None,
    ):
        """
        Initialize the Shopify GraphQL client.
        
        Args:
            shop_url: The URL of the Shopify store (e.g., 'my-store.myshopify.com')
            access_token: The Shopify Admin API access token
            api_version: The Shopify API version to use
            gateway: Optional ThirdPartyGateway for routing requests
        """
        super().__init__(gateway)
        self.shop_url = shop_url
        self.access_token = access_token
        self.api_version = api_version
        self.logger = logging.getLogger(__name__)
        
        # GraphQL endpoint
        self.endpoint = f"https://{self.shop_url}/admin/api/{self.api_version}/graphql.json"
        
        # Headers for GraphQL requests
        self.headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": self.access_token
        }
        
        # Rate limiting parameters
        self.max_retries = 5
        self.retry_delay = 1.0
        self.last_request_time = 0
        self.min_request_interval = 0.5  # seconds between requests to avoid rate limits
        self.available_points = 1000  # Default bucket size for GraphQL API

    def _handle_rate_limiting(self, cost: int = 1) -> None:
        """
        Handle rate limiting by ensuring minimum time between requests and tracking query cost.
        
        Args:
            cost: Estimated cost of the query in points
        """
        # Ensure we have enough points
        if cost > self.available_points:
            self.logger.warning(f"Query cost ({cost}) exceeds available points ({self.available_points}). Waiting for reset.")
            time.sleep(2.0)  # Wait for points to reset
            
        # Ensure minimum time between requests
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            time.sleep(sleep_time)
            
        self.last_request_time = time.time()

    def _execute_graphql_query(self, query: str, variables: Dict = None, estimated_cost: int = 1) -> Dict:
        """
        Execute a GraphQL query against the Shopify Admin API.
        
        Args:
            query: The GraphQL query string
            variables: Variables to include with the query
            estimated_cost: Estimated cost of the query in points
            
        Returns:
            The GraphQL response data
            
        Raises:
            Exception: If the GraphQL query fails after all retries
        """
        if variables is None:
            variables = {}
            
        payload = {
            "query": query,
            "variables": variables
        }
        
        retries = 0
        while retries < self.max_retries:
            self._handle_rate_limiting(estimated_cost)
            
            try:
                response = requests.post(
                    self.endpoint,
                    headers=self.headers,
                    json=payload
                )
                
                # Update rate limit info from headers
                if 'X-Shopify-Shop-Api-Call-Limit' in response.headers:
                    limit_header = response.headers['X-Shopify-Shop-Api-Call-Limit']
                    current, limit = map(int, limit_header.split('/'))
                    self.available_points = limit - current
                    
                # Handle response
                if response.status_code == 200:
                    result = response.json()
                    
                    # Check for GraphQL errors
                    if 'errors' in result:
                        errors = result['errors']
                        error_message = errors[0].get('message', 'Unknown GraphQL error')
                        error_code = errors[0].get('extensions', {}).get('code', 'UNKNOWN_ERROR')
                        
                        if error_code == 'THROTTLED':
                            # Handle rate limiting
                            self.logger.warning(f"Rate limited by Shopify GraphQL API: {error_message}")
                            retry_after = 1.0  # Default retry delay
                            retries += 1
                            time.sleep(retry_after)
                            continue
                        else:
                            # Other GraphQL error
                            self.logger.error(f"GraphQL error: {error_message} (Code: {error_code})")
                            raise Exception(f"GraphQL error: {error_message}")
                    
                    # Return data if successful
                    if 'data' in result:
                        return result['data']
                    else:
                        return {}
                        
                elif response.status_code == 429:
                    # Too Many Requests
                    retry_after = float(response.headers.get('Retry-After', self.retry_delay))
                    self.logger.warning(f"Rate limited by Shopify. Retrying after {retry_after} seconds")
                    time.sleep(retry_after)
                    retries += 1
                else:
                    # Other HTTP error
                    self.logger.error(f"HTTP error {response.status_code}: {response.text}")
                    raise Exception(f"HTTP error {response.status_code}: {response.text}")
                    
            except requests.RequestException as e:
                self.logger.error(f"Request error: {e}")
                retries += 1
                time.sleep(self.retry_delay)
                
        raise Exception(f"Failed to execute GraphQL query after {self.max_retries} retries")

    # Product Analytics Methods
    
    def get_product_list(self, limit: int = 50, cursor: str = None) -> List[Dict]:
        """
        Get a list of products from the Shopify store.
        
        Args:
            limit: Maximum number of products to return
            cursor: Cursor for pagination
            
        Returns:
            List of product dictionaries
        """
        query = """
        query GetProducts($limit: Int!, $cursor: String) {
          products(first: $limit, after: $cursor) {
            edges {
              cursor
              node {
                id
                title
                description
                handle
                tags
                priceRangeV2 {
                  minVariantPrice {
                    amount
                    currencyCode
                  }
                  maxVariantPrice {
                    amount
                    currencyCode
                  }
                }
                images(first: 1) {
                  edges {
                    node {
                      url
                      altText
                    }
                  }
                }
                variants(first: 10) {
                  edges {
                    node {
                      id
                      title
                      sku
                      price
                      inventoryQuantity
                      inventoryItem {
                        id
                        tracked
                      }
                    }
                  }
                }
                metafields(first: 10) {
                  edges {
                    node {
                      namespace
                      key
                      value
                    }
                  }
                }
              }
            }
            pageInfo {
              hasNextPage
              endCursor
            }
          }
        }
        """
        
        variables = {
            "limit": limit,
            "cursor": cursor
        }
        
        # Estimated cost: 10 points per product
        estimated_cost = limit * 10
        
        result = self._execute_graphql_query(query, variables, estimated_cost)
        
        # Extract products from the edges
        products = []
        if 'products' in result and 'edges' in result['products']:
            for edge in result['products']['edges']:
                product = edge['node']
                
                # Convert GraphQL IDs to regular IDs
                product['id'] = self._extract_id_from_gid(product['id'])
                
                # Convert variant IDs
                if 'variants' in product and 'edges' in product['variants']:
                    for variant_edge in product['variants']['edges']:
                        variant = variant_edge['node']
                        variant['id'] = self._extract_id_from_gid(variant['id'])
                        if 'inventoryItem' in variant and variant['inventoryItem']:
                            variant['inventoryItem']['id'] = self._extract_id_from_gid(variant['inventoryItem']['id'])
                
                products.append(product)
                
        return products

    def _extract_id_from_gid(self, gid: str) -> str:
        """
        Extract the numeric ID from a Shopify GraphQL global ID.
        
        Args:
            gid: Global ID string (e.g., 'gid://shopify/Product/12345')
            
        Returns:
            The numeric ID as a string
        """
        if gid and '/' in gid:
            return gid.split('/')[-1]
        return gid

    def _create_gid(self, resource_type: str, resource_id: str) -> str:
        """
        Create a Shopify GraphQL global ID.
        
        Args:
            resource_type: The resource type (e.g., 'Product')
            resource_id: The resource ID
            
        Returns:
            The global ID string
        """
        return f"gid://shopify/{resource_type}/{resource_id}"

    def get_product_by_id(self, product_id: int) -> Dict:
        """
        Get a product by its ID.
        
        Args:
            product_id: The ID of the product
            
        Returns:
            Product dictionary
        """
        query = """
        query GetProduct($id: ID!) {
          product(id: $id) {
            id
            title
            description
            handle
            tags
            priceRangeV2 {
              minVariantPrice {
                amount
                currencyCode
              }
              maxVariantPrice {
                amount
                currencyCode
              }
            }
            images(first: 5) {
              edges {
                node {
                  url
                  altText
                }
              }
            }
            variants(first: 20) {
              edges {
                node {
                  id
                  title
                  sku
                  price
                  inventoryQuantity
                  inventoryItem {
                    id
                    tracked
                    inventoryLevels(first: 1) {
                      edges {
                        node {
                          available
                          location {
                            name
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
            metafields(first: 20) {
              edges {
                node {
                  namespace
                  key
                  value
                }
              }
            }
            collections(first: 5) {
              edges {
                node {
                  id
                  title
                }
              }
            }
          }
        }
        """
        
        # Convert to global ID
        global_id = self._create_gid("Product", str(product_id))
        
        variables = {
            "id": global_id
        }
        
        # Estimated cost: 50 points for detailed product query
        result = self._execute_graphql_query(query, variables, 50)
        
        if 'product' in result:
            product = result['product']
            
            # Convert GraphQL IDs to regular IDs
            product['id'] = self._extract_id_from_gid(product['id'])
            
            # Convert variant IDs
            if 'variants' in product and 'edges' in product['variants']:
                for variant_edge in product['variants']['edges']:
                    variant = variant_edge['node']
                    variant['id'] = self._extract_id_from_gid(variant['id'])
                    if 'inventoryItem' in variant and variant['inventoryItem']:
                        variant['inventoryItem']['id'] = self._extract_id_from_gid(variant['inventoryItem']['id'])
            
            # Extract collections
            if 'collections' in product and 'edges' in product['collections']:
                product['collections'] = [
                    {
                        'id': self._extract_id_from_gid(edge['node']['id']),
                        'title': edge['node']['title']
                    }
                    for edge in product['collections']['edges']
                ]
            
            # Extract metafields
            if 'metafields' in product and 'edges' in product['metafields']:
                product['metafields'] = [
                    {
                        'namespace': edge['node']['namespace'],
                        'key': edge['node']['key'],
                        'value': edge['node']['value']
                    }
                    for edge in product['metafields']['edges']
                ]
            
            return product
        
        return {}

    def get_product_performance(
        self, 
        product_ids: Optional[List[int]] = None, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[ProductPerformanceMetrics]:
        """
        Get performance metrics for products.
        
        Args:
            product_ids: Optional list of product IDs to filter by
            start_date: Start date for analytics period
            end_date: End date for analytics period
            
        Returns:
            List of ProductPerformanceMetrics objects
        """
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
            
        # Format dates for Shopify API
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        # Get orders for the period
        orders_query = """
        query GetOrders($query: String!, $limit: Int!) {
          orders(query: $query, first: $limit) {
            edges {
              node {
                id
                name
                createdAt
                totalPriceSet {
                  shopMoney {
                    amount
                    currencyCode
                  }
                }
                lineItems(first: 50) {
                  edges {
                    node {
                      quantity
                      product {
                        id
                        title
                      }
                      variant {
                        id
                        sku
                        price
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """
        
        # Build query filter
        query_filter = f"created_at:>={start_date_str} created_at:<={end_date_str} status:any"
        
        variables = {
            "query": query_filter,
            "limit": 100  # Adjust based on your needs
        }
        
        # Estimated cost: 500 points for order query with line items
        orders_result = self._execute_graphql_query(orders_query, variables, 500)
        
        # Process orders to extract product performance
        product_metrics = {}
        
        # Initialize metrics for all requested products
        if product_ids:
            for product_id in product_ids:
                product = self.get_product_by_id(product_id)
                if product:
                    product_metrics[str(product_id)] = ProductPerformanceMetrics(
                        product_id=str(product_id),
                        title=product.get('title', 'Unknown')
                    )
        
        # Process orders
        if 'orders' in orders_result and 'edges' in orders_result['orders']:
            for order_edge in orders_result['orders']['edges']:
                order = order_edge['node']
                
                if 'lineItems' in order and 'edges' in order['lineItems']:
                    for line_item_edge in order['lineItems']['edges']:
                        line_item = line_item_edge['node']
                        
                        if 'product' in line_item and line_item['product']:
                            product_id = self._extract_id_from_gid(line_item['product']['id'])
                            
                            # Skip if we're filtering by product_ids and this one isn't in the list
                            if product_ids and int(product_id) not in product_ids:
                                continue
                                
                            if product_id not in product_metrics:
                                product_metrics[product_id] = ProductPerformanceMetrics(
                                    product_id=product_id,
                                    title=line_item['product']['title']
                                )
                            
                            # Update metrics
                            quantity = line_item.get('quantity', 0)
                            price = float(line_item['variant']['price']) if 'variant' in line_item and line_item['variant'] else 0
                            
                            product_metrics[product_id].units_sold += quantity
                            product_metrics[product_id].revenue += price * quantity
        
        # Get analytics data for views, add to carts, etc.
        analytics_data = self._get_analytics_data(start_date_str, end_date_str, product_ids)
        
        # Merge analytics data and calculate additional metrics
        for product_id, metrics in product_metrics.items():
            if product_id in analytics_data:
                analytics = analytics_data[product_id]
                metrics.views = analytics.get('views', 0)
                metrics.add_to_carts = analytics.get('add_to_carts', 0)
                metrics.checkout_initiations = analytics.get('checkout_initiations', 0)
                
                # Calculate conversion rate
                if metrics.views > 0:
                    metrics.conversion_rate = (metrics.units_sold / metrics.views) * 100
                
                # Calculate profit margin (if cost data is available)
                # In a real implementation, this would use cost data from metafields or another source
                metrics.profit_margin = 0.4  # Placeholder: 40% profit margin
        
        return list(product_metrics.values())

    def _get_analytics_data(
        self, 
        start_date: str, 
        end_date: str,
        product_ids: Optional[List[int]] = None
    ) -> Dict[str, Dict]:
        """
        Get analytics data from Shopify Analytics API.
        
        Args:
            start_date: Start date string (YYYY-MM-DD)
            end_date: End date string (YYYY-MM-DD)
            product_ids: Optional list of product IDs to filter by
            
        Returns:
            Dictionary mapping product IDs to analytics data
        """
        # Note: Shopify's GraphQL API doesn't provide direct access to all analytics data
        # In a real implementation, you might use the Analytics API or Reports API
        # For now, we'll simulate this with placeholder data
        
        self.logger.info(f"Getting analytics data from {start_date} to {end_date}")
        
        # Placeholder for analytics data
        analytics_data = {}
        
        # If we have product IDs, get analytics for those products
        product_ids_to_process = product_ids or []
        
        # If no specific IDs were provided, get IDs from recent products
        if not product_ids_to_process:
            products = self.get_product_list(limit=25)
            product_ids_to_process = [int(p['id']) for p in products]
        
        for product_id in product_ids_to_process:
            # In a real implementation, make API call to Shopify Analytics
            # For now, generate placeholder data
            views = 100 + (hash(str(product_id)) % 900)  # Random between 100-1000
            add_to_carts = int(views * 0.2)  # 20% of views
            checkout_initiations = int(add_to_carts * 0.5)  # 50% of add to carts
            
            analytics_data[str(product_id)] = {
                'views': views,
                'add_to_carts': add_to_carts,
                'checkout_initiations': checkout_initiations
            }
        
        return analytics_data

    def identify_underperforming_products(
        self, 
        benchmark_type: str = "category_average",
        performance_threshold: float = 0.75,
        time_period: str = "last_30_days"
    ) -> List[Dict]:
        """
        Identify underperforming products based on sales metrics.
        
        Args:
            benchmark_type: Type of benchmark to use ('category_average', 'store_average', etc.)
            performance_threshold: Threshold for determining underperformance (0.0-1.0)
            time_period: Time period for analysis ('last_30_days', 'last_90_days', etc.)
            
        Returns:
            List of underperforming products with analysis
        """
        # Convert time_period to start_date
        days = int(time_period.split('_')[1].rstrip('days'))
        start_date = datetime.now() - timedelta(days=days)
        
        # Get product performance data
        all_products = self.get_product_performance(start_date=start_date)
        
        # Group products by category if using category_average
        if benchmark_type == "category_average":
            # Get products with their categories
            products_with_categories = {}
            
            # Get categories for each product
            for product in all_products:
                product_details = self.get_product_by_id(int(product.product_id))
                category = "Uncategorized"
                
                # Get the first collection as the primary category
                if 'collections' in product_details and product_details['collections']:
                    category = product_details['collections'][0]['title']
                
                products_with_categories[product.product_id] = category
            
            # Group performance by category
            category_metrics = {}
            for product in all_products:
                product_id = product.product_id
                if product_id in products_with_categories:
                    category = products_with_categories[product_id]
                    if category not in category_metrics:
                        category_metrics[category] = {
                            'revenue': [],
                            'units_sold': [],
                            'profit_margin': [],
                            'conversion_rate': []
                        }
                    
                    category_metrics[category]['revenue'].append(product.revenue)
                    category_metrics[category]['units_sold'].append(product.units_sold)
                    category_metrics[category]['profit_margin'].append(product.profit_margin)
                    category_metrics[category]['conversion_rate'].append(product.conversion_rate)
            
            # Calculate category averages
            category_averages = {}
            for category, metrics in category_metrics.items():
                category_averages[category] = {
                    'revenue': sum(metrics['revenue']) / len(metrics['revenue']) if metrics['revenue'] else 0,
                    'units_sold': sum(metrics['units_sold']) / len(metrics['units_sold']) if metrics['units_sold'] else 0,
                    'profit_margin': sum(metrics['profit_margin']) / len(metrics['profit_margin']) if metrics['profit_margin'] else 0,
                    'conversion_rate': sum(metrics['conversion_rate']) / len(metrics['conversion_rate']) if metrics['conversion_rate'] else 0
                }
            
            # Identify underperforming products
            underperforming = []
            for product in all_products:
                product_id = product.product_id
                if product_id in products_with_categories:
                    category = products_with_categories[product_id]
                    if category in category_averages:
                        avg = category_averages[category]
                        
                        # Check if product is underperforming in multiple metrics
                        underperformance_count = 0
                        reasons = []
                        
                        if product.revenue < avg['revenue'] * performance_threshold:
                            underperformance_count += 1
                            reasons.append(f"Revenue is {product.revenue:.2f} vs category average {avg['revenue']:.2f}")
                            
                        if product.units_sold < avg['units_sold'] * performance_threshold:
                            underperformance_count += 1
                            reasons.append(f"Units sold is {product.units_sold} vs category average {avg['units_sold']:.0f}")
                            
                        if product.profit_margin < avg['profit_margin'] * performance_threshold:
                            underperformance_count += 1
                            reasons.append(f"Profit margin is {product.profit_margin:.2f}% vs category average {avg['profit_margin']:.2f}%")
                            
                        if product.conversion_rate < avg['conversion_rate'] * performance_threshold:
                            underperformance_count += 1
                            reasons.append(f"Conversion rate is {product.conversion_rate:.2f}% vs category average {avg['conversion_rate']:.2f}%")
                        
                        # If underperforming in at least 2 metrics, add to list
                        if underperformance_count >= 2:
                            underperforming.append({
                                'product_id': product.product_id,
                                'title': product.title,
                                'category': category,
                                'reasons': reasons,
                                'metrics': {
                                    'revenue': product.revenue,
                                    'units_sold': product.units_sold,
                                    'profit_margin': product.profit_margin,
                                    'conversion_rate': product.conversion_rate
                                },
                                'category_averages': avg
                            })
        
        # Use store average as benchmark
        else:
            # Calculate store averages
            store_avg = {
                'revenue': sum(p.revenue for p in all_products) / len(all_products) if all_products else 0,
                'units_sold': sum(p.units_sold for p in all_products) / len(all_products) if all_products else 0,
                'profit_margin': sum(p.profit_margin for p in all_products) / len(all_products) if all_products else 0,
                'conversion_rate': sum(p.conversion_rate for p in all_products) / len(all_products) if all_products else 0
            }
            
            # Identify underperforming products
            underperforming = []
            for product in all_products:
                # Check if product is underperforming in multiple metrics
                underperformance_count = 0
                reasons = []
                
                if product.revenue < store_avg['revenue'] * performance_threshold:
                    underperformance_count += 1
                    reasons.append(f"Revenue is {product.revenue:.2f} vs store average {store_avg['revenue']:.2f}")
                    
                if product.units_sold < store_avg['units_sold'] * performance_threshold:
                    underperformance_count += 1
                    reasons.append(f"Units sold is {product.units_sold} vs store average {store_avg['units_sold']:.0f}")
                    
                if product.profit_margin < store_avg['profit_margin'] * performance_threshold:
                    underperformance_count += 1
                    reasons.append(f"Profit margin is {product.profit_margin:.2f}% vs store average {store_avg['profit_margin']:.2f}%")
                    
                if product.conversion_rate < store_avg['conversion_rate'] * performance_threshold:
                    underperformance_count += 1
                    reasons.append(f"Conversion rate is {product.conversion_rate:.2f}% vs store average {store_avg['conversion_rate']:.2f}%")
                
                # If underperforming in at least 2 metrics, add to list
                if underperformance_count >= 2:
                    underperforming.append({
                        'product_id': product.product_id,
                        'title': product.title,
                        'reasons': reasons,
                        'metrics': {
                            'revenue': product.revenue,
                            'units_sold': product.units_sold,
                            'profit_margin': product.profit_margin,
                            'conversion_rate': product.conversion_rate
                        },
                        'store_averages': store_avg
                    })
        
        return underperforming

    # SEO Methods
    
    def get_product_seo_data(self, product_ids: Optional[List[int]] = None) -> List[SEOMetadata]:
        """
        Get SEO metadata for products.
        
        Args:
            product_ids: Optional list of product IDs to filter by
            
        Returns:
            List of SEOMetadata objects
        """
        # Get products
        products = []
        if product_ids:
            for pid in product_ids:
                product = self.get_product_by_id(pid)
                if product:
                    products.append(product)
        else:
            products = self.get_product_list(limit=50)
            
        seo_data = []
        for product in products:
            # Extract SEO metadata from metafields
            seo_title = None
            seo_description = None
            
            if 'metafields' in product:
                for metafield in product['metafields']:
                    if metafield['namespace'] == 'seo' and metafield['key'] == 'title':
                        seo_title = metafield['value']
                    elif metafield['namespace'] == 'seo' and metafield['key'] == 'description':
                        seo_description = metafield['value']
            
            # Extract tags
            tags = product.get('tags', '').split(', ') if isinstance(product.get('tags'), str) else []
            
            # Calculate keyword density if description exists
            keyword_density = None
            if 'description' in product and product['description']:
                keyword_density = self._calculate_keyword_density(product['description'])
                
            # Calculate SEO score
            seo_score = self._calculate_seo_score(product)
            
            seo_data.append(SEOMetadata(
                product_id=str(product['id']),
                title=product.get('title', ''),
                description=product.get('description', ''),
                url=f"https://{self.shop_url}/products/{product.get('handle')}",
                handle=product.get('handle', ''),
                tags=tags,
                seo_title=seo_title or product.get('title', ''),
                seo_description=seo_description,
                keyword_density=keyword_density,
                seo_score=seo_score
            ))
            
        return seo_data

    def _calculate_keyword_density(self, content: str) -> float:
        """
        Calculate keyword density in content.
        
        Args:
            content: Content to analyze
            
        Returns:
            Keyword density as a percentage
        """
        # In a real implementation, this would use NLP to extract keywords and calculate density
        # For now, return a placeholder value
        return 2.0

    def _calculate_seo_score(self, product: Dict) -> float:
        """
        Calculate an SEO score for a product.
        
        Args:
            product: Product dictionary
            
        Returns:
            SEO score from 0-100
        """
        score = 0
        max_score = 100
        
        # Check title length (ideal: 50-60 characters)
        title = product.get('title', '')
        if len(title) >= 50 and len(title) <= 60:
            score += 20
        elif len(title) >= 40 and len(title) <= 70:
            score += 15
        elif len(title) > 0:
            score += 5
            
        # Check description length (ideal: at least 300 characters)
        description = product.get('description', '')
        if len(description) >= 300:
            score += 20
        elif len(description) >= 150:
            score += 10
        elif len(description) > 0:
            score += 5
            
        # Check if SEO title and description are set in metafields
        has_seo_title = False
        has_seo_description = False
        
        if 'metafields' in product:
            for metafield in product['metafields']:
                if metafield['namespace'] == 'seo' and metafield['key'] == 'title':
                    has_seo_title = True
                elif metafield['namespace'] == 'seo' and metafield['key'] == 'description':
                    has_seo_description = True
        
        if has_seo_title:
            score += 15
        if has_seo_description:
            score += 15
            
        # Check if product has tags
        if product.get('tags'):
            score += 10
            
        # Check if product has images with alt text
        if 'images' in product and 'edges' in product['images']:
            has_alt = any(edge['node'].get('altText') for edge in product['images']['edges'])
            if has_alt:
                score += 10
                
        # Check URL/handle (ideal: contains keywords, no numbers)
        handle = product.get('handle', '')
        if handle and not any(c.isdigit() for c in handle):
            score += 10
            
        return min(score, max_score)

    def update_product_seo(
        self, 
        product_id: int, 
        seo_title: Optional[str] = None,
        seo_description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        handle: Optional[str] = None
    ) -> bool:
        """
        Update SEO metadata for a product.
        
        Args:
            product_id: The ID of the product
            seo_title: New SEO title
            seo_description: New SEO description
            tags: New tags list
            handle: New product handle (URL slug)
            
        Returns:
            True if update was successful, False otherwise
        """
        # Convert to global ID
        global_id = self._create_gid("Product", str(product_id))
        
        try:
            # Update product fields with GraphQL mutation
            update_fields = {}
            input_fields = {}
            
            if handle is not None:
                input_fields["handle"] = handle
                
            if tags is not None:
                input_fields["tags"] = tags
            
            # Only include fields that are being updated
            if input_fields:
                update_fields["input"] = input_fields
                
                # Execute product update mutation
                product_update_mutation = """
                mutation UpdateProduct($input: ProductInput!) {
                  productUpdate(input: $input) {
                    product {
                      id
                    }
                    userErrors {
                      field
                      message
                    }
                  }
                }
                """
                
                variables = {
                    "input": {
                        "id": global_id,
                        **input_fields
                    }
                }
                
                result = self._execute_graphql_query(product_update_mutation, variables, 50)
                
                if 'productUpdate' in result:
                    if result['productUpdate'].get('userErrors'):
                        errors = result['productUpdate']['userErrors']
                        self.logger.error(f"Error updating product: {errors}")
                        return False
            
            # Update metafields if needed
            if seo_title is not None or seo_description is not None:
                metafields_to_update = []
                
                if seo_title is not None:
                    metafields_to_update.append({
                        "ownerId": global_id,
                        "namespace": "seo",
                        "key": "title",
                        "value": seo_title,
                        "type": "single_line_text_field"
                    })
                
                if seo_description is not None:
                    metafields_to_update.append({
                        "ownerId": global_id,
                        "namespace": "seo",
                        "key": "description",
                        "value": seo_description,
                        "type": "single_line_text_field"
                    })
                
                # Update metafields one by one
                for metafield_input in metafields_to_update:
                    metafield_mutation = """
                    mutation UpdateMetafield($input: MetafieldsSetInput!) {
                      metafieldsSet(metafields: $input) {
                        metafields {
                          id
                          namespace
                          key
                        }
                        userErrors {
                          field
                          message
                        }
                      }
                    }
                    """
                    
                    variables = {
                        "input": metafield_input
                    }
                    
                    result = self._execute_graphql_query(metafield_mutation, variables, 10)
                    
                    if 'metafieldsSet' in result and result['metafieldsSet'].get('userErrors'):
                        errors = result['metafieldsSet']['userErrors']
                        self.logger.error(f"Error updating metafield: {errors}")
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating product SEO: {e}")
            return False

    # Inventory Management Methods
    
    def get_inventory_status(self, product_ids: Optional[List[int]] = None) -> List[InventoryStatus]:
        """
        Get inventory status for products.
        
        Args:
            product_ids: Optional list of product IDs to filter by
            
        Returns:
            List of InventoryStatus objects
        """
        # Get products
        products = []
        if product_ids:
            for pid in product_ids:
                product = self.get_product_by_id(pid)
                if product:
                    products.append(product)
        else:
            products = self.get_product_list(limit=50)
            
        inventory_status = []
        
        for product in products:
            product_id = str(product['id'])
            
            # Get inventory levels for each variant
            if 'variants' in product and 'edges' in product['variants']:
                for variant_edge in product['variants']['edges']:
                    variant = variant_edge['node']
                    variant_id = str(variant['id'])
                    
                    # Get inventory data
                    available = variant.get('inventoryQuantity', 0)
                    
                    # Get inventory item data
                    inventory_item = variant.get('inventoryItem', {})
                    tracked = inventory_item.get('tracked', False)
                    
                    # Get inventory levels
                    inventory_levels = []
                    if 'inventoryLevels' in inventory_item and 'edges' in inventory_item['inventoryLevels']:
                        inventory_levels = [edge['node'] for edge in inventory_item['inventoryLevels']['edges']]
                    
                    # Get reorder point (not directly available in GraphQL API)
                    # In a real implementation, this might be stored in a metafield
                    reorder_point = None
                    
                    # Calculate if low stock
                    is_low_stock = False
                    if reorder_point is not None:
                        is_low_stock = available <= reorder_point
                    else:
                        # Default logic: low stock if less than 20% of typical stock or less than 5 units
                        is_low_stock = available <= 5
                    
                    # Calculate days until stockout based on sales velocity
                    days_until_stockout = self._calculate_days_until_stockout(product_id, variant_id, available)
                    
                    inventory_status.append(InventoryStatus(
                        product_id=product_id,
                        variant_id=variant_id,
                        sku=variant.get('sku', ''),
                        title=f"{product.get('title')} - {variant.get('title')}",
                        quantity=available,
                        available=available,
                        committed=0,  # Not directly available in GraphQL API
                        reorder_point=reorder_point,
                        is_low_stock=is_low_stock,
                        days_until_stockout=days_until_stockout
                    ))
        
        return inventory_status

    def _calculate_days_until_stockout(
        self, 
        product_id: str, 
        variant_id: str, 
        available: int
    ) -> Optional[int]:
        """
        Calculate estimated days until stockout based on sales velocity.
        
        Args:
            product_id: The ID of the product
            variant_id: The ID of the variant
            available: Available inventory
            
        Returns:
            Estimated days until stockout, or None if cannot be calculated
        """
        # Get sales velocity (units sold per day) for the last 30 days
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        # Format dates for Shopify API
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        # Build query filter for this specific variant
        query_filter = f"created_at:>={start_date_str} created_at:<={end_date_str} status:any"
        
        # Get orders for the period
        orders_query = """
        query GetOrders($query: String!, $limit: Int!) {
          orders(query: $query, first: $limit) {
            edges {
              node {
                lineItems(first: 50) {
                  edges {
                    node {
                      quantity
                      variant {
                        id
                      }
                      product {
                        id
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """
        
        variables = {
            "query": query_filter,
            "limit": 100
        }
        
        # Estimated cost: 200 points
        orders_result = self._execute_graphql_query(orders_query, variables, 200)
        
        # Count units sold for this variant
        units_sold = 0
        
        if 'orders' in orders_result and 'edges' in orders_result['orders']:
            for order_edge in orders_result['orders']['edges']:
                order = order_edge['node']
                
                if 'lineItems' in order and 'edges' in order['lineItems']:
                    for line_item_edge in order['lineItems']['edges']:
                        line_item = line_item_edge['node']
                        
                        if ('product' in line_item and line_item['product'] and 
                            'variant' in line_item and line_item['variant']):
                            
                            line_product_id = self._extract_id_from_gid(line_item['product']['id'])
                            line_variant_id = self._extract_id_from_gid(line_item['variant']['id'])
                            
                            if line_product_id == product_id and line_variant_id == variant_id:
                                units_sold += line_item.get('quantity', 0)
        
        # Calculate daily sales velocity
        days = 30
        daily_velocity = units_sold / days if units_sold > 0 else 0
        
        # Calculate days until stockout
        if daily_velocity > 0:
            return int(available / daily_velocity)
        else:
            return None

    def generate_restock_recommendations(
        self, 
        consider_lead_time: bool = True,
        optimize_for: str = "minimal_stockouts"
    ) -> List[Dict]:
        """
        Generate restock recommendations based on inventory status and sales velocity.
        
        Args:
            consider_lead_time: Whether to consider supplier lead time
            optimize_for: Optimization strategy ('minimal_stockouts', 'minimal_inventory_cost')
            
        Returns:
            List of restock recommendations
        """
        # Get inventory status
        inventory = self.get_inventory_status()
        
        # Filter for items that need restocking
        restock_candidates = []
        for item in inventory:
            if item.is_low_stock or (item.days_until_stockout is not None and item.days_until_stockout <= 14):
                restock_candidates.append(item)
        
        # Get supplier lead times (in a real implementation, this would come from a database or metafields)
        lead_times = self._get_supplier_lead_times()
        
        # Generate recommendations
        recommendations = []
        for item in restock_candidates:
            # Get product details
            product = self.get_product_by_id(int(item.product_id))
            
            # Find the variant
            variant = None
            if 'variants' in product and 'edges' in product['variants']:
                for variant_edge in product['variants']['edges']:
                    if self._extract_id_from_gid(variant_edge['node']['id']) == item.variant_id:
                        variant = variant_edge['node']
                        break
            
            if variant:
                # Calculate reorder quantity
                reorder_quantity = self._calculate_reorder_quantity(
                    item, 
                    consider_lead_time=consider_lead_time,
                    lead_times=lead_times,
                    optimize_for=optimize_for
                )
                
                # Calculate priority
                if item.available <= 0:
                    priority = "critical"
                elif item.is_low_stock:
                    priority = "high"
                elif item.days_until_stockout and item.days_until_stockout <= 7:
                    priority = "medium"
                else:
                    priority = "low"
                
                # Get supplier (in a real implementation, this would come from metafields or a database)
                supplier = self._get_supplier_for_product(item.product_id)
                
                # Calculate cost
                cost_per_unit = float(variant.get('price', 0)) * 0.6  # Estimate: cost is 60% of price
                total_cost = cost_per_unit * reorder_quantity
                
                recommendations.append({
                    'product_id': item.product_id,
                    'variant_id': item.variant_id,
                    'sku': item.sku,
                    'title': item.title,
                    'current_stock': item.available,
                    'reorder_quantity': reorder_quantity,
                    'priority': priority,
                    'supplier': supplier,
                    'lead_time_days': lead_times.get(supplier, 14),
                    'cost_per_unit': cost_per_unit,
                    'total_cost': total_cost,
                    'days_until_stockout': item.days_until_stockout
                })
        
        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 4))
        
        return recommendations

    def _get_supplier_lead_times(self) -> Dict[str, int]:
        """
        Get supplier lead times in days.
        
        Returns:
            Dictionary mapping supplier names to lead times in days
        """
        # In a real implementation, this would come from a database or Shopify metafields
        # For now, return placeholder data
        return {
            "Supplier A": 7,
            "Supplier B": 14,
            "Supplier C": 21,
            "Default Supplier": 14
        }

    def _get_supplier_for_product(self, product_id: str) -> str:
        """
        Get the supplier for a product.
        
        Args:
            product_id: The ID of the product
            
        Returns:
            Supplier name
        """
        # In a real implementation, this would come from product metafields or a database
        # For now, return a placeholder based on product ID
        suppliers = ["Supplier A", "Supplier B", "Supplier C"]
        index = hash(product_id) % len(suppliers)
        return suppliers[index]

    def _calculate_reorder_quantity(
        self, 
        item: InventoryStatus,
        consider_lead_time: bool = True,
        lead_times: Dict[str, int] = None,
        optimize_for: str = "minimal_stockouts"
    ) -> int:
        """
        Calculate recommended reorder quantity.
        
        Args:
            item: Inventory status item
            consider_lead_time: Whether to consider supplier lead time
            lead_times: Dictionary of supplier lead times
            optimize_for: Optimization strategy
            
        Returns:
            Recommended reorder quantity
        """
        # Get daily sales velocity
        daily_velocity = 0
        if item.days_until_stockout is not None and item.available > 0:
            daily_velocity = item.available / item.days_until_stockout
        
        # Default to 1 unit per day if no velocity data
        if daily_velocity <= 0:
            daily_velocity = 1
        
        # Calculate base reorder quantity (30 days of stock)
        base_quantity = int(daily_velocity * 30)
        
        # Adjust for lead time if requested
        if consider_lead_time and lead_times:
            supplier = self._get_supplier_for_product(item.product_id)
            lead_time = lead_times.get(supplier, 14)
            
            # Add lead time buffer
            base_quantity += int(daily_velocity * lead_time)
        
        # Adjust based on optimization strategy
        if optimize_for == "minimal_stockouts":
            # Add safety stock (15 days)
            safety_stock = int(daily_velocity * 15)
            final_quantity = base_quantity + safety_stock
        elif optimize_for == "minimal_inventory_cost":
            # Reduce to economic order quantity
            # In a real implementation, this would use the EOQ formula
            final_quantity = base_quantity
        else:
            final_quantity = base_quantity
        
        # Ensure minimum order quantity
        return max(final_quantity, 5)  # Minimum 5 units
