"""
Teller Tools for RuTwin Crew

This module provides tools for interacting with financial data via Teller API to perform
account management, transaction analysis, balance retrieval, and cash flow analysis.
"""

import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Union, Any, Tuple
from collections import defaultdict
import statistics

import pandas as pd
from pydantic import BaseModel, Field

from ru_twin.mcp.tools.teller import (
    TellerClient, Account, Transaction, Balance, 
    AccountType, AccountSubtype, TransactionType, TransactionStatus
)
from ru_twin.tools.tool_registry import ToolRegistry


# --- Account Management Models ---

class AccountsGetInput(BaseModel):
    """Input for getting account information"""
    include_balances: bool = Field(
        default=True,
        description="Whether to include balance information"
    )


class AccountDetailsInput(BaseModel):
    """Input for getting detailed account information"""
    account_id: str = Field(
        description="The account ID to retrieve details for"
    )
    include_balance: bool = Field(
        default=True,
        description="Whether to include balance information"
    )


class AccountSummaryInput(BaseModel):
    """Input for getting account summary"""
    group_by_type: bool = Field(
        default=True,
        description="Whether to group accounts by type"
    )


# --- Balance Retrieval Models ---

class AccountBalanceInput(BaseModel):
    """Input for getting account balance"""
    account_id: str = Field(
        description="The account ID to retrieve balance for"
    )


class BalanceSummaryInput(BaseModel):
    """Input for getting balance summary"""
    account_ids: Optional[List[str]] = Field(
        default=None,
        description="Optional list of account IDs to include (defaults to all accounts)"
    )


# --- Transaction Analysis Models ---

class TransactionsGetInput(BaseModel):
    """Input for getting transactions"""
    account_id: Optional[str] = Field(
        default=None,
        description="Optional account ID to filter by (defaults to all accounts)"
    )
    from_date: Optional[str] = Field(
        default=None,
        description="Start date in YYYY-MM-DD format"
    )
    to_date: Optional[str] = Field(
        default=None,
        description="End date in YYYY-MM-DD format"
    )
    count: Optional[int] = Field(
        default=None,
        description="Maximum number of transactions to return"
    )


class TransactionDetailsInput(BaseModel):
    """Input for getting transaction details"""
    account_id: str = Field(
        description="The account ID the transaction belongs to"
    )
    transaction_id: str = Field(
        description="The transaction ID to retrieve details for"
    )


class TransactionSearchInput(BaseModel):
    """Input for searching transactions"""
    transactions: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Optional list of transactions to search through (if not provided, will fetch transactions)"
    )
    query: str = Field(
        description="Search query (description text)"
    )
    min_amount: Optional[float] = Field(
        default=None,
        description="Minimum transaction amount"
    )
    max_amount: Optional[float] = Field(
        default=None,
        description="Maximum transaction amount"
    )
    from_date: Optional[str] = Field(
        default=None,
        description="Start date in YYYY-MM-DD format"
    )
    to_date: Optional[str] = Field(
        default=None,
        description="End date in YYYY-MM-DD format"
    )
    transaction_type: Optional[str] = Field(
        default=None,
        description="Type of transaction to filter by"
    )
    account_id: Optional[str] = Field(
        default=None,
        description="Optional account ID to filter by"
    )


class TransactionCategorizeInput(BaseModel):
    """Input for categorizing transactions"""
    transactions: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Optional list of transactions to categorize (if not provided, will fetch transactions)"
    )
    from_date: Optional[str] = Field(
        default=None,
        description="Start date in YYYY-MM-DD format for fetching transactions"
    )
    to_date: Optional[str] = Field(
        default=None,
        description="End date in YYYY-MM-DD format for fetching transactions"
    )


class SpendingAnalysisInput(BaseModel):
    """Input for spending analysis"""
    transactions: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Optional list of transactions to analyze (if not provided, will fetch transactions)"
    )
    from_date: Optional[str] = Field(
        default=None,
        description="Start date in YYYY-MM-DD format"
    )
    to_date: Optional[str] = Field(
        default=None,
        description="End date in YYYY-MM-DD format"
    )
    group_by: str = Field(
        default="type",
        description="How to group spending (type, date, description)"
    )
    account_id: Optional[str] = Field(
        default=None,
        description="Optional account ID to filter by"
    )


# --- Cash Flow Analysis Models ---

class CashFlowAnalysisInput(BaseModel):
    """Input for cash flow analysis"""
    transactions: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Optional list of transactions to analyze (if not provided, will fetch transactions)"
    )
    period_days: int = Field(
        default=30,
        description="Number of days to analyze"
    )
    account_id: Optional[str] = Field(
        default=None,
        description="Optional account ID to filter by"
    )


