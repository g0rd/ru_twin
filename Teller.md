# Teller Integration for RuTwin Crew

This document provides comprehensive guidance for using the Teller integration with RuTwin Crew. The integration leverages Teller's REST API to enable account management, transaction analysis, balance retrieval, and cash flow analysis.

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

The Teller integration for RuTwin Crew provides a set of tools and tasks that allow AI agents to interact with financial data. The integration is built around four main functional areas:

1. **Account Management**: Retrieve account information and generate account summaries.
2. **Balance Retrieval**: Access real-time balance information for accounts.
3. **Transaction Analysis**: Retrieve, search, categorize, and analyze transaction data.
4. **Cash Flow Analysis**: Analyze cash flow patterns, identify recurring transactions, and forecast future cash flows.

All functionality is implemented using Teller's REST API, providing secure access to financial data across various financial institutions.

## Setup Instructions

### Prerequisites

- Teller access token (obtained through Teller Connect)
- Understanding of Teller's authentication model
- Knowledge of the accounts you want to access

### Environment Variables

Add the following variables to your `.env` file:

```
TELLER_ACCESS_TOKEN=your_access_token
TELLER_ENVIRONMENT=sandbox  # or production
```

### Installation Steps

1. Ensure the Teller client is properly imported in your application:

```python
# In your application initialization
from ru_twin.mcp_clients.teller import TellerClient
from ru_twin.tools.teller_tools import register_tools
```

2. Initialize the Teller client:

```python
# Initialize the client with credentials from environment variables
import os
from dotenv import load_dotenv

load_dotenv()

teller_client = TellerClient(
    access_token=os.getenv("TELLER_ACCESS_TOKEN"),
    environment=os.getenv("TELLER_ENVIRONMENT", "sandbox")
)
```

3. Register the Teller tools with your tool registry:

```python
from ru_twin.tools.tool_registry import ToolRegistry
from ru_twin.tools.teller_tools import register_tools

# Initialize your tool registry
tool_registry = ToolRegistry()

# Register Teller tools
register_tools(tool_registry)
```

4. Import the Teller tasks in your main tasks configuration:

```yaml
# In your main tasks.yaml file
imports:
  - src/ru_twin/config/teller_tasks.yaml

# Your other tasks...
```

## Configuration

### Teller Environments

Teller offers two environments:

1. **Sandbox**: For testing with mock data
2. **Production**: For production use with real financial data

Choose the appropriate environment based on your development stage.

### Authentication

Teller uses a simple authentication model with access tokens. These tokens are obtained through Teller Connect when a user successfully connects a bank account to your Teller application.

The access token is included in the `Authorization` header of each API request:

```
Authorization: Bearer your_access_token
```

### Rate Limiting

The Teller client implements rate limiting protection to ensure your application stays within Teller's API limits. The client will automatically handle rate limiting by:

1. Maintaining a minimum interval between requests
2. Implementing exponential backoff for retries
3. Properly handling 429 (Too Many Requests) responses

You can adjust rate limiting parameters in the TellerClient initialization:

```python
teller_client = TellerClient(
    # ... other parameters
    max_retries=5,
    retry_delay=1.0,
    min_request_interval=0.5
)
```

## Available Tools

### Account Management Tools

| Tool Name | Description | Input Parameters |
|-----------|-------------|------------------|
| `get_accounts` | Get all accounts for the authenticated user | `include_balances` |
| `get_account_details` | Get detailed information for a specific account | `account_id`, `include_balance` |
| `get_account_summary` | Get a summary of all accounts | `group_by_type` |

### Balance Retrieval Tools

| Tool Name | Description | Input Parameters |
|-----------|-------------|------------------|
| `get_account_balance` | Get balance for a specific account | `account_id` |
| `get_balance_summary` | Get a summary of balances for all accounts | `account_ids` |

### Transaction Analysis Tools

| Tool Name | Description | Input Parameters |
|-----------|-------------|------------------|
| `get_transactions` | Get transactions for an account or all accounts | `account_id`, `from_date`, `to_date`, `count` |
| `get_transaction_details` | Get detailed information for a specific transaction | `account_id`, `transaction_id` |
| `search_transactions` | Search for transactions matching criteria | `query`, `min_amount`, `max_amount`, `from_date`, `to_date`, `transaction_type`, `account_id` |
| `categorize_transactions` | Categorize transactions by type | `transactions`, `from_date`, `to_date` |
| `analyze_spending` | Analyze spending patterns | `transactions`, `from_date`, `to_date`, `group_by`, `account_id` |

### Cash Flow Analysis Tools

| Tool Name | Description | Input Parameters |
|-----------|-------------|------------------|
| `analyze_cash_flow` | Analyze cash flow from transactions | `transactions`, `period_days`, `account_id` |
| `identify_recurring_transactions` | Identify recurring transactions | `transactions`, `min_occurrences`, `amount_tolerance`, `days`, `account_id` |
| `forecast_cash_flow` | Forecast future cash flow | `transactions`, `account_balances`, `forecast_days`, `include_recurring`, `account_id` |

## Task Definitions

The Teller integration includes pre-defined tasks in `src/ru_twin/config/teller_tasks.yaml`. These tasks are configured to work with the CrewAI framework and can be assigned to specific agents.

Example task definition:

