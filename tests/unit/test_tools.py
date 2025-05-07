import pytest
from unittest.mock import MagicMock, patch
import json
from datetime import datetime, timedelta

# Import the tools modules
from ru_twin.tools.tool_registry import ToolRegistry
from ru_twin.tools.shopify_tools import (
    analyze_product_sales,
    identify_product_performance_gaps,
    analyze_customer_product_interactions,
    generate_product_performance_dashboard,
    audit_product_listings_for_seo,
    ProductAnalyticsInput,
    PerformanceGapInput,
    CustomerInteractionInput,
    DashboardInput,
    SEOAuditInput
)
from ru_twin.tools.teller_tools import (
    get_accounts,
    get_account_details,
    get_account_summary,
    get_transactions,
    analyze_spending,
    analyze_cash_flow,
    identify_recurring_transactions,
    forecast_cash_flow,
    AccountsGetInput,
    AccountDetailsInput,
    AccountSummaryInput,
    TransactionsGetInput,
    SpendingAnalysisInput,
    CashFlowAnalysisInput,
    RecurringTransactionsInput,
    CashFlowForecastInput
)
from ru_twin.mcp_clients.shopify import ShopifyClient, ProductPerformanceMetrics
from ru_twin.mcp_clients.teller import TellerClient, Account, Balance, Transaction


# Fixtures for common test objects
@pytest.fixture
def tool_registry():
    """Create a tool registry for testing."""
    return ToolRegistry()


@pytest.fixture
def mock_shopify_client():
    """Create a mock ShopifyClient for testing."""
    client = MagicMock(spec=ShopifyClient)
    
    # Mock common methods
    client.get_product_performance.return_value = [
        ProductPerformanceMetrics(
            product_id="1",
            title="Test Product",
            revenue=100.0,
            units_sold=10,
            profit_margin=0.4,
            conversion_rate=2.5,
            views=400,
            add_to_carts=20,
            checkout_initiations=15
        )
    ]
    
    client.identify_underperforming_products.return_value = [
        {
            "product_id": "2",
            "title": "Underperforming Product",
            "reasons": ["Revenue is 50.00 vs category average 100.00"],
            "metrics": {
                "revenue": 50.0,
                "units_sold": 5,
                "profit_margin": 0.2,
                "conversion_rate": 1.0
            },
            "category_averages": {
                "revenue": 100.0,
                "units_sold": 10,
                "profit_margin": 0.4,
                "conversion_rate": 2.0
            }
        }
    ]
    
    return client


@pytest.fixture
def mock_teller_client():
    """Create a mock TellerClient for testing."""
    client = MagicMock(spec=TellerClient)
    
    # Mock account data
    mock_accounts = [
        Account(
            id="acc_123",
            institution={"id": "inst_1", "name": "Test Bank"},
            last_four="1234",
            name="Checking Account",
            subtype="checking",
            type="depository",
            status="open",
            currency="USD",
            enrollment_id="enr_1",
            links={}
        ),
        Account(
            id="acc_456",
            institution={"id": "inst_1", "name": "Test Bank"},
            last_four="5678",
            name="Savings Account",
            subtype="savings",
            type="depository",
            status="open",
            currency="USD",
            enrollment_id="enr_1",
            links={}
        )
    ]
    
    # Mock balance data
    mock_balances = [
        Balance(
            account_id="acc_123",
            available=950.0,
            ledger=1000.0,
            links={}
        ),
        Balance(
            account_id="acc_456",
            available=2000.0,
            ledger=2000.0,
            links={}
        )
    ]
    
    # Mock transaction data
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    mock_transactions = [
        Transaction(
            id="txn_1",
            account_id="acc_123",
            amount=50.0,
            date=today,
            description="Grocery Store",
            status="posted",
            details={},
            running_balance=950.0,
            type="purchase",
            links={}
        ),
        Transaction(
            id="txn_2",
            account_id="acc_123",
            amount=-500.0,
            date=yesterday,
            description="Paycheck",
            status="posted",
            details={},
            running_balance=1000.0,
            type="deposit",
            links={}
        )
    ]
    
    # Set up mock returns
    client.get_accounts.return_value = mock_accounts
    client.get_balances.return_value = mock_balances
    client.get_account.return_value = mock_accounts[0]
    client.get_account_balance.return_value = mock_balances[0]
    client.get_transactions.return_value = mock_transactions
    client.get_account_transactions.return_value = mock_transactions
    client.calculate_account_summary.return_value = {
        "accounts_count": 2,
        "totals_by_type": {"depository": {"count": 2, "ledger_balance": 3000.0, "available_balance": 2950.0}},
        "total_ledger_balance": 3000.0,
        "total_available_balance": 2950.0,
        "account_summary": []
    }
    client.categorize_transactions.return_value = {
        "purchase": [mock_transactions[0]],
        "deposit": [mock_transactions[1]]
    }
    client.analyze_cash_flow.return_value = {
        "period_days": 30,
        "start_date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
        "end_date": today,
        "inflows": 500.0,
        "outflows": 50.0,
        "net_cash_flow": 450.0,
        "recurring_transactions": []
    }
    
    return client