class RecurringTransactionsInput(BaseModel):
    """Input for identifying recurring transactions"""
    transactions: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Optional list of transactions to analyze (if not provided, will fetch transactions)"
    )
    min_occurrences: int = Field(
        default=2,
        description="Minimum number of occurrences to consider recurring"
    )
    amount_tolerance: float = Field(
        default=1.0,
        description="Amount variation tolerance (in dollars)"
    )
    days: int = Field(
        default=90,
        description="Number of days of transaction history to analyze"
    )
    account_id: Optional[str] = Field(
        default=None,
        description="Optional account ID to filter by"
    )


class CashFlowForecastInput(BaseModel):
    """Input for forecasting cash flow"""
    transactions: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Optional list of transactions to analyze (if not provided, will fetch transactions)"
    )
    account_balances: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Optional list of account balances (if not provided, will fetch balances)"
    )
    forecast_days: int = Field(
        default=30,
        description="Number of days to forecast"
    )
    include_recurring: bool = Field(
        default=True,
        description="Whether to include recurring transactions in forecast"
    )
    account_id: Optional[str] = Field(
        default=None,
        description="Optional account ID to filter by"
    )


# --- Tool Functions ---

# Account Management Tools

def get_accounts(
    client: TellerClient,
    input_data: AccountsGetInput
) -> Dict[str, Any]:
    """
    Get all accounts for the authenticated user.
    
    Args:
        client: TellerClient instance
        input_data: Configuration for getting accounts
        
    Returns:
        Dictionary containing account information
    """
    logging.info("Getting accounts")
    
    accounts = client.get_accounts()
    
    # Convert accounts to dictionaries
    account_data = [account.dict() for account in accounts]
    
    # Group accounts by type
    accounts_by_type = {}
    for account in accounts:
        account_type = account.type.value
        if account_type not in accounts_by_type:
            accounts_by_type[account_type] = []
        accounts_by_type[account_type].append(account.dict())
    
    result = {
        "accounts": account_data,
        "accounts_by_type": accounts_by_type,
        "total_accounts": len(accounts)
    }
    
    # Include balances if requested
    if input_data.include_balances:
        balances = client.get_balances()
        balance_data = [balance.dict() for balance in balances]
        
        # Create a lookup for balances
        balance_by_account = {b.account_id: b for b in balances}
        
        # Add balance to each account
        for account in account_data:
            account_id = account["id"]
            if account_id in balance_by_account:
                account["balance"] = balance_by_account[account_id].dict()
        
        result["balances"] = balance_data
    
    return result


def get_account_details(
    client: TellerClient,
    input_data: AccountDetailsInput
) -> Dict[str, Any]:
    """
    Get detailed information for a specific account.
    
    Args:
        client: TellerClient instance
        input_data: Configuration for getting account details
        
    Returns:
        Dictionary containing detailed account information
    """
    logging.info(f"Getting account details for: {input_data.account_id}")
    
    account = client.get_account(input_data.account_id)
    account_data = account.dict()
    
    result = {
        "account": account_data
    }
    
    # Include balance if requested
    if input_data.include_balance:
        try:
            balance = client.get_account_balance(input_data.account_id)
            result["balance"] = balance.dict()
        except Exception as e:
            logging.error(f"Error getting balance: {e}")
            result["balance_error"] = str(e)
    
    # Get recent transactions
    try:
        transactions = client.get_account_transactions(input_data.account_id, count=5)
        result["recent_transactions"] = [t.dict() for t in transactions]
    except Exception as e:
        logging.error(f"Error getting transactions: {e}")
        result["transactions_error"] = str(e)
    
    return result


def get_account_summary(
    client: TellerClient,
    input_data: AccountSummaryInput
) -> Dict[str, Any]:
    """
    Get a summary of all accounts.
    
    Args:
        client: TellerClient instance
        input_data: Configuration for getting account summary
        
    Returns:
        Dictionary containing account summary
    """
    logging.info("Getting account summary")
    
    summary = client.calculate_account_summary()
    
    if not input_data.group_by_type:
        # Remove grouping by type if not requested
        summary.pop("totals_by_type", None)
    
    return summary


# Balance Retrieval Tools

def get_account_balance(
    client: TellerClient,
    input_data: AccountBalanceInput
) -> Dict[str, Any]:
    """
    Get balance for a specific account.
    
    Args:
        client: TellerClient instance
        input_data: Configuration for getting account balance
        
    Returns:
        Dictionary containing account balance
    """
    logging.info(f"Getting balance for account: {input_data.account_id}")
    
    balance = client.get_account_balance(input_data.account_id)
    
    # Get account details for context
    account = client.get_account(input_data.account_id)
    
    return {
        "balance": balance.dict(),
        "account": {
            "id": account.id,
            "name": account.name,
            "type": account.type.value,
            "subtype": account.subtype.value,
            "institution": account.institution.get("name", "Unknown")
        },
        "retrieved_at": datetime.now().isoformat()
    }