```yaml
get_recent_transactions:
  name: "Get Recent Transactions"
  description: "Retrieve recent transactions across all accounts or for a specific account."
  expected_output: "List of recent transactions with amounts, dates, and descriptions."
  required_tools:
    - "get_transactions"
  dependencies:
    - "get_account_overview"
  agent: "financial_assistant"
  priority: "high"
  parameters:
    account_id: null  # null means all accounts
    from_date: "30_days_ago"
    to_date: "today"
    count: 100
```

The tasks are organized into logical workflows that build upon each other:

1. Account and balance retrieval
2. Transaction analysis
3. Cash flow analysis and forecasting
4. Financial reporting and insights

## API Usage

### How the Teller API is Leveraged

The integration uses Teller's REST API for all financial data operations, providing several advantages:

1. **Simplified Authentication**: Simple token-based authentication model
2. **Consistent Data Format**: Uniform JSON responses across endpoints
3. **Comprehensive Account Data**: Access to accounts, balances, and transactions
4. **Multi-Institution Support**: Connect to multiple financial institutions with a single integration

### API Endpoints Used

The integration primarily uses these Teller API endpoints:

- `/accounts`: Retrieve all accounts
- `/accounts/{id}`: Retrieve a specific account
- `/accounts/{id}/balance`: Get balance for a specific account
- `/accounts/{id}/transactions`: Get transactions for a specific account
- `/accounts/{id}/transactions/{id}`: Get a specific transaction

### Example API Request

Here's an example of how the integration makes a request to the Teller API to retrieve transactions:

```python
def get_account_transactions(
    account_id: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    count: Optional[int] = None
) -> List[Transaction]:
    endpoint = f"/accounts/{account_id}/transactions"
    params = []
    
    if from_date:
        params.append(f"from_id={from_date}")
    if to_date:
        params.append(f"to_id={to_date}")
    if count:
        params.append(f"count={count}")
    
    if params:
        endpoint += "?" + "&".join(params)
    
    response = self._make_request(endpoint)
    
    # Process and return transactions...
```

## Common Workflows

### Financial Overview Workflow

1. **Get Account Overview**: Retrieve all accounts and their details
2. **Get Balance Summary**: Get balances across all accounts
3. **Get Recent Transactions**: Retrieve recent transaction history
4. **Analyze Spending**: Analyze spending patterns by category
5. **Analyze Cash Flow**: Evaluate inflows and outflows

Example code:

```python
# Step 1: Get account overview
accounts_result = get_accounts(
    client=teller_client,
    input_data=AccountsGetInput(
        include_balances=True
    )
)

# Step 2: Get balance summary
balance_summary = get_balance_summary(
    client=teller_client,
    input_data=BalanceSummaryInput()
)

# Step 3: Get recent transactions
transactions_result = get_transactions(
    client=teller_client,
    input_data=TransactionsGetInput(
        from_date="2023-04-01",
        to_date="2023-04-30"
    )
)

# Step 4: Analyze spending
spending_analysis = analyze_spending(
    client=teller_client,
    input_data=SpendingAnalysisInput(
        transactions=transactions_result["transactions"],
        group_by="type"
    )
)

# Step 5: Analyze cash flow
cash_flow_analysis = analyze_cash_flow(
    client=teller_client,
    input_data=CashFlowAnalysisInput(
        transactions=transactions_result["transactions"],
        period_days=30
    )
)

# Output financial overview
print(f"Total Accounts: {accounts_result['total_accounts']}")
print(f"Total Balance: ${balance_summary['total_ledger_balance']:.2f}")
print(f"Top Spending Category: {spending_analysis['top_spending_groups'][0]['name']}")
print(f"Net Cash Flow: ${cash_flow_analysis['net_cash_flow']:.2f}")
```

### Cash Flow Forecasting Workflow

1. **Get Recent Transactions**: Retrieve transaction history
2. **Identify Recurring Transactions**: Find regular income and expenses
3. **Get Current Balances**: Establish starting point for forecast
4. **Forecast Cash Flow**: Predict future account balances

### Transaction Search and Analysis Workflow

1. **Get Transactions**: Retrieve transaction history
2. **Search Transactions**: Find specific transactions
3. **Categorize Transactions**: Group transactions by type
4. **Analyze Spending**: Identify spending patterns

## Troubleshooting

### Common Issues and Solutions

| Issue | Possible Cause | Solution |
|-------|---------------|----------|
| Authentication errors | Invalid or expired access token | Obtain a new access token through Teller Connect |
| "Account not found" error | Incorrect account ID | Verify the account ID using the get_accounts tool |
| Missing transactions | Date range issues | Ensure from_date and to_date are in YYYY-MM-DD format |
| Rate limiting errors | Too many requests | Reduce request frequency or implement caching |
| Empty response | No data available | Verify the account has transaction history in the specified date range |

### Debugging Tips

1. **Enable Detailed Logging**: Set the logging level to DEBUG to see API request and response details:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Check Response Status Codes**: The Teller client logs HTTP status codes which can help identify issues.

3. **Verify Account Access**: Ensure the access token has permission to access the requested accounts.

4. **Test with Sandbox First**: Use the sandbox environment to test your integration before moving to production.

### Error Handling

The Teller client includes comprehensive error handling:

1. **Automatic Retries**: The client will automatically retry failed requests with exponential backoff.
2. **Rate Limit Handling**: 429 responses are handled with appropriate waiting periods.
3. **Error Classification**: Errors are categorized and logged for easier debugging.

## Resources

### Documentation Links

- [Teller API Reference](https://teller.io/docs/api)
- [Teller Connect Guide](https://teller.io/docs/guides/connect)
- [Teller 
