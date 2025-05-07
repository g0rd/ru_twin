# Plaid Integration for RuTwin Crew

This document provides comprehensive guidance for using the Plaid integration with RuTwin Crew. The integration leverages Plaid's financial data API to enable account management, transaction analysis, budget planning, financial health assessment, and investment tracking.

## Table of Contents

- [Overview](#overview)
- [Setup Instructions](#setup-instructions)
- [Configuration](#configuration)
- [Available Tools](#available-tools)
- [Task Definitions](#task-definitions)
- [API Usage](#api-usage)
- [Common Workflows](#common-workflows)
- [Troubleshooting](#troubleshooting)
- [Resources](#resources)

## Overview

The Plaid integration for RuTwin Crew provides a comprehensive set of tools and tasks that allow AI agents to interact with financial data. The integration is built around five main functional areas:

1. **Account Management**: Connect to financial institutions, retrieve account information, and verify identity.
2. **Transaction Analysis**: Retrieve, categorize, search, and enrich transaction data.
3. **Budget Planning**: Create budgets, analyze performance, and forecast cash flow.
4. **Financial Health Assessment**: Evaluate overall financial health, analyze debt, and plan for savings goals.
5. **Investment Tracking**: Monitor investment holdings, analyze portfolio performance, and optimize asset allocation.

All functionality is implemented using Plaid's API, providing secure access to financial data across thousands of financial institutions.

## Setup Instructions

### Prerequisites

- Plaid developer account (sign up at [plaid.com](https://plaid.com/))
- Plaid client ID and secret keys
- Access to the Plaid Dashboard to manage API keys and environment settings
- Understanding of Plaid's Link flow for user authentication

### Environment Variables

Add the following variables to your `.env` file:

```
PLAID_CLIENT_ID=your_client_id
PLAID_SECRET=your_secret_key
PLAID_ENVIRONMENT=development  # sandbox, development, or production
```

### Installation Steps

1. Ensure the Plaid client is properly imported in your application:

```python
# In your application initialization
from ru_twin.mcp_clients.plaid import PlaidClient
from ru_twin.tools.finance_tools import register_tools
```

2. Initialize the Plaid client:

```python
# Initialize the client with credentials from environment variables
import os
from dotenv import load_dotenv
from ru_twin.mcp_clients.plaid import PlaidClient, PlaidEnvironment

load_dotenv()

plaid_client = PlaidClient(
    client_id=os.getenv("PLAID_CLIENT_ID"),
    secret=os.getenv("PLAID_SECRET"),
    environment=PlaidEnvironment(os.getenv("PLAID_ENVIRONMENT", "development"))
)
```

3. Register the finance tools with your tool registry:

```python
from ru_twin.tools.tool_registry import ToolRegistry
from ru_twin.tools.finance_tools import register_tools

# Initialize your tool registry
tool_registry = ToolRegistry()

# Register finance tools
register_tools(tool_registry)
```

4. Import the finance tasks in your main tasks configuration:

```yaml
# In your main tasks.yaml file
imports:
  - src/ru_twin/config/finance_tasks.yaml

# Your other tasks...
```

## Configuration

### Plaid Environments

Plaid offers three environments:

1. **Sandbox**: For testing with mock data
2. **Development**: For development with real data (limited institutions)
3. **Production**: For production use with full institution coverage

Choose the appropriate environment based on your development stage.

### Link Flow Integration

The Plaid integration uses a two-step process for connecting user bank accounts:

1. Create a Link token using the `create_link_token` tool
2. Exchange the public token for an access token using the `exchange_public_token` tool

This follows Plaid's recommended authentication flow:

```
Client App → Create Link Token → Plaid Link → Get Public Token → Exchange for Access Token
```

### Access Token Management

Access tokens are stored in the PlaidClient instance for the duration of the session. In a production environment, you should implement secure storage for these tokens.

## Available Tools

### Account Management Tools

| Tool Name | Description | Input Parameters |
|-----------|-------------|------------------|
| `create_link_token` | Create a Link token for initializing Plaid Link | `user_id`, `client_name`, `products`, `country_codes`, `language`, `webhook` |
| `exchange_public_token` | Exchange a public token for an access token | `public_token` |
| `get_accounts` | Get accounts for a specific access token | `access_token`, `include_balances` |
| `get_account_balances` | Get balances for accounts | `access_token`, `account_ids` |
| `get_account_identity` | Get identity information for accounts | `access_token` |

### Transaction Analysis Tools

| Tool Name | Description | Input Parameters |
|-----------|-------------|------------------|
| `get_transactions` | Get transactions for accounts | `access_token`, `start_date`, `end_date`, `account_ids`, `count`, `offset` |
| `categorize_transactions` | Categorize a list of transactions | `transactions` |
| `search_transactions` | Search for transactions matching criteria | `transactions`, `query`, `min_amount`, `max_amount`, `start_date`, `end_date` |
| `enrich_transactions` | Enrich transaction data | `transactions` |

### Budget Planning Tools

| Tool Name | Description | Input Parameters |
|-----------|-------------|------------------|
| `create_budget` | Create a budget plan | `name`, `period`, `categories`, `start_date`, `end_date` |
| `analyze_budget` | Analyze budget performance | `budget`, `transactions` |
| `forecast_cash_flow` | Forecast future cash flow | `transactions`, `account_balances`, `forecast_days`, `include_recurring` |

### Financial Health Tools

| Tool Name | Description | Input Parameters |
|-----------|-------------|------------------|
| `assess_financial_health` | Assess overall financial health | `balances`, `transactions`, `liabilities` |
| `analyze_debt` | Analyze debt and provide repayment strategies | `liabilities`, `income` |
| `plan_savings_goal` | Plan for achieving a savings goal | `goal_amount`, `current_savings`, `monthly_contribution`, `interest_rate` |
| `analyze_spending` | Analyze spending patterns | `transactions`, `start_date`, `end_date`, `group_by` |
| `analyze_merchants` | Analyze spending by merchant | `transactions`, `months` |
| `identify_recurring_expenses` | Identify recurring expenses | `transactions`, `min_occurrences`, `amount_tolerance`, `days` |

### Investment Tracking Tools

| Tool Name | Description | Input Parameters |
|-----------|-------------|------------------|
| `get_investment_holdings` | Get investment holdings | `access_token` |
| `get_investment_transactions` | Get investment transactions | `access_token`, `start_date`, `end_date` |
| `analyze_portfolio` | Analyze investment portfolio | `holdings`, `risk_tolerance` |
| `analyze_asset_allocation` | Analyze asset allocation | `holdings`, `target_allocation` |

## Task Definitions

The Plaid integration includes pre-defined tasks in `src/ru_twin/config/finance_tasks.yaml`. These tasks are configured to work with the CrewAI framework and can be assigned to specific agents.

Example task definition:

```yaml
analyze_recent_transactions:
  name: "Analyze Recent Transactions"
  description: "Retrieve and analyze recent transactions across all connected accounts."
  expected_output: "Transaction summary with statistics and categorization."
  required_tools:
    - "get_transactions"
    - "categorize_transactions"
  dependencies:
    - "get_account_overview"
  agent: "financial_analyst"
  priority: "high"
  parameters:
    start_date: "30_days_ago"
    end_date: "today"
    count: 500
```

The tasks are organized into logical workflows that build upon each other:

1. Account connection and overview
2. Transaction analysis
3. Budget creation and analysis
4. Financial health assessment
5. Investment tracking and optimization

## API Usage

### How the Plaid API is Leveraged

The integration uses Plaid's API for all financial data operations, providing several advantages:

1. **Secure Access**: Plaid handles the secure connection to financial institutions
2. **Normalized Data**: Transactions and accounts are normalized across institutions
3. **Rich Metadata**: Enhanced transaction data with categories and merchant information
4. **Multi-Institution Support**: Connect to thousands of banks with a single integration

### API Endpoints Used

The integration primarily uses these Plaid API endpoints:

- `/link/token/create`: Create tokens for the Plaid Link flow
- `/item/public_token/exchange`: Exchange public tokens for access tokens
- `/accounts/get`: Retrieve account information
- `/accounts/balance/get`: Get real-time balance information
- `/identity/get`: Retrieve account owner information
- `/transactions/get`: Retrieve transaction history
- `/transactions/sync`: Efficiently sync transaction updates
- `/investments/holdings/get`: Retrieve investment holdings
- `/investments/transactions/get`: Retrieve investment transactions
- `/liabilities/get`: Retrieve loan and credit card information

### Example API Request

Here's an example of how the integration makes a request to the Plaid API to retrieve transactions:

```python
def get_transactions(
    access_token: str,
    start_date: str,
    end_date: str,
    account_ids: Optional[List[str]] = None,
    count: int = 100,
    offset: int = 0
) -> List[Transaction]:
    data = {
        "client_id": self.client_id,
        "secret": self.secret,
        "access_token": access_token,
        "start_date": start_date,
        "end_date": end_date,
        "options": {
            "count": count,
            "offset": offset
        }
    }
    
    if account_ids:
        data["options"]["account_ids"] = account_ids
    
    response = self._make_request("/transactions/get", data)
    
    # Process and return transactions...
```

## Common Workflows

### Financial Overview Workflow

1. **Create Link Token**: Generate a token for Plaid Link
2. **Exchange Public Token**: Get an access token after user authentication
3. **Get Account Overview**: Retrieve all accounts and balances
4. **Analyze Recent Transactions**: Get transaction history and categorize
5. **Assess Financial Health**: Evaluate overall financial health

Example code:

```python
# Step 1: Create Link token
link_token_result = create_link_token(
    client=plaid_client,
    input_data=AccountLinkInput(
        user_id="user123",
        client_name="RuTwin Financial Assistant"
    )
)

# After user completes Plaid Link flow and you receive public_token...

# Step 2: Exchange for access token
access_token_result = exchange_public_token(
    client=plaid_client,
    input_data=AccessTokenExchangeInput(
        public_token="public-sandbox-abc123"
    )
)

access_token = access_token_result["access_token"]

# Step 3: Get account overview
accounts_result = get_accounts(
    client=plaid_client,
    input_data=AccountsGetInput(
        access_token=access_token,
        include_balances=True
    )
)

# Step 4: Get and analyze transactions
transactions_result = get_transactions(
    client=plaid_client,
    input_data=TransactionsGetInput(
        access_token=access_token,
        start_date="2023-01-01",
        end_date="2023-01-31"
    )
)

# Step 5: Assess financial health
health_result = assess_financial_health(
    client=plaid_client,
    input_data=FinancialHealthAssessmentInput(
        balances=accounts_result["accounts"],
        transactions=transactions_result["transactions"]
    )
)

# Output financial health assessment
print(f"Financial Health Score: {health_result['overall_health']['score']}")
print(f"Status: {health_result['overall_health']['status']}")
for rec in health_result["recommendations"]:
    print(f"- {rec}")
```

### Budget Creation and Analysis Workflow

1. **Analyze Spending Patterns**: Understand historical spending by category
2. **Create Monthly Budget**: Set up budget based on spending patterns
3. **Identify Recurring Expenses**: Find subscriptions and regular bills
4. **Analyze Budget Performance**: Compare actual spending to budget
5. **Forecast Cash Flow**: Predict future account balances

### Investment Portfolio Optimization Workflow

1. **Track Investment Holdings**: Get current investment positions
2. **Analyze Investment Transactions**: Review trading activity
3. **Analyze Portfolio Performance**: Assess risk and return
4. **Optimize Asset Allocation**: Recommend portfolio adjustments

## Troubleshooting

### Common Issues and Solutions

| Issue | Possible Cause | Solution |
|-------|---------------|----------|
| Authentication errors | Invalid client ID or secret | Verify your Plaid API credentials in the `.env` file |
| "INVALID_ACCESS_TOKEN" error | Expired or revoked access token | Create a new Link token and have the user reconnect their account |
| "PRODUCT_NOT_READY" error | Requested data not yet available | Wait a few minutes and retry the request |
| Missing transactions | Transactions still pending | Some transactions may take 1-2 days to appear in the API |
| Institution connection errors | Institution downtime or maintenance | Check Plaid's status page and retry later |

### Debugging Tips

1. **Enable Detailed Logging**: Set the logging level to DEBUG to see API request and response details:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Use Sandbox Environment**: Test with Plaid's sandbox environment first, which provides predictable test data.

3. **Check Plaid Dashboard**: The Plaid Dashboard provides logs of API requests and institution connection status.

4. **Verify Item Status**: Use the `get_item` method to check the status of a connected institution:
   ```python
   item_info = plaid_client.get_item(access_token)
   print(f"Item status: {item_info.get('item', {}).get('status')}")
   ```

## Resources

### Documentation Links

- [Plaid API Documentation](https://plaid.com/docs/api/)
- [Plaid Link Documentation](https://plaid.com/docs/link/)
- [Plaid Products Overview](https://plaid.com/docs/api/products/)
- [Plaid API Errors](https://plaid.com/docs/errors/)
- [Plaid Status Page](https://status.plaid.com/)

### Tools and Utilities

- [Plaid Postman Collection](https://github.com/plaid/plaid-postman)
- [Plaid Quickstart](https://github.com/plaid/quickstart)
- [Plaid Pattern](https://github.com/plaid/pattern) - Sample end-to-end applications

### Support Channels

- [Plaid Help Center](https://support.plaid.com/)
- [Plaid Developer Forum](https://discuss.plaid.com/)
- [Plaid on Stack Overflow](https://stackoverflow.com/questions/tagged/plaid)

## Integration Maintenance

To keep the integration up-to-date:

1. **API Version Updates**: Plaid occasionally releases new API versions. Check the [changelog](https://plaid.com/docs/api/versioning/#changelog) for updates.

2. **New Products**: Plaid regularly adds new products and features. Review the [products page](https://plaid.com/products/) periodically.

3. **Security Best Practices**: Follow Plaid's [security recommendations](https://plaid.com/docs/security/) for handling user data and access tokens.

4. **Testing**: Regularly test the integration in the sandbox environment to ensure continued functionality.