# Shopify Tools Tests
class TestShopifyTools:
    def test_analyze_product_sales(self, mock_shopify_client):
        """Test the analyze_product_sales tool."""
        input_data = ProductAnalyticsInput(
            time_period="last_30_days",
            metrics=["revenue", "units_sold"]
        )
        
        result = analyze_product_sales(mock_shopify_client, input_data)
        
        assert result is not None
        assert "overall_metrics" in result
        assert "top_performers" in result
        assert "raw_data" in result
        assert result["time_period"] == "last_30_days"
        assert mock_shopify_client.get_product_performance.called
    
    def test_identify_product_performance_gaps(self, mock_shopify_client):
        """Test the identify_product_performance_gaps tool."""
        input_data = PerformanceGapInput(
            benchmark_type="category_average",
            performance_threshold=0.75
        )
        
        result = identify_product_performance_gaps(mock_shopify_client, input_data)
        
        assert result is not None
        assert "summary" in result
        assert "underperforming_products" in result
        assert len(result["underperforming_products"]) > 0
        assert mock_shopify_client.identify_underperforming_products.called
    
    def test_analyze_customer_product_interactions(self, mock_shopify_client):
        """Test the analyze_customer_product_interactions tool."""
        input_data = CustomerInteractionInput(
            track_events=["product_view", "add_to_cart"]
        )
        
        result = analyze_customer_product_interactions(mock_shopify_client, input_data)
        
        assert result is not None
        assert "product_interactions" in result
        assert "average_funnel" in result
        assert "average_conversion_rates" in result
        assert "recommendations" in result
        assert mock_shopify_client.get_product_performance.called
    
    def test_generate_product_performance_dashboard(self, mock_shopify_client):
        """Test the generate_product_performance_dashboard tool."""
        # Create mock input data
        input_data = DashboardInput(
            dashboard_format="interactive",
            refresh_frequency="weekly"
        )
        
        # Create mock sales data, gap analysis, and interaction data
        sales_data = {
            "overall_metrics": {
                "total_revenue": 1000.0,
                "total_units_sold": 100
            },
            "top_performers": {
                "by_revenue": [{"product_id": "1", "title": "Test Product", "revenue": 100.0}]
            }
        }
        
        gap_analysis = {
            "summary": {
                "total_underperforming": 1
            },
            "underperforming_products": [
                {"product_id": "2", "title": "Underperforming Product"}
            ]
        }
        
        interaction_data = {
            "average_funnel": {
                "views": 400,
                "add_to_carts": 20
            },
            "average_conversion_rates": {
                "view_to_cart": 5.0
            },
            "recommendations": ["Focus on improving view to cart conversion"]
        }
        
        result = generate_product_performance_dashboard(
            mock_shopify_client,
            input_data,
            sales_data,
            gap_analysis,
            interaction_data
        )
        
        assert result is not None
        assert "title" in result
        assert "sections" in result
        assert "recommendations" in result
        assert len(result["sections"]) == 4
        assert len(result["recommendations"]) > 0
    
    def test_audit_product_listings_for_seo(self, mock_shopify_client):
        """Test the audit_product_listings_for_seo tool."""
        # Mock the get_product_seo_data method
        mock_shopify_client.get_product_seo_data.return_value = [
            SEOMetadata(
                product_id="1",
                title="Test Product",
                description="This is a test product description",
                url="https://example.com/products/test-product",
                handle="test-product",
                tags=["test", "product"],
                seo_title="Test Product - SEO Title",
                seo_description="SEO optimized description",
                keyword_density=2.5,
                seo_score=85.0
            )
        ]
        
        input_data = SEOAuditInput(
            audit_factors=["title_optimization", "description_quality"]
        )
        
        result = audit_product_listings_for_seo(mock_shopify_client, input_data)
        
        assert result is not None
        assert "summary" in result
        assert "audit_results" in result
        assert len(result["audit_results"]) > 0
        assert "overall_score" in result["audit_results"][0]
        assert "audit_details" in result["audit_results"][0]
        assert mock_shopify_client.get_product_seo_data.called