def get_balance_summary(
    client: TellerClient,
    input_data: BalanceSummaryInput
) -> Dict[str, Any]:
    """
    Get a summary of balances for all accounts or specified accounts.
    
    Args:
        client: TellerClient instance
        input_data: Configuration for getting balance summary
        
    Returns:
        Dictionary containing balance summary
    """
    logging.info("Getting balance summary")
    
    # Get all accounts
    accounts = client.get_accounts()
    
    # Filter accounts if account_ids provided
    if input_data.account_ids:
        accounts = [a for a in accounts if a.id in input_data.account_ids]
    
    # Get balances for each account
    balances = []
    for account in accounts:
        try:
            balance = client.get_account_balance(account.id)
            balances.append(balance)
        except Exception as e:
            logging.error(f"Error getting balance for account {account.id}: {e}")
    
    # Calculate totals by account type
    totals_by_type = {}
    for account in accounts:
        account_type = account.type.value
        if account_type not in totals_by_type:
            totals_by_type[account_type] = {
                "count": 0,
                "ledger_total": 0.0,
                "available_total": 0.0
            }
        
        totals_by_type[account_type]["count"] += 1
        
        # Find balance for this account
        balance = next((b for b in balances if b.account_id == account.id), None)
        if balance:
            totals_by_type[account_type]["ledger_total"] += balance.ledger
            if balance.available is not None:
                totals_by_type[account_type]["available_total"] += balance.available
    
    # Calculate overall totals
    total_ledger = sum(b.ledger for b in balances)
    total_available = sum(b.available for b in balances if b.available is not None)
    
    return {
        "balances": [b.dict() for b in balances],
        "totals_by_type": totals_by_type,
        "total_ledger_balance": total_ledger,
        "total_available_balance": total_available,
        "accounts_count": len(accounts),
        "retrieved_at": datetime.now().isoformat()
    }


# Transaction Analysis Tools

def get_transactions(
    client: TellerClient,
    input_data: TransactionsGetInput
) -> Dict[str, Any]:
    """
    Get transactions for an account or all accounts.
    
    Args:
        client: TellerClient instance
        input_data: Configuration for getting transactions
        
    Returns:
        Dictionary containing transactions
    """
    logging.info("Getting transactions")
    
    if input_data.account_id:
        # Get transactions for specific account
        transactions = client.get_account_transactions(
            account_id=input_data.account_id,
            from_date=input_data.from_date,
            to_date=input_data.to_date,
            count=input_data.count
        )
    else:
        # Get transactions for all accounts
        transactions = client.get_transactions(
            from_date=input_data.from_date,
            to_date=input_data.to_date,
            count=input_data.count
        )
    
    # Convert transactions to dictionaries
    transaction_data = [transaction.dict() for transaction in transactions]
    
    # Calculate basic statistics
    total_amount = sum(t.amount for t in transactions)
    avg_transaction = total_amount / len(transactions) if transactions else 0
    
    # Count by status
    status_counts = {}
    for transaction in transactions:
        status = transaction.status.value
        if status not in status_counts:
            status_counts[status] = 0
        status_counts[status] += 1
    
    # Count by type
    type_counts = {}
    for transaction in transactions:
        if transaction.type:
            t_type = transaction.type.value
            if t_type not in type_counts:
                type_counts[t_type] = 0
            type_counts[t_type] += 1
    
    return {
        "transactions": transaction_data,
        "total_transactions": len(transactions),
        "total_amount": total_amount,
        "average_transaction": avg_transaction,
        "status_counts": status_counts,
        "type_counts": type_counts,
        "from_date": input_data.from_date,
        "to_date": input_data.to_date,
        "account_id": input_data.account_id
    }


def get_transaction_details(
    client: TellerClient,
    input_data: TransactionDetailsInput
) -> Dict[str, Any]:
    """
    Get detailed information for a specific transaction.
    
    Args:
        client: TellerClient instance
        input_data: Configuration for getting transaction details
        
    Returns:
        Dictionary containing detailed transaction information
    """
    logging.info(f"Getting transaction details for: {input_data.transaction_id}")
    
    transaction = client.get_transaction(
        account_id=input_data.account_id,
        transaction_id=input_data.transaction_id
    )
    
    # Get account details for context
    account = client.get_account(input_data.account_id)
    
    return {
        "transaction": transaction.dict(),
        "account": {
            "id": account.id,
            "name": account.name,
            "type": account.type.value,
            "subtype": account.subtype.value,
            "institution": account.institution.get("name", "Unknown")
        }
    }


