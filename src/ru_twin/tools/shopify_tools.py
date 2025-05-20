"""
Shopify Tools for RuTwin Crew

This module provides tools for interacting with Shopify to perform
product analytics, SEO optimization, and inventory management tasks.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any

import pandas as pd
from pydantic import BaseModel, Field

from ru_twin.mcp.client.shopify_client import ShopifyClient, ProductPerformanceMetrics, SEOMetadata, InventoryStatus
from ru_twin.tools.tool_registry import ToolRegistry


# --- Product Analytics Models ---

class ProductAnalyticsInput(BaseModel):
    """Input for product analytics tools"""
    time_period: str = Field(
        default="last_30_days", 
        description="Time period for analysis (e.g., 'last_30_days', 'last_90_days')"
    )
    metrics: List[str] = Field(
        default=["revenue", "units_sold", "profit_margin", "conversion_rate"],
        description="Metrics to analyze"
    )
    product_ids: Optional[List[str]] = Field(
        default=None, 
        description="Optional list of product IDs to analyze. If not provided, all products will be analyzed."
    )


class PerformanceGapInput(BaseModel):
    """Input for identifying performance gaps"""
    benchmark_type: str = Field(
        default="category_average", 
        description="Type of benchmark to use ('category_average', 'store_average')"
    )
    performance_threshold: float = Field(
        default=0.75, 
        description="Threshold for determining underperformance (0.0-1.0)"
    )
    time_period: str = Field(
        default="last_30_days", 
        description="Time period for analysis"
    )


class CustomerInteractionInput(BaseModel):
    """Input for customer interaction analysis"""
    track_events: List[str] = Field(
        default=["product_view", "add_to_cart", "checkout_initiation", "purchase_completion"],
        description="Events to track in the customer journey"
    )
    time_period: str = Field(
        default="last_30_days", 
        description="Time period for analysis"
    )


class DashboardInput(BaseModel):
    """Input for generating dashboards"""
    dashboard_format: str = Field(
        default="interactive", 
        description="Format of the dashboard ('interactive', 'static')"
    )
    refresh_frequency: str = Field(
        default="weekly", 
        description="How often the dashboard should refresh"
    )
    include_metrics: List[str] = Field(
        default=["revenue", "units_sold", "profit_margin", "conversion_rate"],
        description="Metrics to include in the dashboard"
    )


# --- SEO Models ---

class SEOAuditInput(BaseModel):
    """Input for SEO audit tools"""
    audit_factors: List[str] = Field(
        default=[
            "title_optimization", 
            "description_quality", 
            "keyword_usage", 
            "image_alt_text", 
            "metadata_completeness"
        ],
        description="Factors to audit for SEO"
    )
    product_ids: Optional[List[str]] = Field(
        default=None, 
        description="Optional list of product IDs to audit. If not provided, all products will be audited."
    )


class ContentGenerationInput(BaseModel):
    """Input for content generation tools"""
    target_word_count: int = Field(
        default=150, 
        description="Target word count for generated content"
    )
    keyword_density: float = Field(
        default=2.0, 
        description="Target keyword density percentage"
    )
    tone: str = Field(
        default="professional", 
        description="Tone of the content ('professional', 'casual', 'enthusiastic')"
    )
    product_ids: List[str] = Field(
        description="List of product IDs to generate content for"
    )


class KeywordAnalysisInput(BaseModel):
    """Input for keyword analysis tools"""
    tracking_frequency: str = Field(
        default="weekly", 
        description="How often to track keywords"
    )
    competitor_comparison: bool = Field(
        default=True, 
        description="Whether to compare with competitors"
    )
    keywords: Optional[List[str]] = Field(
        default=None, 
        description="Optional list of specific keywords to analyze. If not provided, will use product-related keywords."
    )


class SearchRankingInput(BaseModel):
    """Input for search ranking improvement tools"""
    target_improvement: str = Field(
        default="10%", 
        description="Target percentage improvement in rankings"
    )
    focus_areas: List[str] = Field(
        default=["on_site_search", "google_shopping", "organic_search"],
        description="Areas to focus on for ranking improvement"
    )
    product_ids: Optional[List[str]] = Field(
        default=None, 
        description="Optional list of product IDs to improve. If not provided, will focus on underperforming products."
    )


# --- Inventory Management Models ---

class InventoryMonitorInput(BaseModel):
    """Input for inventory monitoring tools"""
    check_frequency: str = Field(
        default="daily", 
        description="How often to check inventory levels"
    )
    low_stock_threshold: float = Field(
        default=0.2, 
        description="Threshold for determining low stock (0.0-1.0)"
    )
    product_ids: Optional[List[str]] = Field(
        default=None, 
        description="Optional list of product IDs to monitor. If not provided, all products will be monitored."
    )


class InventoryForecastInput(BaseModel):
    """Input for inventory forecasting tools"""
    forecast_horizon: str = Field(
        default="90_days", 
        description="Time horizon for forecast"
    )
    confidence_interval: float = Field(
        default=0.9, 
        description="Confidence interval for forecast (0.0-1.0)"
    )
    include_seasonality: bool = Field(
        default=True, 
        description="Whether to include seasonality in forecast"
    )
    product_ids: Optional[List[str]] = Field(
        default=None, 
        description="Optional list of product IDs to forecast. If not provided, all products will be forecasted."
    )


class RestockRecommendationInput(BaseModel):
    """Input for restock recommendation tools"""
    consider_lead_time: bool = Field(
        default=True, 
        description="Whether to consider supplier lead time"
    )
    optimize_for: str = Field(
        default="minimal_stockouts", 
        description="Optimization strategy ('minimal_stockouts', 'minimal_inventory_cost')"
    )
    include_cost_analysis: bool = Field(
        default=True, 
        description="Whether to include cost analysis in recommendations"
    )


class InventoryTurnoverInput(BaseModel):
    """Input for inventory turnover analysis tools"""
    analysis_period: str = Field(
        default="quarterly", 
        description="Period for turnover analysis"
    )
    categorize_by: List[str] = Field(
        default=["product_category", "price_point", "supplier"],
        description="Categories to break down analysis by"
    )


# --- Tool Functions ---

# Product Analytics Tools

def analyze_product_sales(
    client: ShopifyClient,
    input_data: ProductAnalyticsInput
) -> Dict:
    """
    Analyze sales data for products to identify trends, seasonality, and performance metrics.
    
    Args:
        client: ShopifyClient instance
        input_data: Configuration for the analysis
        
    Returns:
        Dictionary with analysis results
    """
    logging.info(f"Analyzing product sales for period: {input_data.time_period}")
    
    # Parse time period
    days = int(input_data.time_period.split('_')[1].rstrip('days'))
    start_date = datetime.now() - timedelta(days=days)
    
    # Convert product_ids to integers if provided
    product_ids = None
    if input_data.product_ids:
        product_ids = [int(pid) for pid in input_data.product_ids]
    
    # Get product performance data
    performance_data = client.get_product_performance(
        product_ids=product_ids,
        start_date=start_date
    )
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame([p.dict() for p in performance_data])
    
    # Calculate overall metrics
    overall_metrics = {
        'total_revenue': df['revenue'].sum(),
        'total_units_sold': df['units_sold'].sum(),
        'average_profit_margin': df['profit_margin'].mean(),
        'average_conversion_rate': df['conversion_rate'].mean()
    }
    
    # Identify top performing products
    top_revenue_products = df.nlargest(5, 'revenue')[['product_id', 'title', 'revenue']].to_dict('records')
    top_units_products = df.nlargest(5, 'units_sold')[['product_id', 'title', 'units_sold']].to_dict('records')
    top_margin_products = df.nlargest(5, 'profit_margin')[['product_id', 'title', 'profit_margin']].to_dict('records')
    top_conversion_products = df.nlargest(5, 'conversion_rate')[['product_id', 'title', 'conversion_rate']].to_dict('records')
    
    # TODO: In a real implementation, we would analyze trends over time
    # For now, we'll return the current snapshot
    
    return {
        'time_period': input_data.time_period,
        'overall_metrics': overall_metrics,
        'top_performers': {
            'by_revenue': top_revenue_products,
            'by_units_sold': top_units_products,
            'by_profit_margin': top_margin_products,
            'by_conversion_rate': top_conversion_products
        },
        'raw_data': [p.dict() for p in performance_data]
    }


def identify_product_performance_gaps(
    client: ShopifyClient,
    input_data: PerformanceGapInput
) -> Dict:
    """
    Identify underperforming products based on comparison to benchmarks.
    
    Args:
        client: ShopifyClient instance
        input_data: Configuration for the gap analysis
        
    Returns:
        Dictionary with underperforming products and analysis
    """
    logging.info(f"Identifying performance gaps using {input_data.benchmark_type} benchmark")
    
    # Get underperforming products
    underperforming = client.identify_underperforming_products(
        benchmark_type=input_data.benchmark_type,
        performance_threshold=input_data.performance_threshold,
        time_period=input_data.time_period
    )
    
    # Group by reason
    reasons_summary = {}
    for product in underperforming:
        for reason in product.get('reasons', []):
            reason_key = reason.split(' vs ')[0]
            if reason_key not in reasons_summary:
                reasons_summary[reason_key] = 0
            reasons_summary[reason_key] += 1
    
    # Calculate summary statistics
    summary = {
        'total_underperforming': len(underperforming),
        'percentage_of_catalog': f"{len(underperforming) / 100:.1f}%",  # Placeholder, would need total count
        'common_issues': reasons_summary,
        'benchmark_type': input_data.benchmark_type,
        'performance_threshold': input_data.performance_threshold
    }
    
    return {
        'summary': summary,
        'underperforming_products': underperforming
    }


def analyze_customer_product_interactions(
    client: ShopifyClient,
    input_data: CustomerInteractionInput
) -> Dict:
    """
    Analyze how customers interact with products including views, add-to-carts, and purchase completion rates.
    
    Args:
        client: ShopifyClient instance
        input_data: Configuration for the interaction analysis
        
    Returns:
        Dictionary with customer journey analysis
    """
    logging.info(f"Analyzing customer product interactions for events: {input_data.track_events}")
    
    # Parse time period
    days = int(input_data.time_period.split('_')[1].rstrip('days'))
    start_date = datetime.now() - timedelta(days=days)
    
    # Get product performance data which includes interaction metrics
    performance_data = client.get_product_performance(start_date=start_date)
    
    # Extract interaction data
    interactions = []
    for product in performance_data:
        interaction = {
            'product_id': product.product_id,
            'title': product.title,
            'funnel': {
                'views': product.views,
                'add_to_carts': product.add_to_carts,
                'checkout_initiations': product.checkout_initiations,
                'purchases': product.units_sold
            },
            'conversion_rates': {
                'view_to_cart': (product.add_to_carts / product.views * 100) if product.views > 0 else 0,
                'cart_to_checkout': (product.checkout_initiations / product.add_to_carts * 100) if product.add_to_carts > 0 else 0,
                'checkout_to_purchase': (product.units_sold / product.checkout_initiations * 100) if product.checkout_initiations > 0 else 0,
                'overall': product.conversion_rate
            }
        }
        interactions.append(interaction)
    
    # Calculate average funnel metrics
    avg_funnel = {
        'views': sum(p.views for p in performance_data) / len(performance_data) if performance_data else 0,
        'add_to_carts': sum(p.add_to_carts for p in performance_data) / len(performance_data) if performance_data else 0,
        'checkout_initiations': sum(p.checkout_initiations for p in performance_data) / len(performance_data) if performance_data else 0,
        'purchases': sum(p.units_sold for p in performance_data) / len(performance_data) if performance_data else 0
    }
    
    # Calculate average conversion rates
    avg_conversion = {
        'view_to_cart': sum(i['conversion_rates']['view_to_cart'] for i in interactions) / len(interactions) if interactions else 0,
        'cart_to_checkout': sum(i['conversion_rates']['cart_to_checkout'] for i in interactions) / len(interactions) if interactions else 0,
        'checkout_to_purchase': sum(i['conversion_rates']['checkout_to_purchase'] for i in interactions) / len(interactions) if interactions else 0,
        'overall': sum(i['conversion_rates']['overall'] for i in interactions) / len(interactions) if interactions else 0
    }
    
    # Identify drop-off points
    drop_off_analysis = {
        'view_to_cart_drop_off': 100 - avg_conversion['view_to_cart'],
        'cart_to_checkout_drop_off': 100 - avg_conversion['cart_to_checkout'],
        'checkout_to_purchase_drop_off': 100 - avg_conversion['checkout_to_purchase']
    }
    
    # Find biggest drop-off point
    biggest_drop_off = max(drop_off_analysis.items(), key=lambda x: x[1])
    
    return {
        'time_period': input_data.time_period,
        'product_interactions': interactions,
        'average_funnel': avg_funnel,
        'average_conversion_rates': avg_conversion,
        'drop_off_analysis': drop_off_analysis,
        'biggest_drop_off_point': biggest_drop_off[0],
        'recommendations': [
            f"Focus on improving {biggest_drop_off[0].replace('_', ' ')} conversion",
            "Consider A/B testing product descriptions and images",
            "Review checkout process for friction points"
        ]
    }


def generate_product_performance_dashboard(
    client: ShopifyClient,
    input_data: DashboardInput,
    sales_data: Dict = None,
    gap_analysis: Dict = None,
    interaction_data: Dict = None
) -> Dict:
    """
    Generate a dashboard summarizing key product performance metrics.
    
    Args:
        client: ShopifyClient instance
        input_data: Configuration for the dashboard
        sales_data: Optional pre-generated sales analysis data
        gap_analysis: Optional pre-generated gap analysis data
        interaction_data: Optional pre-generated interaction data
        
    Returns:
        Dictionary with dashboard data and visualization instructions
    """
    logging.info(f"Generating product performance dashboard in {input_data.dashboard_format} format")
    
    # If data wasn't provided, generate it
    if not sales_data:
        sales_data = analyze_product_sales(
            client, 
            ProductAnalyticsInput(
                metrics=input_data.include_metrics
            )
        )
    
    if not gap_analysis:
        gap_analysis = identify_product_performance_gaps(
            client,
            PerformanceGapInput()
        )
    
    if not interaction_data:
        interaction_data = analyze_customer_product_interactions(
            client,
            CustomerInteractionInput()
        )
    
    # Compile dashboard data
    dashboard = {
        'title': 'Product Performance Dashboard',
        'refresh_frequency': input_data.refresh_frequency,
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'format': input_data.dashboard_format,
        'sections': [
            {
                'title': 'Overall Performance',
                'type': 'metrics',
                'data': sales_data['overall_metrics']
            },
            {
                'title': 'Top Performing Products',
                'type': 'table',
                'data': sales_data['top_performers']
            },
            {
                'title': 'Underperforming Products',
                'type': 'table',
                'data': {
                    'products': gap_analysis['underperforming_products'][:5],
                    'summary': gap_analysis['summary']
                }
            },
            {
                'title': 'Customer Journey',
                'type': 'funnel',
                'data': {
                    'funnel': interaction_data['average_funnel'],
                    'conversion_rates': interaction_data['average_conversion_rates']
                }
            }
        ],
        'recommendations': [
            *interaction_data.get('recommendations', []),
            f"Address {gap_analysis['summary']['total_underperforming']} underperforming products"
        ]
    }
    
    return dashboard


# SEO Tools

def audit_product_listings_for_seo(
    client: ShopifyClient,
    input_data: SEOAuditInput
) -> Dict:
    """
    Audit product listings for SEO best practices.
    
    Args:
        client: ShopifyClient instance
        input_data: Configuration for the SEO audit
        
    Returns:
        Dictionary with SEO audit results
    """
    logging.info(f"Auditing product listings for SEO factors: {input_data.audit_factors}")
    
    # Convert product_ids to integers if provided
    product_ids = None
    if input_data.product_ids:
        product_ids = [int(pid) for pid in input_data.product_ids]
    
    # Get SEO data for products
    seo_data = client.get_product_seo_data(product_ids=product_ids)
    
    # Perform audit based on factors
    audit_results = []
    
    for product in seo_data:
        audit_item = {
            'product_id': product.product_id,
            'title': product.title,
            'url': product.url,
            'seo_score': product.seo_score,
            'audit_details': {}
        }
        
        # Check title optimization
        if 'title_optimization' in input_data.audit_factors:
            title_length = len(product.title)
            title_score = 100
            title_feedback = []
            
            if title_length < 20:
                title_score -= 50
                title_feedback.append("Title is too short (under 20 characters)")
            elif title_length < 40:
                title_score -= 25
                title_feedback.append("Title is shorter than recommended (40-60 characters)")
            elif title_length > 60:
                title_score -= 25
                title_feedback.append("Title is longer than recommended (over 60 characters)")
                
            audit_item['audit_details']['title_optimization'] = {
                'score': title_score,
                'feedback': title_feedback
            }
        
        # Check description quality
        if 'description_quality' in input_data.audit_factors:
            desc_length = len(product.description)
            desc_score = 100
            desc_feedback = []
            
            if desc_length < 50:
                desc_score -= 75
                desc_feedback.append("Description is too short (under 50 characters)")
            elif desc_length < 150:
                desc_score -= 50
                desc_feedback.append("Description is shorter than recommended (under 150 characters)")
            elif desc_length < 300:
                desc_score -= 25
                desc_feedback.append("Description could be more detailed (recommended 300+ characters)")
                
            audit_item['audit_details']['description_quality'] = {
                'score': desc_score,
                'feedback': desc_feedback
            }
        
        # Check keyword usage
        if 'keyword_usage' in input_data.audit_factors:
            keyword_score = 100
            keyword_feedback = []
            
            if product.keyword_density is None:
                keyword_score -= 50
                keyword_feedback.append("Unable to analyze keyword density")
            elif product.keyword_density < 0.5:
                keyword_score -= 50
                keyword_feedback.append("Keyword density is too low (under 0.5%)")
            elif product.keyword_density > 5.0:
                keyword_score -= 25
                keyword_feedback.append("Keyword density may be too high (over 5%)")
                
            if not product.tags or len(product.tags) < 3:
                keyword_score -= 25
                keyword_feedback.append("Not enough tags (recommended 3+ tags)")
                
            audit_item['audit_details']['keyword_usage'] = {
                'score': keyword_score,
                'feedback': keyword_feedback,
                'density': product.keyword_density,
                'tags': product.tags
            }
        
        # Calculate overall score (average of factor scores)
        factor_scores = [details['score'] for details in audit_item['audit_details'].values()]
        overall_score = sum(factor_scores) / len(factor_scores) if factor_scores else 0
        audit_item['overall_score'] = overall_score
        
        # Generate recommendations
        recommendations = []
        for factor, details in audit_item['audit_details'].items():
            if details['score'] < 70:
                for feedback in details['feedback']:
                    recommendations.append(f"[{factor}] {feedback}")
        
        audit_item['recommendations'] = recommendations
        audit_results.append(audit_item)
    
    # Calculate summary statistics
    avg_score = sum(item['overall_score'] for item in audit_results) / len(audit_results) if audit_results else 0
    score_distribution = {
        'excellent': len([i for i in audit_results if i['overall_score'] >= 90]),
        'good': len([i for i in audit_results if 70 <= i['overall_score'] < 90]),
        'needs_improvement': len([i for i in audit_results if 50 <= i['overall_score'] < 70]),
        'poor': len([i for i in audit_results if i['overall_score'] < 50])
    }
    
    return {
        'summary': {
            'average_score': avg_score,
            'score_distribution': score_distribution,
            'products_audited': len(audit_results),
            'factors_analyzed': input_data.audit_factors
        },
        'audit_results': audit_results
    }


def generate_seo_product_descriptions(
    client: ShopifyClient,
    input_data: ContentGenerationInput
) -> Dict:
    """
    Generate SEO-optimized product descriptions.
    
    Args:
        client: ShopifyClient instance
        input_data: Configuration for content generation
        
    Returns:
        Dictionary with generated descriptions
    """
    logging.info(f"Generating SEO-optimized descriptions for {len(input_data.product_ids)} products")
    
    # Convert product_ids to integers
    product_ids = [int(pid) for pid in input_data.product_ids]
    
    # Get current product data
    products = []
    for pid in product_ids:
        product = client.get_product_by_id(pid)
        if product:  # Check if product was found
            products.append(product)
    
    # Get SEO data to identify optimization opportunities
    seo_data = client.get_product_seo_data(product_ids=product_ids)
    seo_by_id = {item.product_id: item for item in seo_data}
    
    # Generate optimized descriptions
    optimized_descriptions = []
    
    for product in products:
        product_id = str(product.get('id'))
        title = product.get('title', '')
        current_description = product.get('description', '')
        
        # Get tags - in GraphQL they might be a string or a list
        tags = []
        if 'tags' in product:
            if isinstance(product['tags'], str):
                tags = product['tags'].split(', ') if product['tags'] else []
            elif isinstance(product['tags'], list):
                tags = product['tags']
        
        # Get SEO data if available
        seo_info = seo_by_id.get(product_id)
        
        # In a real implementation, this would use an LLM to generate the description
        # For now, we'll create a placeholder description
        
        # Extract key features from current description (placeholder logic)
        key_features = ["Feature 1", "Feature 2", "Feature 3"]
        
        # Generate description template based on tone
        if input_data.tone == "professional":
            template = f"Discover the exceptional {title}. This premium product offers {key_features[0]}, {key_features[1]}, and {key_features[2]}. Designed with quality and performance in mind, it's the perfect solution for your needs."
        elif input_data.tone == "casual":
            template = f"Check out our amazing {title}! You'll love the {key_features[0]}, {key_features[1]}, and {key_features[2]}. It's super easy to use and perfect for everyday needs."
        else:  # enthusiastic
            template = f"WOW! Our incredible {title} is a game-changer! With amazing {key_features[0]}, spectacular {key_features[1]}, and unbelievable {key_features[2]}, you'll be absolutely thrilled with this purchase!"
        
        # Add keywords from tags
        if tags:
            keywords = ", ".join(tags[:3])
            template += f" Perfect for {keywords}."
        
        # Add call to action
        template += " Order now and experience the difference!"
        
        optimized_descriptions.append({
            'product_id': product_id,
            'title': title,
            'current_description': current_description,
            'optimized_description': template,
            'target_keywords': tags[:5] if tags else [],
            'word_count': len(template.split()),
            'estimated_keyword_density': input_data.keyword_density  # Placeholder
        })
    
    return {
        'optimized_descriptions': optimized_descriptions,
        'generation_parameters': {
            'target_word_count': input_data.target_word_count,
            'keyword_density': input_data.keyword_density,
            'tone': input_data.tone
        }
    }


def analyze_keyword_performance(
    client: ShopifyClient,
    input_data: KeywordAnalysisInput
) -> Dict:
    """
    Analyze keyword rankings and performance for product pages.
    
    Args:
        client: ShopifyClient instance
        input_data: Configuration for keyword analysis
        
    Returns:
        Dictionary with keyword performance analysis
    """
    logging.info(f"Analyzing keyword performance with tracking frequency: {input_data.tracking_frequency}")
    
    # In a real implementation, this would connect to Google Search Console, Ahrefs, or similar
    # For now, we'll create placeholder data
    
    # Get products and their keywords
    products = client.get_product_list(limit=50)
    
    # If specific keywords were provided, use those
    keywords = input_data.keywords or []
    
    # Otherwise, extract keywords from product tags
    if not keywords:
        for product in products:
            # Handle tags which might be a string or a list in GraphQL
            if 'tags' in product:
                if isinstance(product['tags'], str):
                    tags = product['tags'].split(', ') if product['tags'] else []
                elif isinstance(product['tags'], list):
                    tags = product['tags']
                else:
                    tags = []
                keywords.extend(tags)
        
        # Remove duplicates and limit to top 20
        keywords = list(set(keywords))[:20]
    
    # Generate placeholder keyword performance data
    keyword_performance = []
    
    for keyword in keywords:
        # Simulate ranking data
        ranking = {
            'keyword': keyword,
            'current_position': 15 + (hash(keyword) % 20),  # Random position between 15-35
            'previous_position': 15 + (hash(keyword) % 20) + 5,  # Slightly worse than current
            'search_volume': 500 + (hash(keyword) % 1500),  # Random volume between 500-2000
            'click_through_rate': 2.0 + (hash(keyword) % 8),  # Random CTR between 2-10%
            'ranking_change': -5 + (hash(keyword) % 10),  # Random change between -5 and +5
            'difficulty': 30 + (hash(keyword) % 40)  # Random difficulty between 30-70
        }
        
        # Add competitor data if requested
        if input_data.competitor_comparison:
            ranking['competitor_positions'] = {
                'competitor_1': 10 + (hash(f"{keyword}_1") % 20),
                'competitor_2': 10 + (hash(f"{keyword}_2") % 20),
                'competitor_3': 10 + (hash(f"{keyword}_3") % 20)
            }
        
        keyword_performance.append(ranking)
    
    # Sort by potential impact (combination of volume and current position)
    for kw in keyword_performance:
        kw['potential_impact'] = (kw['search_volume'] / 100) * (50 - min(kw['current_position'], 50)) / 50
    
    keyword_performance.sort(key=lambda x: x['potential_impact'], reverse=True)
    
    # Generate opportunity insights
    opportunities = []
    
    for kw in keyword_performance[:5]:  # Top 5 by potential impact
        if kw['current_position'] > 10:
            opportunities.append({
                'keyword': kw['keyword'],
                'opportunity': f"Improve ranking for '{kw['keyword']}' from position {kw['current_position']} to top 10",
                'potential_traffic_increase': int(kw['search_volume'] * 0.1),  # Estimate 10% of search volume
                'difficulty': kw['difficulty']
            })
    
    return {
        'tracking_frequency': input_data.tracking_frequency,
        'keywords_analyzed': len(keyword_performance),
        'keyword_performance': keyword_performance,
        'improvement_opportunities': opportunities,
        'overall_trends': {
            'improving_keywords': len([k for k in keyword_performance if k['ranking_change'] < 0]),
            'declining_keywords': len([k for k in keyword_performance if k['ranking_change'] > 0]),
            'stable_keywords': len([k for k in keyword_performance if k['ranking_change'] == 0])
        }
    }


def improve_product_search_rankings(
    client: ShopifyClient,
    input_data: SearchRankingInput,
    keyword_analysis: Dict = None,
    seo_audit: Dict = None
) -> Dict:
    """
    Generate strategies to improve product search rankings.
    
    Args:
        client: ShopifyClient instance
        input_data: Configuration for ranking improvement
        keyword_analysis: Optional pre-generated keyword analysis
        seo_audit: Optional pre-generated SEO audit
        
    Returns:
        Dictionary with ranking improvement strategies
    """
    logging.info(f"Generating strategies to improve search rankings with focus on: {input_data.focus_areas}")
    
    # If data wasn't provided, generate it
    if not keyword_analysis:
        keyword_analysis = analyze_keyword_performance(
            client,
            KeywordAnalysisInput(
                competitor_comparison=True
            )
        )
    
    # Convert product_ids to integers if provided
    product_ids = None
    if input_data.product_ids:
        product_ids = [int(pid) for pid in input_data.product_ids]
    
    if not seo_audit:
        seo_audit = audit_product_listings_for_seo(
            client,
            SEOAuditInput(
                product_ids=input_data.product_ids
            )
        )
    
    # Generate improvement strategies based on focus areas
    strategies = []
    
    # On-site search improvements
    if "on_site_search" in input_data.focus_areas:
        strategies.append({
            'focus_area': 'on_site_search',
            'title': 'Improve On-Site Search Visibility',
            'actions': [
                'Update product tags to include relevant search terms',
                'Ensure product titles include primary keywords',
                'Add product attributes and variants that match common search terms',
                'Review and improve internal categorization'
            ],
            'priority': 'high',
            'estimated_impact': 'medium',
            'implementation_difficulty': 'low'
        })
    
    # Google Shopping improvements
    if "google_shopping" in input_data.focus_areas:
        strategies.append({
            'focus_area': 'google_shopping',
            'title': 'Optimize Google Shopping Listings',
            'actions': [
                'Ensure product titles follow best practices (Brand + Product Type + Key Attributes)',
                'Optimize product descriptions with relevant keywords',
                'Use high-quality images that meet Google requirements',
                'Keep pricing and availability data accurate and up-to-date',
                'Implement proper product categorization'
            ],
            'priority': 'high',
            'estimated_impact': 'high',
            'implementation_difficulty': 'medium'
        })
    
    # Organic search improvements
    if "organic_search" in input_data.focus_areas:
        # Extract high-opportunity keywords
        target_keywords = [k['keyword'] for k in keyword_analysis.get('improvement_opportunities', [])]
        
        # Extract products needing SEO improvements
        products_needing_improvement = [
            p for p in seo_audit.get('audit_results', [])
            if p.get('overall_score', 0) < 70
        ]
        
        strategies.append({
            'focus_area': 'organic_search',
            'title': 'Boost Organic Search Rankings',
            'actions': [
                f"Target high-opportunity keywords: {', '.join(target_keywords[:3])}",
                f"Improve SEO for {len(products_needing_improvement)} underperforming product pages",
                'Create content that links to product pages',
                'Optimize page load speed and mobile experience',
                'Improve internal linking structure'
            ],
            'target_keywords': target_keywords,
            'target_products': [p.get('product_id') for p in products_needing_improvement[:5]],
            'priority': 'high',
            'estimated_impact': 'high',
            'implementation_difficulty': 'high'
        })
    
    # Generate implementation plan
    implementation_plan = {
        'immediate_actions': [],
        'short_term_actions': [],
        'long_term_actions': []
    }
    
    # Distribute actions across timeframes
    for strategy in strategies:
        actions = strategy.get('actions', [])
        
        # Immediate actions (first 20%)
        immediate_count = max(1, len(actions) // 5)
        implementation_plan['immediate_actions'].extend(
            [f"[{strategy['focus_area']}] {action}" for action in actions[:immediate_count]]
        )
        
        # Short term actions (next 40%)
        short_term_count = max(1, len(actions) // 2)
        implementation_plan['short_term_actions'].extend(
            [f"[{strategy['focus_area']}] {action}" for action in actions[immediate_count:immediate_count+short_term_count]]
        )
        
        # Long term actions (remaining 40%)
        implementation_plan['long_term_actions'].extend(
            [f"[{strategy['focus_area']}] {action}" for action in actions[immediate_count+short_term_count:]]
        )
    
    # Calculate expected improvement
    target_improvement_pct = float(input_data.target_improvement.rstrip('%'))
    expected_improvement = {
        'visibility_increase': f"{target_improvement_pct}%",
        'estimated_traffic_increase': f"{target_improvement_pct * 1.2:.1f}%",  # Slightly higher than visibility
        'estimated_conversion_increase': f"{target_improvement_pct * 0.3:.1f}%"  # Fraction of visibility increase
    }
    
    return {
        'strategies': strategies,
        'implementation_plan': implementation_plan,
        'expected_improvement': expected_improvement,
        'focus_areas': input_data.focus_areas,
        'target_improvement': input_data.target_improvement
    }


# Inventory Management Tools

def monitor_inventory_levels(
    client: ShopifyClient,
    input_data: InventoryMonitorInput
) -> Dict:
    """
    Monitor current inventory levels and identify items approaching reorder points.
    
    Args:
        client: ShopifyClient instance
        input_data: Configuration for inventory monitoring
        
    Returns:
        Dictionary with inventory status and alerts
    """
    logging.info(f"Monitoring inventory levels with check frequency: {input_data.check_frequency}")
    
    # Convert product_ids to integers if provided
    product_ids = None
    if input_data.product_ids:
        product_ids = [int(pid) for pid in input_data.product_ids]
    
    # Get inventory status
    inventory_status = client.get_inventory_status(product_ids=product_ids)
    
    # Identify low stock items
    low_stock_items = [item for item in inventory_status if item.is_low_stock]
    
    # Identify out of stock items
    out_of_stock_items = [item for item in inventory_status if item.available <= 0]
    
    # Identify items approaching low stock
    approaching_low_stock = []
    for item in inventory_status:
        if not item.is_low_stock and item.days_until_stockout is not None:
            if item.days_until_stockout <= 14:  # Within 2 weeks of stockout
                approaching_low_stock.append(item)
    
    # Generate alerts
    alerts = []
    
    # Critical alerts for out of stock
    for item in out_of_stock_items:
        alerts.append({
            'level': 'critical',
            'product_id': item.product_id,
            'variant_id': item.variant_id,
            'sku': item.sku,
            'title': item.title,
            'message': f"OUT OF STOCK: {item.title} (SKU: {item.sku})"
        })
    
    # High alerts for low stock
    for item in low_stock_items:
        if item not in out_of_stock_items:  # Avoid duplicate alerts
            alerts.append({
                'level': 'high',
                'product_id': item.product_id,
                'variant_id': item.variant_id,
                'sku': item.sku,
                'title': item.title,
                'message': f"LOW STOCK: {item.title} (SKU: {item.sku}) - Only {item.available} units remaining"
            })
    
    # Medium alerts for approaching low stock
    for item in approaching_low_stock:
        alerts.append({
            'level': 'medium',
            'product_id': item.product_id,
            'variant_id': item.variant_id,
            'sku': item.sku,
            'title': item.title,
            'message': f"APPROACHING LOW STOCK: {item.title} (SKU: {item.sku}) - Estimated stockout in {item.days_until_stockout} days"
        })
    
    # Calculate inventory health metrics
    total_items = len(inventory_status)
    stock_health = {
        'out_of_stock_percentage': len(out_of_stock_items) / total_items * 100 if total_items > 0 else 0,
        'low_stock_percentage': len(low_stock_items) / total_items * 100 if total_items > 0 else 0,
        'healthy_stock_percentage': (total_items - len(low_stock_items) - len(out_of_stock_items)) / total_items * 100 if total_items > 0 else 0,
        'total_products_monitored': total_items
    }
    
    return {
        'check_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'check_frequency': input_data.check_frequency,
        'inventory_summary': {
            'total_items': total_items,
            'out_of_stock': len(out_of_stock_items),
            'low_stock': len(low_stock_items),
            'approaching_low_stock': len(approaching_low_stock),
            'healthy_stock': total_items - len(low_stock_items) - len(out_of_stock_items)
        },
        'stock_health_metrics': stock_health,
        'alerts': alerts,
        'inventory_details': [item.dict() for item in inventory_status]
    }


def predict_inventory_needs(
    client: ShopifyClient,
    input_data: InventoryForecastInput
) -> Dict:
    """
    Forecast future inventory requirements based on historical sales data.
    
    Args:
        client: ShopifyClient instance
        input_data: Configuration for inventory forecasting
        
    Returns:
        Dictionary with inventory forecast
    """
    logging.info(f"Predicting inventory needs for horizon: {input_data.forecast_horizon}")
    
    # Parse forecast horizon
    days = int(input_data.forecast_horizon.split('_')[0])
    
    # Convert product_ids to integers if provided
    product_ids = None
    if input_data.product_ids:
        product_ids = [int(pid) for pid in input_data.product_ids]
    
    # Get current inventory status
    inventory_status = client.get_inventory_status(product_ids=product_ids)
    
    # Get historical sales data (last 90 days)
    start_date = datetime.now() - timedelta(days=90)
    performance_data = client.get_product_performance(
        product_ids=product_ids,
        start_date=start_date
    )
    
    # Create lookup for performance data
    performance_by_id = {p.product_id: p for p in performance_data}
    
    # Generate forecast
    forecast = []
    
    for item in inventory_status:
        # Get performance data for this product
        perf = performance_by_id.get(item.product_id)
        
        if perf:
            # Calculate daily sales rate (units per day)
            daily_sales_rate = perf.units_sold / 90  # 90 days of historical data
            
            # Apply seasonality adjustment if requested
            seasonality_factor = 1.0
            if input_data.include_seasonality:
                # In a real implementation, this would use historical data to calculate seasonality
                # For now, use a placeholder adjustment based on current month
                current_month = datetime.now().month
                if current_month in [11, 12]:  # Holiday season
                    seasonality_factor = 1.5
                elif current_month in [1, 2]:  # Post-holiday slump
                    seasonality_factor = 0.8
                elif current_month in [6, 7, 8]:  # Summer
                    seasonality_factor = 1.2
            
            # Apply adjusted daily rate
            adjusted_daily_rate = daily_sales_rate * seasonality_factor
            
            # Calculate projected sales for forecast period
            projected_sales = adjusted_daily_rate * days
            
            # Calculate confidence interval
            confidence_interval = input_data.confidence_interval
            lower_bound = projected_sales * (1 - (1 - confidence_interval) / 2)
            upper_bound = projected_sales * (1 + (1 - confidence_interval) / 2)
            
            # Calculate days until stockout
            days_until_stockout = item.available / adjusted_daily_rate if adjusted_daily_rate > 0 else None
            
            # Calculate required inventory
            required_inventory = max(0, projected_sales - item.available)
            
            forecast.append({
                'product_id': item.product_id,
                'variant_id': item.variant_id,
                'sku': item.sku,
                'title': item.title,
                'current_stock': item.available,
                'daily_sales_rate': daily_sales_rate,
                'seasonality_factor': seasonality_factor,
                'adjusted_daily_rate': adjusted_daily_rate,
                'projected_sales': projected_sales,
                'projected_sales_range': {
                    'lower_bound': lower_bound,
                    'upper_bound': upper_bound
                },
                'days_until_stockout': days_until_stockout,
                'required_inventory': required_inventory
            })
    
    # Sort by urgency (days until stockout)
    forecast.sort(key=lambda x: x['days_until_stockout'] if x['days_until_stockout'] is not None else float('inf'))
    
    return {
        'forecast_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'forecast_horizon': input_data.forecast_horizon,
        'confidence_interval': input_data.confidence_interval,
        'include_seasonality': input_data.include_seasonality,
        'forecast_summary': {
            'total_products': len(forecast),
            'products_needing_restock': len([f for f in forecast if f['required_inventory'] > 0]),
            'total_units_needed': sum(f['required_inventory'] for f in forecast)
        },
        'forecast_details': forecast
    }


def generate_restock_recommendations(
    client: ShopifyClient,
    input_data: RestockRecommendationInput,
    inventory_status: Dict = None,
    inventory_forecast: Dict = None
) -> Dict:
    """
    Generate actionable restock recommendations based on inventory status and forecast.
    
    Args:
        client: ShopifyClient instance
        input_data: Configuration for restock recommendations
        inventory_status: Optional pre-generated inventory status
        inventory_forecast: Optional pre-generated inventory forecast
        
    Returns:
        Dictionary with restock recommendations
    """
    logging.info(f"Generating restock recommendations optimizing for: {input_data.optimize_for}")
    
    # If data wasn't provided, generate it
    if not inventory_status:
        inventory_status = monitor_inventory_levels(
            client,
            InventoryMonitorInput()
        )
    
    if not inventory_forecast:
        inventory_forecast = predict_inventory_needs(
            client,
            InventoryForecastInput(
                forecast_horizon="90_days",
                include_seasonality=True
            )
        )
    
    # Get supplier lead times
    lead_times = client._get_supplier_lead_times()
    
    # Generate recommendations from the client
    recommendations = client.generate_restock_recommendations(
        consider_lead_time=input_data.consider_lead_time,
        optimize_for=input_data.optimize_for
    )
    
    # Enhance recommendations with additional data
    enhanced_recommendations = []
    
    for rec in recommendations:
        # Find forecast data for this product
        forecast_item = next(
            (f for f in inventory_forecast.get('forecast_details', []) 
             if f['product_id'] == rec['product_id'] and f['variant_id'] == rec['variant_id']),
            None
        )
        
        enhanced_rec = {**rec}  # Copy original recommendation
        
        # Add forecast data if available
        if forecast_item:
            enhanced_rec['forecast'] = {
                'projected_sales': forecast_item['projected_sales'],
                'projected_sales_range': forecast_item['projected_sales_range'],
                'daily_sales_rate': forecast_item['daily_sales_rate']
            }
        
        # Add cost analysis if requested
        if input_data.include_cost_analysis:
            enhanced_rec['cost_analysis'] = {
                'unit_cost': rec.get('cost_per_unit', 0),
                'total_cost': rec.get('total_cost', 0),
                'carrying_cost': rec.get('total_cost', 0) * 0.25,  # Estimate 25% carrying cost
                'stockout_cost': rec.get('cost_per_unit', 0) * 1.5 * rec.get('reorder_quantity', 0)  # Estimate lost revenue
            }
        
        enhanced_recommendations.append(enhanced_rec)
    
    # Group recommendations by supplier
    supplier_groups = {}
    for rec in enhanced_recommendations:
        supplier = rec.get('supplier', 'Unknown')
        if supplier not in supplier_groups:
            supplier_groups[supplier] = []
        supplier_groups[supplier].append(rec)
    
    # Calculate total costs
    total_cost = sum(rec.get('total_cost', 0) for rec in enhanced_recommendations)
    
    return {
        'recommendation_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'optimization_strategy': input_data.optimize_for,
        'consider_lead_time': input_data.consider_lead_time,
        'summary': {
            'total_products_to_restock': len(enhanced_recommendations),
            'total_units_to_order': sum(rec.get('reorder_quantity', 0) for rec in enhanced_recommendations),
            'total_cost': total_cost,
            'suppliers_count': len(supplier_groups)
        },
        'recommendations_by_priority': {
            'critical': [r for r in enhanced_recommendations if r.get('priority') == 'critical'],
            'high': [r for r in enhanced_recommendations if r.get('priority') == 'high'],
            'medium': [r for r in enhanced_recommendations if r.get('priority') == 'medium'],
            'low': [r for r in enhanced_recommendations if r.get('priority') == 'low']
        },
        'recommendations_by_supplier': supplier_groups,
        'all_recommendations': enhanced_recommendations
    }


def analyze_inventory_turnover(
    client: ShopifyClient,
    input_data: InventoryTurnoverInput
) -> Dict:
    """
    Calculate and analyze inventory turnover rates to identify slow-moving products.
    
    Args:
        client: ShopifyClient instance
        input_data: Configuration for turnover analysis
        
    Returns:
        Dictionary with inventory turnover analysis
    """
    logging.info(f"Analyzing inventory turnover for period: {input_data.analysis_period}")
    
    # Determine time period for analysis
    if input_data.analysis_period == "quarterly":
        days = 90
    elif input_data.analysis_period == "monthly":
        days = 30
    elif input_data.analysis_period == "annually":
        days = 365
    else:
        days = 90  # Default to quarterly
    
    start_date = datetime.now() - timedelta(days=days)
    
    # Get inventory status
    inventory_status = client.get_inventory_status()
    
    # Get sales data for the period
    performance_data = client.get_product_performance(start_date=start_date)
    
    # Create lookup for performance data
    performance_by_id = {p.product_id: p for p in performance_data}
    
    # Calculate turnover rates
    turnover_data = []
    
    for item in inventory_status:
        # Get performance data for this product
        perf = performance_by_id.get(item.product_id)
        
        if perf:
            # Calculate average inventory
            # In a real implementation, this would use historical inventory levels
            # For now, use current inventory as an approximation
            average_inventory = item.available
            
            # Calculate cost of goods sold
            cogs = perf.units_sold * (perf.revenue / perf.units_sold) * (1 - perf.profit_margin) if perf.units_sold > 0 else 0
            
            # Calculate turnover rate
            turnover_rate = cogs / average_inventory if average_inventory > 0 else 0
            
            # Calculate days of inventory
            days_of_inventory = days / turnover_rate if turnover_rate > 0 else float('inf')
            
            # Get product details
            product = client.get_product_by_id(int(item.product_id))
            
            # Get category - in GraphQL this comes from collections
            category = "Uncategorized"
            if 'collections' in product and product['collections']:
                category = product['collections'][0]['title']
            
            # Get price point from variants
            price = 0
            if 'variants' in product and 'edges' in product['variants']:
                for variant_edge in product['variants']['edges']:
                    variant = variant_edge['node']
                    if str(client._extract_id_from_gid(variant['id'])) == item.variant_id:
                        price = float(variant.get('price', 0))
                        break
            
            # Determine price point category
            if price < 25:
                price_point = "Low"
            elif price < 100:
                price_point = "Medium"
            else:
                price_point = "High"
            
            # Get supplier
            supplier = client._get_supplier_for_product(item.product_id)
            
            turnover_data.append({
                'product_id': item.product_id,
                'variant_id': item.variant_id,
                'sku': item.sku,
                'title': item.title,
                'average_inventory': average_inventory,
                'cogs': cogs,
                'turnover_rate': turnover_rate,
                'days_of_inventory': days_of_inventory,
                'category': category,
                'price_point': price_point,
                'price': price,
                'supplier': supplier
            })
    
    # Calculate average turnover rate
    avg_turnover = sum(item['turnover_rate'] for item in turnover_data) / len(turnover_data) if turnover_data else 0
    
    # Identify slow-moving products (turnover rate < 50% of average)
    slow_moving = [item for item in turnover_data if item['turnover_rate'] < avg_turnover * 0.5]
    
    # Identify fast-moving products (turnover rate > 150% of average)
    fast_moving = [item for item in turnover_data if item['turnover_rate'] > avg_turnover * 1.5]
    
    # Group by categories requested
    category_analysis = {}
    for category_type in input_data.categorize_by:
        if category_type == "product_category":
            key = 'category'
        elif category_type == "price_point":
            key = 'price_point'
        elif category_type == "supplier":
            key = 'supplier'
        else:
            continue
            
        groups = {}
        for item in turnover_data:
            group = item.get(key, 'Unknown')
            if group not in groups:
                groups[group] = []
            groups[group].append(item)
            
        # Calculate average turnover by group
        avg_by_group = {}
        for group, items in groups.items():
            avg_by_group[group] = sum(item['turnover_rate'] for item in items) / len(items) if items else 0
            
        category_analysis[category_type] = {
            'groups': groups,
            'average_by_group': avg_by_group
        }
    
    # Generate recommendations for slow-moving products
    recommendations = []
    
    for item in slow_moving:
        if item['days_of_inventory'] > 180:  # Over 6 months of inventory
            recommendations.append({
                'product_id': item['product_id'],
                'sku': item['sku'],
                'title': item['title'],
                'days_of_inventory': item['days_of_inventory'],
                'recommendation': 'Consider clearance sale or liquidation',
                'priority': 'high'
            })
        elif item['days_of_inventory'] > 90:  # 3-6 months of inventory
            recommendations.append({
                'product_id': item['product_id'],
                'sku': item['sku'],
                'title': item['title'],
                'days_of_inventory': item['days_of_inventory'],
                'recommendation': 'Implement promotional pricing or bundle with fast-moving products',
                'priority': 'medium'
            })
        else:
            recommendations.append({
                'product_id': item['product_id'],
                'sku': item['sku'],
                'title': item['title'],
                'days_of_inventory': item['days_of_inventory'],
                'recommendation': 'Monitor closely and consider reducing reorder quantities',
                'priority': 'low'
            })
    
    return {
        'analysis_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'analysis_period': input_data.analysis_period,
        'summary': {
            'total_products_analyzed': len(turnover_data),
            'average_turnover_rate': avg_turnover,
            'slow_moving_products': len(slow_moving),
            'fast_moving_products': len(fast_moving),
            'average_days_of_inventory': sum(item['days_of_inventory'] for item in turnover_data if item['days_of_inventory'] != float('inf')) / 
                                         len([item for item in turnover_data if item['days_of_inventory'] != float('inf')]) 
                                         if turnover_data else 0
        },
        'category_analysis': category_analysis,
        'slow_moving_products': slow_moving,
        'fast_moving_products': fast_moving,
        'recommendations': recommendations,
        'all_products': turnover_data
    }


# Register tools with the registry
def register_tools(registry: ToolRegistry) -> None:
    """Register all Shopify tools with the tool registry."""
    
    # Product Analytics Tools
    registry.register_tool(
        "analyze_product_sales",
        analyze_product_sales,
        "Analyze sales data for products to identify trends and performance metrics",
        ProductAnalyticsInput
    )
    
    registry.register_tool(
        "identify_product_performance_gaps",
        identify_product_performance_gaps,
        "Identify underperforming products based on comparison to benchmarks",
        PerformanceGapInput
    )
    
    registry.register_tool(
        "analyze_customer_product_interactions",
        analyze_customer_product_interactions,
        "Analyze how customers interact with products through the purchase funnel",
        CustomerInteractionInput
    )
    
    registry.register_tool(
        "generate_product_performance_dashboard",
        generate_product_performance_dashboard,
        "Generate a dashboard summarizing key product performance metrics",
        DashboardInput
    )
    
    # SEO Tools
    registry.register_tool(
        "audit_product_listings_for_seo",
        audit_product_listings_for_seo,
        "Audit product listings for SEO best practices",
        SEOAuditInput
    )
    
    registry.register_tool(
        "generate_seo_product_descriptions",
        generate_seo_product_descriptions,
        "Generate SEO-optimized product descriptions",
        ContentGenerationInput
    )
    
    registry.register_tool(
        "analyze_keyword_performance",
        analyze_keyword_performance,
        "Analyze keyword rankings and performance for product pages",
        KeywordAnalysisInput
    )
    
    registry.register_tool(
        "improve_product_search_rankings",
        improve_product_search_rankings,
        "Generate strategies to improve product search rankings",
        SearchRankingInput
    )
    
    # Inventory Management Tools
    registry.register_tool(
        "monitor_inventory_levels",
        monitor_inventory_levels,
        "Monitor current inventory levels and identify items approaching reorder points",
        InventoryMonitorInput
    )
    
    registry.register_tool(
        "predict_inventory_needs",
        predict_inventory_needs,
        "Forecast future inventory requirements based on historical sales data",
        InventoryForecastInput
    )
    
    registry.register_tool(
        "generate_restock_recommendations",
        generate_restock_recommendations,
        "Generate actionable restock recommendations",
        RestockRecommendationInput
    )
    
    registry.register_tool(
        "analyze_inventory_turnover",
        analyze_inventory_turnover,
        "Calculate and analyze inventory turnover rates to identify slow-moving products",
        InventoryTurnoverInput
    )