# Teller Tools Tests
class TestTellerTools:
    def test_get_accounts(self, mock_teller_client):
        """Test the get_accounts tool."""
        input_data = AccountsGetInput(include_balances=True)
        
        result = get_accounts(mock_teller_client, input_data)
        
        assert result is not None
        assert "accounts" in result
        assert "accounts_by_type" in result
        assert "total_accounts" in result
        assert "balances" in result
        assert len(result["accounts"]) == 2
        assert mock_teller_client.get_accounts.called
        assert mock_teller_client.get_balances.called
    
    def test_get_account_details(self, mock_teller_client):
        """Test the get_account_details tool."""
        input_data = AccountDetailsInput(
            account_id="acc_123",
            include_balance=True
        )
        
        result = get_account_details(mock_teller_client, input_data)
        
        assert result is not None
        assert "account" in result
        assert "balance" in result
        assert "recent_transactions" in result
        assert result["account"]["id"] == "acc_123"
        assert mock_teller_client.get_account.called
        assert mock_teller_client.get_account_balance.called
        assert mock_teller_client.get_account_transactions.called
    
    def test_get_account_summary(self, mock_teller_client):
        """Test the get_account_summary tool."""
        input_data = AccountSummaryInput(group_by_type=True)
        
        result = get_account_summary(mock_teller_client, input_data)
        
        assert result is not None
        assert "accounts_count" in result
        assert "totals_by_type" in result
        assert "total_ledger_balance" in result
        assert "total_available_balance" in result
        assert mock_teller_client.calculate_account_summary.called
    
    def test_get_transactions(self, mock_teller_client):
        """Test the get_transactions tool."""
        input_data = TransactionsGetInput(
            from_date="2023-01-01",
            to_date="2023-01-31"
        )
        
        result = get_transactions(mock_teller_client, input_data)
        
        assert result is not None
        assert "transactions" in result
        assert "total_transactions" in result
        assert "total_amount" in result
        assert "average_transaction" in result
        assert "status_counts" in result
        assert "type_counts" in result
        assert len(result["transactions"]) == 2
        assert mock_teller_client.get_transactions.called
    
    def test_analyze_spending(self, mock_teller_client):
        """Test the analyze_spending tool."""
        input_data = SpendingAnalysisInput(
            from_date="2023-01-01",
            to_date="2023-01-31",
            group_by="type"
        )
        
        result = analyze_spending(mock_teller_client, input_data)
        
        assert result is not None
        assert "total_spending" in result
        assert "average_transaction" in result
        assert "transaction_count" in result
        assert "spending_groups" in result
        assert "spending_distribution" in result
        assert "top_spending_groups" in result
        assert mock_teller_client.get_transactions.called
    
    def test_analyze_cash_flow(self, mock_teller_client):
        """Test the analyze_cash_flow tool."""
        input_data = CashFlowAnalysisInput(period_days=30)
        
        result = analyze_cash_flow(mock_teller_client, input_data)
        
        assert result is not None
        assert "inflows" in result
        assert "outflows" in result
        assert "net_cash_flow" in result
        assert "daily_averages" in result
        assert "insights" in result
        assert mock_teller_client.get_transactions.called
        assert mock_teller_client.analyze_cash_flow.called
    
    def test_identify_recurring_transactions(self, mock_teller_client):
        """Test the identify_recurring_transactions tool."""
        # Mock the necessary methods
        mock_teller_client.get_account_transactions.return_value = [
            Transaction(
                id="txn_3",
                account_id="acc_123",
                amount=9.99,
                date="2023-01-01",
                description="Netflix Subscription",
                status="posted",
                details={},
                running_balance=990.01,
                type="purchase",
                links={}
            ),
            Transaction(
                id="txn_4",
                account_id="acc_123",
                amount=9.99,
                date="2023-02-01",
                description="Netflix Subscription",
                status="posted",
                details={},
                running_balance=980.02,
                type="purchase",
                links={}
            )
        ]
        
        input_data = RecurringTransactionsInput(
            min_occurrences=2,
            amount_tolerance=0.5,
            days=90,
            account_id="acc_123"
        )
        
        result = identify_recurring_transactions(mock_teller_client, input_data)
        
        assert result is not None
        assert "recurring_transactions" in result
        assert "recurring_income" in result
        assert "recurring_expenses" in result
        assert "total_recurring_income" in result
        assert "total_recurring_expenses" in result
        assert "grouped_by_frequency" in result
        assert mock_teller_client.get_account_transactions.called
    
    def test_forecast_cash_flow(self, mock_teller_client):
        """Test the forecast_cash_flow tool."""
        # Mock additional methods needed for forecasting
        mock_teller_client.get_account_balance.return_value = Balance(
            account_id="acc_123",
            available=950.0,
            ledger=1000.0,
            links={}
        )
        
        input_data = CashFlowForecastInput(
            forecast_days=30,
            include_recurring=True,
            account_id="acc_123"
        )
        
        result = forecast_cash_flow(mock_teller_client, input_data)
        
        assert result is not None
        assert "starting_balance" in result
        assert "ending_balance" in result
        assert "forecast_period" in result
        assert "summary" in result
        assert "daily_forecast" in result
        assert len(result["daily_forecast"]) > 0
        assert mock_teller_client.get_account_transactions.called
        assert mock_teller_client.get_account_balance.called


# Tool Registry Tests
def test_tool_registry(tool_registry):
    """Test the ToolRegistry functionality."""
    # Define a simple test tool
    def test_tool(x: int, y: int) -> int:
        return x + y
    
    # Create a simple input model
    class TestToolInput(BaseModel):
        x: int
        y: int
    
    # Register the tool
    tool_registry.register_tool(
        "test_tool",
        test_tool,
        "A simple test tool that adds two numbers",
        TestToolInput
    )
    
    # Verify the tool was registered
    assert "test_tool" in tool_registry.tools
    assert tool_registry.tools["test_tool"]["function"] == test_tool
    assert tool_registry.tools["test_tool"]["description"] == "A simple test tool that adds two numbers"
    assert tool_registry.tools["test_tool"]["input_model"] == TestToolInput
    
    # Test getting a tool
    tool_info = tool_registry.get_tool("test_tool")
    assert tool_info is not None
    assert tool_info["function"] == test_tool
    
    # Test getting all tools
    all_tools = tool_registry.get_all_tools()
    assert len(all_tools) == 1
    assert "test_tool" in all_tools


# Example test (as requested in the instructions)
def test_example_tool():
    assert True