def search_transactions(
    client: TellerClient,
    input_data: TransactionSearchInput
) -> Dict[str, Any]:
    """
    Search for transactions matching specific criteria.
    
    Args:
        client: TellerClient instance
        input_data: Search criteria
        
    Returns:
        Dictionary containing matching transactions
    """
    logging.info(f"Searching transactions with query: {input_data.query}")
    
    # Get transactions if not provided
    if input_data.transactions is None:
        if input_data.account_id:
            transactions = client.get_account_transactions(
                account_id=input_data.account_id,
                from_date=input_data.from_date,
                to_date=input_data.to_date
            )
        else:
            transactions = client.get_transactions(
                from_date=input_data.from_date,
                to_date=input_data.to_date
            )
    else:
        # Convert dictionary transactions to Transaction objects
        transactions = []
        for t_dict in input_data.transactions:
            transaction = Transaction(
                id=t_dict.get("id", ""),
                account_id=t_dict.get("account_id", ""),
                amount=t_dict.get("amount", 0.0),
                date=t_dict.get("date", ""),
                description=t_dict.get("description", ""),
                status=t_dict.get("status", "posted"),
                details=t_dict.get("details"),
                running_balance=t_dict.get("running_balance"),
                type=t_dict.get("type"),
                links=t_dict.get("links")
            )
            transactions.append(transaction)
    
    # Apply filters
    query_lower = input_data.query.lower()
    filtered_transactions = []
    
    for transaction in transactions:
        # Check text match in description
        if query_lower not in transaction.description.lower():
            continue
        
        # Check amount range
        if input_data.min_amount is not None and transaction.amount < input_data.min_amount:
            continue
        if input_data.max_amount is not None and transaction.amount > input_data.max_amount:
            continue
        
        # Check date range
        if input_data.from_date and transaction.date < input_data.from_date:
            continue
        if input_data.to_date and transaction.date > input_data.to_date:
            continue
        
        # Check transaction type
        if input_data.transaction_type and (not transaction.type or transaction.type.value != input_data.transaction_type):
            continue
        
        # Check account ID
        if input_data.account_id and transaction.account_id != input_data.account_id:
            continue
        
        filtered_transactions.append(transaction)
    
    # Prepare result
    result = {
        "matching_transactions": [t.dict() for t in filtered_transactions],
        "total_matches": len(filtered_transactions),
        "query": input_data.query,
        "filters": {
            "amount_range": {
                "min": input_data.min_amount,
                "max": input_data.max_amount
            },
            "date_range": {
                "from": input_data.from_date,
                "to": input_data.to_date
            },
            "transaction_type": input_data.transaction_type,
            "account_id": input_data.account_id
        }
    }
    
    return result


def categorize_transactions(
    client: TellerClient,
    input_data: TransactionCategorizeInput
) -> Dict[str, Any]:
    """
    Categorize transactions by type.
    
    Args:
        client: TellerClient instance
        input_data: Configuration for categorizing transactions
        
    Returns:
        Dictionary containing categorized transactions
    """
    logging.info("Categorizing transactions")
    
    # Get transactions if not provided
    if input_data.transactions is None:
        transactions = client.get_transactions(
            from_date=input_data.from_date,
            to_date=input_data.to_date
        )
    else:
        # Convert dictionary transactions to Transaction objects
        transactions = []
        for t_dict in input_data.transactions:
            transaction = Transaction(
                id=t_dict.get("id", ""),
                account_id=t_dict.get("account_id", ""),
                amount=t_dict.get("amount", 0.0),
                date=t_dict.get("date", ""),
                description=t_dict.get("description", ""),
                status=t_dict.get("status", "posted"),
                details=t_dict.get("details"),
                running_balance=t_dict.get("running_balance"),
                type=t_dict.get("type"),
                links=t_dict.get("links")
            )
            transactions.append(transaction)
    
    # Categorize transactions
    categorized = client.categorize_transactions(transactions)
    
    # Prepare result
    result = {}
    for category, category_transactions in categorized.items():
        result[category] = {
            "transactions": [t.dict() for t in category_transactions],
            "count": len(category_transactions),
            "total_amount": sum(t.amount for t in category_transactions)
        }
    
    # Calculate category distribution
    total_transactions = len(transactions)
    category_distribution = {
        category: len(category_transactions) / total_transactions * 100
        for category, category_transactions in categorized.items()
    }
    
    return {
        "categorized_transactions": result,
        "category_distribution": category_distribution,
        "total_categories": len(categorized),
        "total_transactions": total_transactions
    }


def analyze_spending(
    client: TellerClient,
    input_data: SpendingAnalysisInput
) -> Dict[str, Any]:
    """
    Analyze spending patterns.
    
    Args:
        client: TellerClient instance
        input_data: Configuration for spending analysis
        
    Returns:
        Dictionary containing spending analysis
    """
    logging.info(f"Analyzing spending patterns grouped by {input_data.group_by}")
    
    # Get transactions if not provided
    if input_data.transactions is None:
        if input_data.account_id:
            transactions = client.get_account_transactions(
                account_id=input_data.account_id,
                from_date=input_data.from_date,
                to_date=input_data.to_date
            )
        else:
            transactions = client.get_transactions(
                from_date=input_data.from_date,
                to_date=input_data.to_date
            )
    else:
        # Convert dictionary transactions to Transaction objects
        transactions = []
        for t_dict in input_data.transactions:
            transaction = Transaction(
                id=t_dict.get("id", ""),
                account_id=t_dict.get("account_id", ""),
                amount=t_dict.get("amount", 0.0),
                date=t_dict.get("date", ""),
                description=t_dict.get("description", ""),
                status=t_dict.get("status", "posted"),
                details=t_dict.get("details"),
                running_balance=t_dict.get("running_balance"),
                type=t_dict.get("type"),
                links=t_dict.get("links")
            )
            transactions.append(transaction)
    
    # Filter for spending only (positive amounts are debits/spending in Teller)
    spending_transactions = [t for t in transactions if t.amount > 0]
    
    # Group transactions based on specified grouping
    grouped_spending = {}
    
    if input_data.group_by == "type":
        # Group by transaction type
        for transaction in spending_transactions:
            t_type = transaction.type.value if transaction.type else "other"
            if t_type not in grouped_spending:
                grouped_spending[t_type] = {
                    "total": 0,
                    "count": 0,
                    "transactions": []
                }
            
            grouped_spending[t_type]["total"] += transaction.amount
            grouped_spending[t_type]["count"] += 1
            grouped_spending[t_type]["transactions"].append(transaction.dict())
        
        # Calculate averages
        for t_type, data in grouped_spending.items():
            data["average"] = data["total"] / data["count"] if data["count"] > 0 else 0
    
    elif input_data.group_by == "date":
        # Group by date
        for transaction in spending_transactions:
            date = transaction.date
            if date not in grouped_spending:
                grouped_spending[date] = {
                    "total": 0,
                    "count": 0,
                    "transactions": []
                }
            
            grouped_spending[date]["total"] += transaction.amount
            grouped_spending[date]["count"] += 1
            grouped_spending[date]["transactions"].append(transaction.dict())
        
        # Calculate averages
        for date, data in grouped_spending.items():
            data["average"] = data["total"] / data["count"] if data["count"] > 0 else 0
    
    elif input_data.group_by == "description":
        # Group by description
        for transaction in spending_transactions:
            description = transaction.description
            if description not in grouped_spending:
                grouped_spending[description] = {
                    "total": 0,
                    "count": 0,
                    "transactions": []
                }
            
            grouped_spending[description]["total"] += transaction.amount
            grouped_spending[description]["count"] += 1
            grouped_spending[description]["transactions"].append(transaction.dict())
        
        # Calculate averages
        for description, data in grouped_spending.items():
            data["average"] = data["total"] / data["count"] if data["count"] > 0 else 0
    
    # Calculate overall statistics
    total_spending = sum(t.amount for t in spending_transactions)
    avg_transaction = total_spending / len(spending_transactions) if spending_transactions else 0
    
    # Calculate spending distribution
    spending_distribution = {}
    for group, data in grouped_spending.items():
        spending_distribution[group] = (data["total"] / total_spending * 100) if total_spending > 0 else 0
    
    # Sort groups by total spending
    sorted_groups = sorted(grouped_spending.items(), key=lambda x: x[1]["total"], reverse=True)
    top_spending_groups = [{"name": group, "amount": data["total"]} for group, data in sorted_groups[:5]]
    
    return {
        "total_spending": total_spending,
        "average_transaction": avg_transaction,
        "transaction_count": len(spending_transactions),
        "grouped_by": input_data.group_by,
        "spending_groups": grouped_spending,
        "spending_distribution": spending_distribution,
        "top_spending_groups": top_spending_groups,
        "date_range": {
            "from": input_data.from_date,
            "to": input_data.to_date
        },
        "account_id": input_data.account_id,
        "analysis_date": datetime.now().isoformat()
    }


# Cash Flow Analysis Tools

def analyze_cash_flow(
    client: TellerClient,
    input_data: CashFlowAnalysisInput
) -> Dict[str, Any]:
    """
    Analyze cash flow from transactions.
    
    Args:
        client: TellerClient instance
        input_data: Configuration for cash flow analysis
        
    Returns:
        Dictionary containing cash flow analysis
    """
    logging.info(f"Analyzing cash flow for the past {input_data.period_days} days")
    
    # Get transactions if not provided
    if input_data.transactions is None:
        if input_data.account_id:
            transactions = client.get_account_transactions(
                account_id=input_data.account_id,
                from_date=(datetime.now() - timedelta(days=input_data.period_days)).strftime("%Y-%m-%d")
            )
        else:
            transactions = client.get_transactions(
                from_date=(datetime.now() - timedelta(days=input_data.period_days)).strftime("%Y-%m-%d")
            )
    else:
        # Convert dictionary transactions to Transaction objects
        transactions = []
        for t_dict in input_data.transactions:
            transaction = Transaction(
                id=t_dict.get("id", ""),
                account_id=t_dict.get("account_id", ""),
                amount=t_dict.get("amount", 0.0),
                date=t_dict.get("date", ""),
                description=t_dict.get("description", ""),
                status=t_dict.get("status", "posted"),
                details=t_dict.get("details"),
                running_balance=t_dict.get("running_balance"),
                type=t_dict.get("type"),
                links=t_dict.get("links")
            )
            transactions.append(transaction)
    
    # Use the client's cash flow analysis
    cash_flow = client.analyze_cash_flow(transactions, input_data.period_days)
    
    # Add additional insights
    
    # Calculate daily averages
    daily_inflow = cash_flow["inflows"] / input_data.period_days
    daily_outflow = cash_flow["outflows"] / input_data.period_days
    daily_net = cash_flow["net_cash_flow"] / input_data.period_days
    
    # Categorize cash flow
    if cash_flow["net_cash_flow"] > 0:
        cash_flow_status = "positive"
    elif cash_flow["net_cash_flow"] < 0:
        cash_flow_status = "negative"
    else:
        cash_flow_status = "neutral"
    
    # Calculate inflow to outflow ratio
    inflow_outflow_ratio = cash_flow["inflows"] / cash_flow["outflows"] if cash_flow["outflows"] > 0 else float('inf')
    
    # Add insights to result
    cash_flow["daily_averages"] = {
        "inflow": daily_inflow,
        "outflow": daily_outflow,
        "net": daily_net
    }
    
    cash_flow["insights"] = {
        "cash_flow_status": cash_flow_status,
        "inflow_outflow_ratio": inflow_outflow_ratio,
        "days_analyzed": input_data.period_days,
        "account_id": input_data.account_id,
        "analysis_date": datetime.now().isoformat()
    }
    
    return cash_flow


def identify_recurring_transactions(
    client: TellerClient,
    input_data: RecurringTransactionsInput
) -> Dict[str, Any]:
    """
    Identify recurring transactions from transaction history.
    
    Args:
        client: TellerClient instance
        input_data: Configuration for identifying recurring transactions
        
    Returns:
        Dictionary containing identified recurring transactions
    """
    logging.info(f"Identifying recurring transactions with minimum {input_data.min_occurrences} occurrences")
    
    # Get transactions if not provided
    if input_data.transactions is None:
        if input_data.account_id:
            transactions = client.get_account_transactions(
                account_id=input_data.account_id,
                from_date=(datetime.now() - timedelta(days=input_data.days)).strftime("%Y-%m-%d")
            )
        else:
            transactions = client.get_transactions(
                from_date=(datetime.now() - timedelta(days=input_data.days)).strftime("%Y-%m-%d")
            )
    else:
        # Convert dictionary transactions to Transaction objects
        transactions = []
        for t_dict in input_data.transactions:
            transaction = Transaction(
                id=t_dict.get("id", ""),
                account_id=t_dict.get("account_id", ""),
                amount=t_dict.get("amount", 0.0),
                date=t_dict.get("date", ""),
                description=t_dict.get("description", ""),
                status=t_dict.get("status", "posted"),
                details=t_dict.get("details"),
                running_balance=t_dict.get("running_balance"),
                type=t_dict.get("type"),
                links=t_dict.get("links")
            )
            transactions.append(transaction)
    
    # Group by description
    description_transactions = {}
    for transaction in transactions:
        description = transaction.description
        if description not in description_transactions:
            description_transactions[description] = []
        description_transactions[description].append(transaction)
    
    # Identify potential recurring transactions
    recurring_transactions = []
    
    for description, desc_transactions in description_transactions.items():
        # Skip if not enough occurrences
        if len(desc_transactions) < input_data.min_occurrences:
            continue
        
        # Group transactions by amount (within tolerance)
        amount_groups = defaultdict(list)
        
        for transaction in desc_transactions:
            # Find a group within tolerance
            grouped = False
            for amount_key in amount_groups.keys():
                if abs(transaction.amount - amount_key) <= input_data.amount_tolerance:
                    amount_groups[amount_key].append(transaction)
                    grouped = True
                    break
            
            # If no group found, create a new one
            if not grouped:
                amount_groups[transaction.amount].append(transaction)
        
        # Check each amount group for recurring patterns
        for amount, amount_txns in amount_groups.items():
            if len(amount_txns) < input_data.min_occurrences:
                continue
                
            # Sort transactions by date
            sorted_txns = sorted(amount_txns, key=lambda t: t.date)
            
            # Calculate intervals between transactions
            intervals = []
            for i in range(len(sorted_txns) - 1):
                date1 = datetime.strptime(sorted_txns[i].date, "%Y-%m-%d")
                date2 = datetime.strptime(sorted_txns[i+1].date, "%Y-%m-%d")
                interval = (date2 - date1).days
                intervals.append(interval)
            
            # Check if intervals are consistent (within 3 days)
            if intervals and max(intervals) - min(intervals) <= 3:
                avg_interval = sum(intervals) / len(intervals)
                
                # Determine frequency type
                frequency_type = "unknown"
                if 25 <= avg_interval <= 31:
                    frequency_type = "monthly"
                elif 13 <= avg_interval <= 16:
                    frequency_type = "biweekly"
                elif 6 <= avg_interval <= 8:
                    frequency_type = "weekly"
                elif 85 <= avg_interval <= 95:
                    frequency_type = "quarterly"
                elif 350 <= avg_interval <= 380:
                    frequency_type = "annual"
                
                # Calculate next expected date
                last_date = datetime.strptime(sorted_txns[-1].date, "%Y-%m-%d")
                next_date = last_date + timedelta(days=round(avg_interval))
                
                recurring_transactions.append({
                    "description": description,
                    "amount": amount,
                    "occurrences": len(amount_txns),
                    "average_interval_days": avg_interval,
                    "frequency_type": frequency_type,
                    "last_date": sorted_txns[-1].date,
                    "next_expected_date": next_date.strftime("%Y-%m-%d"),
                    "transaction_type": sorted_txns[0].type.value if sorted_txns[0].type else "unknown",
                    "transactions": [t.dict() for t in sorted_txns]
                })
    
    # Sort by amount (descending)
    recurring_transactions.sort(key=lambda x: x["amount"], reverse=True)
    
    # Separate income and expenses
    recurring_income = [t for t in recurring_transactions if t["amount"] < 0]
    recurring_expenses = [t for t in recurring_transactions if t["amount"] > 0]
    
    # Calculate totals
    total_recurring_income = sum(abs(t["amount"]) for t in recurring_income)
    total_recurring_expenses = sum(t["amount"] for t in recurring_expenses)
    
    # Group by frequency type
    grouped_by_frequency = {}
    for transaction in recurring_transactions:
        frequency = transaction["frequency_type"]
        if frequency not in grouped_by_frequency:
            grouped_by_frequency[frequency] = []
        grouped_by_frequency[frequency].append(transaction)
    
    return {
        "recurring_transactions": recurring_transactions,
        "recurring_income": recurring_income,
        "recurring_expenses": recurring_expenses,
        "total_recurring_income": total_recurring_income,
        "total_recurring_expenses": total_recurring_expenses,
        "grouped_by_frequency": grouped_by_frequency,
        "transaction_count": len(recurring_transactions),
        "analysis_period": {
            "days": input_data.days,
            "start_date": (datetime.now() - timedelta(days=input_data.days)).strftime("%Y-%m-%d"),
            "end_date": datetime.now().strftime("%Y-%m-%d")
        },
        "account_id": input_data.account_id,
        "analysis_date": datetime.now().isoformat()
    }


def forecast_cash_flow(
    client: TellerClient,
    input_data: CashFlowForecastInput
) -> Dict[str, Any]:
    """
    Forecast future cash flow based on historical transactions.
    
    Args:
        client: TellerClient instance
        input_data: Configuration for cash flow forecasting
        
    Returns:
        Dictionary containing cash flow forecast
    """
    logging.info(f"Forecasting cash flow for {input_data.forecast_days} days")
    
    # Get transactions if not provided
    if input_data.transactions is None:
        if input_data.account_id:
            transactions = client.get_account_transactions(
                account_id=input_data.account_id,
                from_date=(datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")  # Get 90 days of history
            )
        else:
            transactions = client.get_transactions(
                from_date=(datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")  # Get 90 days of history
            )
    else:
        # Convert dictionary transactions to Transaction objects
        transactions = []
        for t_dict in input_data.transactions:
            transaction = Transaction(
                id=t_dict.get("id", ""),
                account_id=t_dict.get("account_id", ""),
                amount=t_dict.get("amount", 0.0),
                date=t_dict.get("date", ""),
                description=t_dict.get("description", ""),
                status=t_dict.get("status", "posted"),
                details=t_dict.get("details"),
                running_balance=t_dict.get("running_balance"),
                type=t_dict.get("type"),
                links=t_dict.get("links")
            )
            transactions.append(transaction)
    
    # Get account balances if not provided
    if input_data.account_balances is None:
        if input_data.account_id:
            balances = [client.get_account_balance(input_data.account_id)]
        else:
            balances = client.get_balances()
    else:
        # Convert dictionary balances to Balance objects
        balances = []
        for b_dict in input_data.account_balances:
            balance = Balance(
                account_id=b_dict.get("account_id", ""),
                available=b_dict.get("available"),
                ledger=b_dict.get("ledger", 0.0),
                links=b_dict.get("links")
            )
            balances.append(balance)
    
    # Calculate starting balance
    if input_data.account_id:
        # Use specific account balance
        starting_balance = next((b.ledger for b in balances if b.account_id == input_data.account_id), 0)
    else:
        # Use sum of all account balances
        starting_balance = sum(b.ledger for b in balances)
    
    # Analyze historical cash flow
    # In Teller, negative amounts are typically credits (money in) and positive are debits (money out)
    inflows = sum(abs(t.amount) for t in transactions if t.amount < 0)
    outflows = sum(t.amount for t in transactions if t.amount > 0)
    
    # Calculate daily averages
    days_of_history = 90  # Assuming 90 days of transaction history
    daily_inflow = inflows / days_of_history
    daily_outflow = outflows / days_of_history
    daily_net = daily_inflow - daily_outflow
    
    # Identify recurring transactions if requested
    recurring_transactions = []
    if input_data.include_recurring:
        # Use the identify_recurring_transactions function
        recurring_result = identify_recurring_transactions(
            client,
            RecurringTransactionsInput(
                transactions=input_data.transactions,
                min_occurrences=2,
                amount_tolerance=1.0,
                days=90,
                account_id=input_data.account_id
            )
        )
        recurring_transactions = recurring_result.get("recurring_transactions", [])
    
    # Generate forecast
    forecast_start = datetime.now()
    forecast_end = forecast_start + timedelta(days=input_data.forecast_days)
    
    daily_forecast = []
    running_balance = starting_balance
    
    current_date = forecast_start
    while current_date <= forecast_end:
        date_str = current_date.strftime("%Y-%m-%d")
        
        # Start with daily average flow
        day_inflow = daily_inflow
        day_outflow = daily_outflow
        
        # Add recurring transactions for this day
        if input_data.include_recurring:
            for recurring in recurring_transactions:
                next_date = datetime.strptime(recurring["next_expected_date"], "%Y-%m-%d")
                interval = recurring["average_interval_days"]
                
                # Check if this recurring transaction occurs on the current date
                while next_date <= current_date:
                    next_date += timedelta(days=interval)
                
                if (next_date - current_date).days < 1:  # Transaction occurs today
                    if recurring["amount"] > 0:  # Expense
                        day_outflow += recurring["amount"]
                    else:  # Income
                        day_inflow += abs(recurring["amount"])
        
        # Update running balance
        day_net = day_inflow - day_outflow
        running_balance += day_net
        
        daily_forecast.append({
            "date": date_str,
            "inflow": day_inflow,
            "outflow": day_outflow,
            "net_flow": day_net,
            "balance": running_balance
        })
        
        current_date += timedelta(days=1)
    
    # Calculate summary statistics
    total_inflow = sum(day["inflow"] for day in daily_forecast)
    total_outflow = sum(day["outflow"] for day in daily_forecast)
    net_change = total_inflow - total_outflow
    ending_balance = starting_balance + net_change
    
    return {
        "starting_balance": starting_balance,
        "ending_balance": ending_balance,
        "forecast_period": {
            "start": forecast_start.strftime("%Y-%m-%d"),
            "end": forecast_end.strftime("%Y-%m-%d"),
            "days": input_data.forecast_days
        },
        "summary": {
            "total_inflow": total_inflow,
            "total_outflow": total_outflow,
            "net_change": net_change,
            "daily_average_net": net_change / input_data.forecast_days
        },
        "recurring_transactions": recurring_transactions if input_data.include_recurring else [],
        "daily_forecast": daily_forecast,
        "account_id": input_data.account_id,
        "forecast_generated_at": datetime.now().isoformat()
    }


# Register tools with the registry
def register_tools(registry: ToolRegistry) -> None:
    """Register all Teller tools with the tool registry."""
    
    # Account Management Tools
    registry.register_tool(
        "get_accounts",
        get_accounts,
        "Get all accounts for the authenticated user",
        AccountsGetInput
    )
    
    registry.register_tool(
        "get_account_details",
        get_account_details,
        "Get detailed information for a specific account",
        AccountDetailsInput
    )
    
    registry.register_tool(
        "get_account_summary",
        get_account_summary,
        "Get a summary of all accounts",
        AccountSummaryInput
    )
    
    # Balance Retrieval Tools
    registry.register_tool(
        "get_account_balance",
        get_account_balance,
        "Get balance for a specific account",
        AccountBalanceInput
    )
    
    registry.register_tool(
        "get_balance_summary",
        get_balance_summary,
        "Get a summary of balances for all accounts or specified accounts",
        BalanceSummaryInput
    )
    
    # Transaction Analysis Tools
    registry.register_tool(
        "get_transactions",
        get_transactions,
        "Get transactions for an account or all accounts",
        TransactionsGetInput
    )
    
    registry.register_tool(
        "get_transaction_details",
        get_transaction_details,
        "Get detailed information for a specific transaction",
        TransactionDetailsInput
    )
    
    registry.register_tool(
        "search_transactions",
        search_transactions,
        "Search for transactions matching specific criteria",
        TransactionSearchInput
    )
    
    registry.register_tool(
        "categorize_transactions",
        categorize_transactions,
        "Categorize transactions by type",
        TransactionCategorizeInput
    )
    
    registry.register_tool(
        "analyze_spending",
        analyze_spending,
        "Analyze spending patterns",
        SpendingAnalysisInput
    )
    
    # Cash Flow Analysis Tools
    registry.register_tool(
        "analyze_cash_flow",
        analyze_cash_flow,
        "Analyze cash flow from transactions",
        CashFlowAnalysisInput
    )
    
    registry.register_tool(
        "identify_recurring_transactions",
        identify_recurring_transactions,
        "Identify recurring transactions from transaction history",
        RecurringTransactionsInput
    )
    
    registry.register_tool(
        "forecast_cash_flow",
        forecast_cash_flow,
        "Forecast future cash flow based on historical transactions",
        CashFlowForecastInput
    )
