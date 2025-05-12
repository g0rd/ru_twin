"""
Finance Tools for RuTwin Crew

This module provides tools for interacting with financial data via Plaid API to perform
account management, transaction analysis, budget planning, financial health assessment,
and investment tracking.
"""

import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Union, Any, Tuple

import pandas as pd
from pydantic import BaseModel, Field

from ru_twin.mcp_clients.plaid import (
    PlaidClient, Account, Transaction, Balance, 
    Identity, Investment, Liability, AccountType
)
from ru_twin.tools.tool_registry import ToolRegistry


# --- Account Management Models ---

class AccountLinkInput(BaseModel):
    """Input for account linking tools"""
    user_id: str = Field(
        description="Client-generated ID for the user"
    )
    client_name: str = Field(
        description="Name of your application"
    )
    products: List[str] = Field(
        default=["transactions", "auth", "identity"],
        description="List of Plaid products to use"
    )
    country_codes: List[str] = Field(
        default=["US"],
        description="List of country codes"
    )
    language: str = Field(
        default="en",
        description="Language to display Link in"
    )
    webhook: Optional[str] = Field(
        default=None,
        description="Webhook URL for notifications"
    )


class AccessTokenExchangeInput(BaseModel):
    """Input for exchanging public token for access token"""
    public_token: str = Field(
        description="The public token from Plaid Link"
    )


class AccountsGetInput(BaseModel):
    """Input for getting account information"""
    access_token: str = Field(
        description="The Plaid access token"
    )
    include_balances: bool = Field(
        default=True,
        description="Whether to include balance information"
    )


class AccountBalancesInput(BaseModel):
    """Input for getting account balances"""
    access_token: str = Field(
        description="The Plaid access token"
    )
    account_ids: Optional[List[str]] = Field(
        default=None,
        description="Optional list of account IDs to filter by"
    )


class AccountIdentityInput(BaseModel):
    """Input for getting account identity information"""
    access_token: str = Field(
        description="The Plaid access token"
    )


# --- Transaction Analysis Models ---

class TransactionsGetInput(BaseModel):
    """Input for getting transactions"""
    access_token: str = Field(
        description="The Plaid access token"
    )
    start_date: str = Field(
        description="Start date in YYYY-MM-DD format"
    )
    end_date: str = Field(
        description="End date in YYYY-MM-DD format"
    )
    account_ids: Optional[List[str]] = Field(
        default=None,
        description="Optional list of account IDs to filter by"
    )
    count: int = Field(
        default=100,
        description="Maximum number of transactions to return"
    )
    offset: int = Field(
        default=0,
        description="Number of transactions to skip"
    )


class TransactionCategorizeInput(BaseModel):
    """Input for categorizing transactions"""
    transactions: List[Dict[str, Any]] = Field(
        description="List of transactions to categorize"
    )


class TransactionSearchInput(BaseModel):
    """Input for searching transactions"""
    transactions: List[Dict[str, Any]] = Field(
        description="List of transactions to search through"
    )
    query: str = Field(
        description="Search query (merchant name, description, etc.)"
    )
    min_amount: Optional[float] = Field(
        default=None,
        description="Minimum transaction amount"
    )
    max_amount: Optional[float] = Field(
        default=None,
        description="Maximum transaction amount"
    )
    start_date: Optional[str] = Field(
        default=None,
        description="Start date in YYYY-MM-DD format"
    )
    end_date: Optional[str] = Field(
        default=None,
        description="End date in YYYY-MM-DD format"
    )


class TransactionEnrichInput(BaseModel):
    """Input for enriching transaction data"""
    transactions: List[Dict[str, Any]] = Field(
        description="List of transactions to enrich"
    )


# --- Budget Planning Models ---

class BudgetCreateInput(BaseModel):
    """Input for creating a budget"""
    name: str = Field(
        description="Budget name"
    )
    period: str = Field(
        default="monthly",
        description="Budget period (weekly, monthly, yearly)"
    )
    categories: Dict[str, float] = Field(
        description="Dictionary mapping categories to budget amounts"
    )
    start_date: str = Field(
        description="Start date in YYYY-MM-DD format"
    )
    end_date: Optional[str] = Field(
        default=None,
        description="End date in YYYY-MM-DD format"
    )


class BudgetAnalysisInput(BaseModel):
    """Input for analyzing budget performance"""
    budget: Dict[str, Any] = Field(
        description="Budget definition"
    )
    transactions: List[Dict[str, Any]] = Field(
        description="List of transactions to analyze against the budget"
    )


class CashFlowForecastInput(BaseModel):
    """Input for forecasting cash flow"""
    transactions: List[Dict[str, Any]] = Field(
        description="Historical transactions"
    )
    account_balances: List[Dict[str, Any]] = Field(
        description="Current account balances"
    )
    forecast_days: int = Field(
        default=90,
        description="Number of days to forecast"
    )
    include_recurring: bool = Field(
        default=True,
        description="Whether to include recurring transactions in forecast"
    )


# --- Income Verification Models ---

class IncomeVerificationInput(BaseModel):
    """Input for income verification"""
    access_token: str = Field(
        description="The Plaid access token"
    )
    account_ids: Optional[List[str]] = Field(
        default=None,
        description="Optional list of account IDs to filter by"
    )
    months: int = Field(
        default=3,
        description="Number of months of data to analyze"
    )


class IncomeAnalysisInput(BaseModel):
    """Input for analyzing income patterns"""
    transactions: List[Dict[str, Any]] = Field(
        description="List of transactions to analyze"
    )
    months: int = Field(
        default=6,
        description="Number of months of data to analyze"
    )


# --- Financial Health Models ---

class FinancialHealthAssessmentInput(BaseModel):
    """Input for financial health assessment"""
    balances: List[Dict[str, Any]] = Field(
        description="Account balances"
    )
    transactions: List[Dict[str, Any]] = Field(
        description="Recent transactions"
    )
    liabilities: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Optional liability information"
    )


class DebtAnalysisInput(BaseModel):
    """Input for debt analysis"""
    liabilities: List[Dict[str, Any]] = Field(
        description="Liability information"
    )
    income: float = Field(
        description="Monthly income"
    )


class SavingsGoalInput(BaseModel):
    """Input for savings goal planning"""
    goal_amount: float = Field(
        description="Target savings amount"
    )
    current_savings: float = Field(
        description="Current savings amount"
    )
    monthly_contribution: float = Field(
        description="Monthly contribution amount"
    )
    interest_rate: float = Field(
        default=0.0,
        description="Annual interest rate (as decimal)"
    )


# --- Spending Analysis Models ---

class SpendingAnalysisInput(BaseModel):
    """Input for spending analysis"""
    transactions: List[Dict[str, Any]] = Field(
        description="List of transactions to analyze"
    )
    start_date: Optional[str] = Field(
        default=None,
        description="Start date in YYYY-MM-DD format"
    )
    end_date: Optional[str] = Field(
        default=None,
        description="End date in YYYY-MM-DD format"
    )
    group_by: str = Field(
        default="category",
        description="How to group spending (category, month, merchant)"
    )


class MerchantAnalysisInput(BaseModel):
    """Input for merchant analysis"""
    transactions: List[Dict[str, Any]] = Field(
        description="List of transactions to analyze"
    )
    months: int = Field(
        default=3,
        description="Number of months of data to analyze"
    )


class RecurringExpensesInput(BaseModel):
    """Input for identifying recurring expenses"""
    transactions: List[Dict[str, Any]] = Field(
        description="List of transactions to analyze"
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


# --- Investment Tracking Models ---

class InvestmentHoldingsInput(BaseModel):
    """Input for getting investment holdings"""
    access_token: str = Field(
        description="The Plaid access token"
    )


class InvestmentTransactionsInput(BaseModel):
    """Input for getting investment transactions"""
    access_token: str = Field(
        description="The Plaid access token"
    )
    start_date: str = Field(
        description="Start date in YYYY-MM-DD format"
    )
    end_date: str = Field(
        description="End date in YYYY-MM-DD format"
    )


class PortfolioAnalysisInput(BaseModel):
    """Input for portfolio analysis"""
    holdings: List[Dict[str, Any]] = Field(
        description="Investment holdings"
    )
    risk_tolerance: str = Field(
        default="moderate",
        description="Risk tolerance (conservative, moderate, aggressive)"
    )


class AssetAllocationInput(BaseModel):
    """Input for asset allocation analysis"""
    holdings: List[Dict[str, Any]] = Field(
        description="Investment holdings"
    )
    target_allocation: Optional[Dict[str, float]] = Field(
        default=None,
        description="Optional target allocation percentages by asset class"
    )


# --- Tool Functions ---

# Account Management Tools

def create_link_token(
    client: PlaidClient,
    input_data: AccountLinkInput
) -> Dict[str, Any]:
    """
    Create a Link token for initializing Plaid Link.
    
    Args:
        client: PlaidClient instance
        input_data: Configuration for the link token
        
    Returns:
        Dictionary containing the link_token
    """
    logging.info(f"Creating link token for user: {input_data.user_id}")
    
    result = client.create_link_token(
        user_id=input_data.user_id,
        client_name=input_data.client_name,
        products=input_data.products,
        country_codes=input_data.country_codes,
        language=input_data.language,
        webhook=input_data.webhook
    )
    
    return {
        "link_token": result.get("link_token"),
        "expiration": result.get("expiration"),
        "request_id": result.get("request_id")
    }


def exchange_public_token(
    client: PlaidClient,
    input_data: AccessTokenExchangeInput
) -> Dict[str, Any]:
    """
    Exchange a public token from Link for an access token.
    
    Args:
        client: PlaidClient instance
        input_data: Public token information
        
    Returns:
        Dictionary containing access_token and item_id
    """
    logging.info("Exchanging public token for access token")
    
    result = client.exchange_public_token(input_data.public_token)
    
    return {
        "access_token": result.get("access_token"),
        "item_id": result.get("item_id"),
        "request_id": result.get("request_id")
    }


def get_accounts(
    client: PlaidClient,
    input_data: AccountsGetInput
) -> Dict[str, Any]:
    """
    Get accounts for a specific access token.
    
    Args:
        client: PlaidClient instance
        input_data: Configuration for getting accounts
        
    Returns:
        Dictionary containing account information
    """
    logging.info(f"Getting accounts for access token: {input_data.access_token[:10]}...")
    
    accounts = client.get_accounts(input_data.access_token)
    
    # Convert accounts to dictionaries
    account_data = [account.dict() for account in accounts]
    
    # Group accounts by type
    accounts_by_type = {}
    for account in accounts:
        account_type = account.type
        if account_type not in accounts_by_type:
            accounts_by_type[account_type] = []
        accounts_by_type[account_type].append(account.dict())
    
    # Get item information
    item_info = client.get_item(input_data.access_token)
    
    return {
        "accounts": account_data,
        "accounts_by_type": accounts_by_type,
        "item": item_info.get("item", {}),
        "institution_id": item_info.get("item", {}).get("institution_id"),
        "request_id": item_info.get("request_id")
    }


def get_account_balances(
    client: PlaidClient,
    input_data: AccountBalancesInput
) -> Dict[str, Any]:
    """
    Get balances for accounts.
    
    Args:
        client: PlaidClient instance
        input_data: Configuration for getting balances
        
    Returns:
        Dictionary containing balance information
    """
    logging.info(f"Getting balances for access token: {input_data.access_token[:10]}...")
    
    balances = client.get_balances(
        access_token=input_data.access_token,
        account_ids=input_data.account_ids
    )
    
    # Convert balances to dictionaries
    balance_data = [balance.dict() for balance in balances]
    
    # Calculate totals by account type
    totals_by_type = {}
    for balance in balances:
        account_info = next((a for a in client.get_accounts(input_data.access_token) 
                             if a.account_id == balance.account_id), None)
        
        if account_info:
            account_type = account_info.type
            if account_type not in totals_by_type:
                totals_by_type[account_type] = 0
            totals_by_type[account_type] += balance.current
    
    # Calculate overall totals
    total_balance = sum(balance.current for balance in balances)
    total_available = sum(balance.available or balance.current for balance in balances)
    
    return {
        "balances": balance_data,
        "totals_by_type": totals_by_type,
        "total_balance": total_balance,
        "total_available": total_available,
        "last_updated": datetime.now().isoformat()
    }


def get_account_identity(
    client: PlaidClient,
    input_data: AccountIdentityInput
) -> Dict[str, Any]:
    """
    Get identity information for accounts.
    
    Args:
        client: PlaidClient instance
        input_data: Configuration for getting identity information
        
    Returns:
        Dictionary containing identity information
    """
    logging.info(f"Getting identity information for access token: {input_data.access_token[:10]}...")
    
    identities = client.get_identity(input_data.access_token)
    
    # Convert identities to dictionaries
    identity_data = [identity.dict() for identity in identities]
    
    # Extract primary identity information
    primary_identity = {}
    if identity_data:
        first_identity = identity_data[0]
        primary_identity = {
            "names": first_identity.get("names", []),
            "primary_name": first_identity.get("names", [""])[0] if first_identity.get("names") else "",
            "emails": first_identity.get("emails", []),
            "primary_email": first_identity.get("emails", [{}])[0].get("data", "") if first_identity.get("emails") else "",
            "phone_numbers": first_identity.get("phone_numbers", []),
            "primary_phone": first_identity.get("phone_numbers", [{}])[0].get("data", "") if first_identity.get("phone_numbers") else "",
            "addresses": first_identity.get("addresses", []),
            "primary_address": first_identity.get("addresses", [{}])[0] if first_identity.get("addresses") else {}
        }
    
    return {
        "identities": identity_data,
        "primary_identity": primary_identity,
        "accounts": [identity.get("account_id") for identity in identity_data]
    }


# Transaction Analysis Tools

def get_transactions(
    client: PlaidClient,
    input_data: TransactionsGetInput
) -> Dict[str, Any]:
    """
    Get transactions for accounts.
    
    Args:
        client: PlaidClient instance
        input_data: Configuration for getting transactions
        
    Returns:
        Dictionary containing transaction information
    """
    logging.info(f"Getting transactions from {input_data.start_date} to {input_data.end_date}")
    
    transactions = client.get_transactions(
        access_token=input_data.access_token,
        start_date=input_data.start_date,
        end_date=input_data.end_date,
        account_ids=input_data.account_ids,
        count=input_data.count,
        offset=input_data.offset
    )
    
    # Convert transactions to dictionaries
    transaction_data = [transaction.dict() for transaction in transactions]
    
    # Calculate basic statistics
    total_amount = sum(t.amount for t in transactions)
    avg_transaction = total_amount / len(transactions) if transactions else 0
    
    # Get date range information
    date_format = "%Y-%m-%d"
    start_date = datetime.strptime(input_data.start_date, date_format)
    end_date = datetime.strptime(input_data.end_date, date_format)
    days_in_range = (end_date - start_date).days + 1
    
    return {
        "transactions": transaction_data,
        "total_transactions": len(transactions),
        "total_amount": total_amount,
        "average_transaction": avg_transaction,
        "days_in_range": days_in_range,
        "daily_average": total_amount / days_in_range if days_in_range > 0 else 0,
        "start_date": input_data.start_date,
        "end_date": input_data.end_date
    }


def categorize_transactions(
    client: PlaidClient,
    input_data: TransactionCategorizeInput
) -> Dict[str, Any]:
    """
    Categorize a list of transactions.
    
    Args:
        client: PlaidClient instance
        input_data: Transactions to categorize
        
    Returns:
        Dictionary containing categorized transactions
    """
    logging.info(f"Categorizing {len(input_data.transactions)} transactions")
    
    # Convert dictionary transactions to Transaction objects
    transactions = []
    for t_dict in input_data.transactions:
        transaction = Transaction(
            transaction_id=t_dict.get("transaction_id", ""),
            account_id=t_dict.get("account_id", ""),
            amount=t_dict.get("amount", 0.0),
            date=t_dict.get("date", ""),
            name=t_dict.get("name", ""),
            merchant_name=t_dict.get("merchant_name"),
            pending=t_dict.get("pending", False),
            category=t_dict.get("category"),
            category_id=t_dict.get("category_id"),
            location=t_dict.get("location"),
            payment_channel=t_dict.get("payment_channel"),
            authorized_date=t_dict.get("authorized_date"),
            payment_meta=t_dict.get("payment_meta"),
            logo_url=t_dict.get("logo_url"),
            website=t_dict.get("website")
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
        "uncategorized_count": len(categorized.get("Uncategorized", [])),
        "total_transactions": total_transactions
    }


def search_transactions(
    client: PlaidClient,
    input_data: TransactionSearchInput
) -> Dict[str, Any]:
    """
    Search for transactions matching specific criteria.
    
    Args:
        client: PlaidClient instance
        input_data: Search criteria
        
    Returns:
        Dictionary containing matching transactions
    """
    logging.info(f"Searching transactions with query: {input_data.query}")
    
    # Convert dictionary transactions to Transaction objects
    transactions = []
    for t_dict in input_data.transactions:
        transaction = Transaction(
            transaction_id=t_dict.get("transaction_id", ""),
            account_id=t_dict.get("account_id", ""),
            amount=t_dict.get("amount", 0.0),
            date=t_dict.get("date", ""),
            name=t_dict.get("name", ""),
            merchant_name=t_dict.get("merchant_name"),
            pending=t_dict.get("pending", False),
            category=t_dict.get("category"),
            category_id=t_dict.get("category_id"),
            location=t_dict.get("location"),
            payment_channel=t_dict.get("payment_channel"),
            authorized_date=t_dict.get("authorized_date"),
            payment_meta=t_dict.get("payment_meta"),
            logo_url=t_dict.get("logo_url"),
            website=t_dict.get("website")
        )
        transactions.append(transaction)
    
    # Apply filters
    query_lower = input_data.query.lower()
    filtered_transactions = []
    
    for transaction in transactions:
        # Check text match
        name_match = query_lower in transaction.name.lower()
        merchant_match = transaction.merchant_name and query_lower in transaction.merchant_name.lower()
        category_match = transaction.category and any(query_lower in cat.lower() for cat in transaction.category)
        
        if not (name_match or merchant_match or category_match):
            continue
        
        # Check amount range
        if input_data.min_amount is not None and transaction.amount < input_data.min_amount:
            continue
        if input_data.max_amount is not None and transaction.amount > input_data.max_amount:
            continue
        
        # Check date range
        if input_data.start_date and transaction.date < input_data.start_date:
            continue
        if input_data.end_date and transaction.date > input_data.end_date:
            continue
        
        filtered_transactions.append(transaction)
    
    # Prepare result
    result = {
        "matching_transactions": [t.dict() for t in filtered_transactions],
        "total_matches": len(filtered_transactions),
        "query": input_data.query,
        "amount_range": {
            "min": input_data.min_amount,
            "max": input_data.max_amount
        },
        "date_range": {
            "start": input_data.start_date,
            "end": input_data.end_date
        }
    }
    
    return result


def enrich_transactions(
    client: PlaidClient,
    input_data: TransactionEnrichInput
) -> Dict[str, Any]:
    """
    Enrich transaction data with additional information.
    
    Args:
        client: PlaidClient instance
        input_data: Transactions to enrich
        
    Returns:
        Dictionary containing enriched transactions
    """
    logging.info(f"Enriching {len(input_data.transactions)} transactions")
    
    # Convert dictionary transactions to Transaction objects
    transactions = []
    for t_dict in input_data.transactions:
        transaction = Transaction(
            transaction_id=t_dict.get("transaction_id", ""),
            account_id=t_dict.get("account_id", ""),
            amount=t_dict.get("amount", 0.0),
            date=t_dict.get("date", ""),
            name=t_dict.get("name", ""),
            merchant_name=t_dict.get("merchant_name"),
            pending=t_dict.get("pending", False),
            category=t_dict.get("category"),
            category_id=t_dict.get("category_id"),
            location=t_dict.get("location"),
            payment_channel=t_dict.get("payment_channel"),
            authorized_date=t_dict.get("authorized_date"),
            payment_meta=t_dict.get("payment_meta"),
            logo_url=t_dict.get("logo_url"),
            website=t_dict.get("website")
        )
        transactions.append(transaction)
    
    # Enrich transactions
    # Note: In a real implementation, this would call an enrichment API
    # For now, we'll add some placeholder enriched data
    enriched_transactions = []
    
    for transaction in transactions:
        # Create enriched transaction with original data
        enriched = transaction.dict()
        
        # Add enriched fields (placeholder data)
        if transaction.merchant_name:
            enriched["merchant_logo_url"] = f"https://logo.clearbit.com/{transaction.merchant_name.lower().replace(' ', '')}.com"
            enriched["merchant_website"] = f"https://{transaction.merchant_name.lower().replace(' ', '')}.com"
        
        # Add category confidence (placeholder)
        if transaction.category:
            enriched["category_confidence"] = 0.85
        
        # Add transaction tags (placeholder)
        enriched["tags"] = []
        if transaction.amount > 100:
            enriched["tags"].append("large_transaction")
        if transaction.pending:
            enriched["tags"].append("pending")
        
        # Add spending insights (placeholder)
        if transaction.merchant_name and transaction.amount > 0:
            avg_amount = transaction.amount * 0.9  # Placeholder
            enriched["spending_insights"] = {
                "average_amount": avg_amount,
                "comparison": "above_average" if transaction.amount > avg_amount else "below_average",
                "percent_difference": abs(transaction.amount - avg_amount) / avg_amount * 100
            }
        
        enriched_transactions.append(enriched)
    
    return {
        "enriched_transactions": enriched_transactions,
        "total_transactions": len(enriched_transactions),
        "enrichment_date": datetime.now().isoformat()
    }


# Budget Planning Tools

def create_budget(
    client: PlaidClient,
    input_data: BudgetCreateInput
) -> Dict[str, Any]:
    """
    Create a budget plan.
    
    Args:
        client: PlaidClient instance
        input_data: Budget configuration
        
    Returns:
        Dictionary containing the created budget
    """
    logging.info(f"Creating {input_data.period} budget: {input_data.name}")
    
    # Calculate end date if not provided
    end_date = input_data.end_date
    if not end_date:
        start_date = datetime.strptime(input_data.start_date, "%Y-%m-%d")
        if input_data.period == "weekly":
            end_date = (start_date + timedelta(days=7)).strftime("%Y-%m-%d")
        elif input_data.period == "monthly":
            # Add one month (approximately)
            next_month = start_date.month + 1
            next_year = start_date.year
            if next_month > 12:
                next_month = 1
                next_year += 1
            end_date = start_date.replace(year=next_year, month=next_month).strftime("%Y-%m-%d")
        elif input_data.period == "yearly":
            end_date = start_date.replace(year=start_date.year + 1).strftime("%Y-%m-%d")
    
    # Calculate total budget
    total_budget = sum(input_data.categories.values())
    
    # Create budget object
    budget = {
        "name": input_data.name,
        "period": input_data.period,
        "start_date": input_data.start_date,
        "end_date": end_date,
        "categories": input_data.categories,
        "total_budget": total_budget,
        "created_at": datetime.now().isoformat(),
        "id": f"budget_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    }
    
    return {
        "budget": budget,
        "message": f"Budget '{input_data.name}' created successfully"
    }


def analyze_budget(
    client: PlaidClient,
    input_data: BudgetAnalysisInput
) -> Dict[str, Any]:
    """
    Analyze budget performance against actual spending.
    
    Args:
        client: PlaidClient instance
        input_data: Budget and transactions to analyze
        
    Returns:
        Dictionary containing budget analysis
    """
    logging.info(f"Analyzing budget: {input_data.budget.get('name')}")
    
    budget = input_data.budget
    
    # Convert dictionary transactions to Transaction objects
    transactions = []
    for t_dict in input_data.transactions:
        transaction = Transaction(
            transaction_id=t_dict.get("transaction_id", ""),
            account_id=t_dict.get("account_id", ""),
            amount=t_dict.get("amount", 0.0),
            date=t_dict.get("date", ""),
            name=t_dict.get("name", ""),
            merchant_name=t_dict.get("merchant_name"),
            pending=t_dict.get("pending", False),
            category=t_dict.get("category"),
            category_id=t_dict.get("category_id"),
            location=t_dict.get("location"),
            payment_channel=t_dict.get("payment_channel"),
            authorized_date=t_dict.get("authorized_date"),
            payment_meta=t_dict.get("payment_meta"),
            logo_url=t_dict.get("logo_url"),
            website=t_dict.get("website")
        )
        transactions.append(transaction)
    
    # Filter transactions within budget period
    start_date = budget.get("start_date")
    end_date = budget.get("end_date")
    period_transactions = [t for t in transactions if start_date <= t.date <= end_date]
    
    # Categorize transactions
    categorized = client.categorize_transactions(period_transactions)
    
    # Calculate spending by category
    spending_by_category = {}
    for category, category_transactions in categorized.items():
        spending_by_category[category] = sum(t.amount for t in category_transactions)
    
    # Calculate budget performance
    budget_categories = budget.get("categories", {})
    performance = {}
    
    for category, budget_amount in budget_categories.items():
        spent = spending_by_category.get(category, 0)
        remaining = budget_amount - spent
        percent_used = (spent / budget_amount * 100) if budget_amount > 0 else 0
        
        performance[category] = {
            "budget": budget_amount,
            "spent": spent,
            "remaining": remaining,
            "percent_used": percent_used,
            "status": "over_budget" if spent > budget_amount else "on_track"
        }
    
    # Calculate overall performance
    total_budget = budget.get("total_budget", 0)
    total_spent = sum(spending_by_category.values())
    overall_remaining = total_budget - total_spent
    overall_percent_used = (total_spent / total_budget * 100) if total_budget > 0 else 0
    
    return {
        "budget_name": budget.get("name"),
        "period": budget.get("period"),
        "date_range": {
            "start": start_date,
            "end": end_date
        },
        "category_performance": performance,
        "overall_performance": {
            "budget": total_budget,
            "spent": total_spent,
            "remaining": overall_remaining,
            "percent_used": overall_percent_used,
            "status": "over_budget" if total_spent > total_budget else "on_track"
        },
        "transactions_count": len(period_transactions),
        "analysis_date": datetime.now().isoformat()
    }


def forecast_cash_flow(
    client: PlaidClient,
    input_data: CashFlowForecastInput
) -> Dict[str, Any]:
    """
    Forecast future cash flow based on historical transactions.
    
    Args:
        client: PlaidClient instance
        input_data: Historical data and forecast parameters
        
    Returns:
        Dictionary containing cash flow forecast
    """
    logging.info(f"Forecasting cash flow for {input_data.forecast_days} days")
    
    # Convert dictionary transactions to Transaction objects
    transactions = []
    for t_dict in input_data.transactions:
        transaction = Transaction(
            transaction_id=t_dict.get("transaction_id", ""),
            account_id=t_dict.get("account_id", ""),
            amount=t_dict.get("amount", 0.0),
            date=t_dict.get("date", ""),
            name=t_dict.get("name", ""),
            merchant_name=t_dict.get("merchant_name"),
            pending=t_dict.get("pending", False),
            category=t_dict.get("category"),
            category_id=t_dict.get("category_id"),
            location=t_dict.get("location"),
            payment_channel=t_dict.get("payment_channel"),
            authorized_date=t_dict.get("authorized_date"),
            payment_meta=t_dict.get("payment_meta"),
            logo_url=t_dict.get("logo_url"),
            website=t_dict.get("website")
        )
        transactions.append(transaction)
    
    # Convert account balances to Balance objects
    balances = []
    for b_dict in input_data.account_balances:
        balance = Balance(
            account_id=b_dict.get("account_id", ""),
            current=b_dict.get("current", 0.0),
            available=b_dict.get("available"),
            limit=b_dict.get("limit"),
            iso_currency_code=b_dict.get("iso_currency_code", "USD"),
            unofficial_currency_code=b_dict.get("unofficial_currency_code"),
            last_updated_datetime=datetime.now()
        )
        balances.append(balance)
    
    # Calculate starting balance
    starting_balance = sum(b.current for b in balances)
    
    # Analyze historical cash flow
    inflows = sum(t.amount for t in transactions if t.amount < 0)  # Credits are negative in Plaid
    outflows = sum(t.amount for t in transactions if t.amount > 0)  # Debits are positive in Plaid
    
    # Calculate daily averages
    days_of_history = 90  # Assuming 90 days of transaction history
    daily_inflow = -inflows / days_of_history  # Negate to make positive
    daily_outflow = outflows / days_of_history
    daily_net = daily_inflow - daily_outflow
    
    # Identify recurring transactions if requested
    recurring_transactions = []
    if input_data.include_recurring:
        # Group transactions by merchant
        merchant_transactions = {}
        for transaction in transactions:
            merchant = transaction.merchant_name or transaction.name
            if merchant not in merchant_transactions:
                merchant_transactions[merchant] = []
            merchant_transactions[merchant].append(transaction)
        
        # Find recurring patterns
        for merchant, merchant_txns in merchant_transactions.items():
            if len(merchant_txns) >= 2:
                amounts = [t.amount for t in merchant_txns]
                # If all transactions have the same amount, consider it recurring
                if len(set(amounts)) == 1:
                    # Calculate average interval
                    dates = sorted([datetime.strptime(t.date, "%Y-%m-%d") for t in merchant_txns])
                    intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
                    avg_interval = sum(intervals) / len(intervals) if intervals else 30
                    
                    recurring_transactions.append({
                        "merchant": merchant,
                        "amount": amounts[0],
                        "average_interval_days": avg_interval,
                        "transaction_type": "outflow" if amounts[0] > 0 else "inflow",
                        "next_expected_date": (dates[-1] + timedelta(days=avg_interval)).strftime("%Y-%m-%d")
                    })
    
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
        for recurring in recurring_transactions:
            next_date = datetime.strptime(recurring["next_expected_date"], "%Y-%m-%d")
            interval = recurring["average_interval_days"]
            
            # Check if this recurring transaction occurs on the current date
            while next_date <= current_date:
                next_date += timedelta(days=interval)
            
            if (next_date - current_date).days < 1:  # Transaction occurs today
                if recurring["transaction_type"] == "outflow":
                    day_outflow += recurring["amount"]
                else:
                    day_inflow += recurring["amount"]
        
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
        "recurring_transactions": recurring_transactions,
        "daily_forecast": daily_forecast,
        "forecast_generated_at": datetime.now().isoformat()
    }


# Income Verification Tools

def verify_income(
    client: PlaidClient,
    input_data: IncomeVerificationInput
) -> Dict[str, Any]:
    """
    Verify income based on transaction history.
    
    Args:
        client: PlaidClient instance
        input_data: Income verification parameters
        
    Returns:
        Dictionary containing income verification results
    """
    logging.info(f"Verifying income for the past {input_data.months} months")
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30 * input_data.months)
    
    # Get transactions for the period
    transactions = client.get_transactions(
        access_token=input_data.access_token,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        account_ids=input_data.account_ids
    )
    
    # Identify income transactions (negative amounts in Plaid are credits/income)
    income_transactions = [t for t in transactions if t.amount < 0]
    
    # Group by month
    monthly_income = {}
    for transaction in income_transactions:
        month = transaction.date[:7]  # YYYY-MM format
        if month not in monthly_income:
            monthly_income[month] = []
        monthly_income[month].append(transaction)
    
    # Calculate monthly totals
    monthly_totals = {}
    for month, month_transactions in monthly_income.items():
        monthly_totals[month] = sum(-t.amount for t in month_transactions)  # Negate to make positive
    
    # Calculate average monthly income
    total_income = sum(monthly_totals.values())
    avg_monthly_income = total_income / len(monthly_totals) if monthly_totals else 0
    
    # Identify potential income sources
    income_sources = {}
    for transaction in income_transactions:
        source = transaction.merchant_name or transaction.name
        if source not in income_sources:
            income_sources[source] = []
        income_sources[source].append(transaction)
    
    # Calculate income by source
    income_by_source = {}
    for source, source_transactions in income_sources.items():
        total = sum(-t.amount for t in source_transactions)  # Negate to make positive
        frequency = len(source_transactions)
        avg_amount = total / frequency
        
        income_by_source[source] = {
            "total": total,
            "frequency": frequency,
            "average_amount": avg_amount,
            "percent_of_income": (total / total_income * 100) if total_income > 0 else 0
        }
    
    # Sort sources by total income
    sorted_sources = sorted(income_by_source.items(), key=lambda x: x[1]["total"], reverse=True)
    primary_income_source = sorted_sources[0][0] if sorted_sources else None
    
    return {
        "verified_monthly_income": avg_monthly_income,
        "income_stability": {
            "months_analyzed": len(monthly_totals),
            "monthly_variation": calculate_coefficient_of_variation(list(monthly_totals.values())),
            "is_stable": is_income_stable(list(monthly_totals.values()))
        },
        "monthly_income": monthly_totals,
        "income_sources": income_by_source,
        "primary_income_source": primary_income_source,
        "total_income_transactions": len(income_transactions),
        "verification_period": {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "months": input_data.months
        },
        "verification_date": datetime.now().isoformat()
    }


def analyze_income_patterns(
    client: PlaidClient,
    input_data: IncomeAnalysisInput
) -> Dict[str, Any]:
    """
    Analyze income patterns and trends.
    
    Args:
        client: PlaidClient instance
        input_data: Income analysis parameters
        
    Returns:
        Dictionary containing income pattern analysis
    """
    logging.info(f"Analyzing income patterns for the past {input_data.months} months")
    
    # Convert dictionary transactions to Transaction objects
    transactions = []
    for t_dict in input_data.transactions:
        transaction = Transaction(
            transaction_id=t_dict.get("transaction_id", ""),
            account_id=t_dict.get("account_id", ""),
            amount=t_dict.get("amount", 0.0),
            date=t_dict.get("date", ""),
            name=t_dict.get("name", ""),
            merchant_name=t_dict.get("merchant_name"),
            pending=t_dict.get("pending", False),
            category=t_dict.get("category"),
            category_id=t_dict.get("category_id"),
            location=t_dict.get("location"),
            payment_channel=t_dict.get("payment_channel"),
            authorized_date=t_dict.get("authorized_date"),
            payment_meta=t_dict.get("payment_meta"),
            logo_url=t_dict.get("logo_url"),
            website=t_dict.get("website")
        )
        transactions.append(transaction)
    
    # Identify income transactions (negative amounts in Plaid are credits/income)
    income_transactions = [t for t in transactions if t.amount < 0]
    
    # Group by month
    monthly_income = {}
    for transaction in income_transactions:
        month = transaction.date[:7]  # YYYY-MM format
        if month not in monthly_income:
            monthly_income[month] = []
        monthly_income[month].append(transaction)
    
    # Calculate monthly totals
    monthly_totals = {}
    for month, month_transactions in monthly_income.items():
        monthly_totals[month] = sum(-t.amount for t in month_transactions)  # Negate to make positive
    
    # Calculate income growth trend
    months = sorted(monthly_totals.keys())
    if len(months) >= 2:
        first_month = months[0]
        last_month = months[-1]
        first_income = monthly_totals[first_month]
        last_income = monthly_totals[last_month]
        
        growth_amount = last_income - first_income
        growth_percent = (growth_amount / first_income * 100) if first_income > 0 else 0
        monthly_growth_rate = calculate_monthly_growth_rate(months, monthly_totals)
    else:
        growth_amount = 0
        growth_percent = 0
        monthly_growth_rate = 0
    
    # Identify income patterns
    # 1. Pay frequency
    pay_frequency = detect_pay_frequency(income_transactions)
    
    # 2. Day of month patterns
    day_of_month_pattern = analyze_day_of_month_pattern(income_transactions)
    
    # 3. Income sources
    income_sources = {}
    for transaction in income_transactions:
        source = transaction.merchant_name or transaction.name
        if source not in income_sources:
            income_sources[source] = []
        income_sources[source].append(transaction)
    
    # Calculate income by source
    income_by_source = {}
    for source, source_transactions in income_sources.items():
        total = sum(-t.amount for t in source_transactions)  # Negate to make positive
        frequency = len(source_transactions)
        avg_amount = total / frequency
        
        income_by_source[source] = {
            "total": total,
            "frequency": frequency,
            "average_amount": avg_amount,
            "transactions": [t.dict() for t in source_transactions]
        }
    
    return {
        "income_trend": {
            "months_analyzed": len(months),
            "first_month": months[0] if months else None,
            "last_month": months[-1] if months else None,
            "growth_amount": growth_amount,
            "growth_percent": growth_percent,
            "monthly_growth_rate": monthly_growth_rate
        },
        "income_patterns": {
            "pay_frequency": pay_frequency,
            "day_of_month_pattern": day_of_month_pattern,
            "income_stability": {
                "coefficient_of_variation": calculate_coefficient_of_variation(list(monthly_totals.values())),
                "is_stable": is_income_stable(list(monthly_totals.values()))
            }
        },
        "income_sources": income_by_source,
        "monthly_income": monthly_totals,
        "analysis_date": datetime.now().isoformat()
    }


# Financial Health Tools

def assess_financial_health(
    client: PlaidClient,
    input_data: FinancialHealthAssessmentInput
) -> Dict[str, Any]:
    """
    Assess overall financial health.
    
    Args:
        client: PlaidClient instance
        input_data: Financial data for assessment
        
    Returns:
        Dictionary containing financial health assessment
    """
    logging.info("Assessing financial health")
    
    # Convert dictionary balances to Balance objects
    balances = []
    for b_dict in input_data.balances:
        balance = Balance(
            account_id=b_dict.get("account_id", ""),
            current=b_dict.get("current", 0.0),
            available=b_dict.get("available"),
            limit=b_dict.get("limit"),
            iso_currency_code=b_dict.get("iso_currency_code", "USD"),
            unofficial_currency_code=b_dict.get("unofficial_currency_code"),
            last_updated_datetime=datetime.now()
        )
        balances.append(balance)
    
    # Convert dictionary transactions to Transaction objects
    transactions = []
    for t_dict in input_data.transactions:
        transaction = Transaction(
            transaction_id=t_dict.get("transaction_id", ""),
            account_id=t_dict.get("account_id", ""),
            amount=t_dict.get("amount", 0.0),
            date=t_dict.get("date", ""),
            name=t_dict.get("name", ""),
            merchant_name=t_dict.get("merchant_name"),
            pending=t_dict.get("pending", False),
            category=t_dict.get("category"),
            category_id=t_dict.get("category_id"),
            location=t_dict.get("location"),
            payment_channel=t_dict.get("payment_channel"),
            authorized_date=t_dict.get("authorized_date"),
            payment_meta=t_dict.get("payment_meta"),
            logo_url=t_dict.get("logo_url"),
            website=t_dict.get("website")
        )
        transactions.append(transaction)
    
    # Convert dictionary liabilities to Liability objects
    liabilities = []
    if input_data.liabilities:
        for l_dict in input_data.liabilities:
            liability = Liability(
                account_id=l_dict.get("account_id", ""),
                type=l_dict.get("type", ""),
                origination_date=l_dict.get("origination_date"),
                term=l_dict.get("term"),
                interest_rate=l_dict.get("interest_rate"),
                payment_amount=l_dict.get("payment_amount"),
                outstanding_balance=l_dict.get("outstanding_balance"),
                origination_principal=l_dict.get("origination_principal"),
                next_payment_due_date=l_dict.get("next_payment_due_date"),
                details=l_dict.get("details")
            )
            liabilities.append(liability)
    
    # Use the client's financial health calculation
    health_metrics = client.calculate_financial_health(balances, transactions, liabilities)
    
    # Calculate additional metrics
    
    # 1. Debt-to-asset ratio
    total_assets = health_metrics.get("total_assets", 0)
    total_liabilities = health_metrics.get("total_liabilities", 0)
    debt_to_asset_ratio = total_liabilities / total_assets if total_assets > 0 else float('inf')
    
    # 2. Liquidity ratio
    liquid_assets = sum(
        b.available or b.current for b in balances 
        if b.subtype in ["checking", "savings"]
    )
    short_term_liabilities = sum(
        l.payment_amount or 0 for l in liabilities 
        if l.type == "credit"
    )
    liquidity_ratio = liquid_assets / short_term_liabilities if short_term_liabilities > 0 else float('inf')
    
    # 3. Net worth trend
    # In a real implementation, this would use historical data
    net_worth_trend = "stable"  # Placeholder
    
    # 4. Credit utilization
    credit_limits = sum(b.limit or 0 for b in balances if b.type == "credit")
    credit_used = sum(b.current for b in balances if b.type == "credit")
    credit_utilization = credit_used / credit_limits * 100 if credit_limits > 0 else 0
    
    # Calculate overall financial health score (0-100)
    # This is a simplified scoring model
    score_components = {
        "savings_rate": min(health_metrics.get("savings_rate", 0) / 20 * 25, 25),  # 25% weight, max at 20% savings rate
        "emergency_fund": min(health_metrics.get("emergency_fund_months", 0) / 6 * 25, 25),  # 25% weight, max at 6 months
        "debt_management": 25 * (1 - min(health_metrics.get("debt_to_income_ratio", 0) / 36, 1)),  # 25% weight, 0 at 36% DTI
        "credit_usage": 25 * (1 - min(credit_utilization / 30, 1))  # 25% weight, 0 at 30% utilization
    }
    
    overall_score = sum(score_components.values())
    
    # Determine health status based on score
    health_status = "excellent" if overall_score >= 80 else "good" if overall_score >= 60 else "fair" if overall_score >= 40 else "poor"
    
    # Generate recommendations
    recommendations = []
    
    if health_metrics.get("emergency_fund_months", 0) < 3:
        recommendations.append("Build emergency fund to cover at least 3-6 months of expenses")
    
    if health_metrics.get("debt_to_income_ratio", 0) > 36:
        recommendations.append("Reduce debt to improve debt-to-income ratio")
    
    if credit_utilization > 30:
        recommendations.append("Reduce credit card balances to lower credit utilization")
    
    if health_metrics.get("savings_rate", 0) < 15:
        recommendations.append("Increase savings rate to at least 15% of income")
    
    return {
        "overall_health": {
            "score": overall_score,
            "status": health_status,
            "score_components": score_components
        },
        "key_metrics": {
            "net_worth": health_metrics.get("net_worth", 0),
            "monthly_income": health_metrics.get("monthly_income", 0),
            "monthly_expenses": health_metrics.get("monthly_expenses", 0),
            "savings_rate": health_metrics.get("savings_rate", 0),
            "debt_to_income_ratio": health_metrics.get("debt_to_income_ratio", 0),
            "emergency_fund_months": health_metrics.get("emergency_fund_months", 0),
            "debt_to_asset_ratio": debt_to_asset_ratio,
            "liquidity_ratio": liquidity_ratio,
            "credit_utilization": credit_utilization
        },
        "balance_sheet": {
            "total_assets": health_metrics.get("total_assets", 0),
            "liquid_assets": liquid_assets,
            "total_liabilities": health_metrics.get("total_liabilities", 0),
            "net_worth": health_metrics.get("net_worth", 0),
            "net_worth_trend": net_worth_trend
        },
        "recommendations": recommendations,
        "assessment_date": datetime.now().isoformat()
    }


def analyze_debt(
    client: PlaidClient,
    input_data: DebtAnalysisInput
) -> Dict[str, Any]:
    """
    Analyze debt and provide repayment strategies.
    
    Args:
        client: PlaidClient instance
        input_data: Debt information for analysis
        
    Returns:
        Dictionary containing debt analysis
    """
    logging.info("Analyzing debt")
    
    # Convert dictionary liabilities to Liability objects
    liabilities = []
    for l_dict in input_data.liabilities:
        liability = Liability(
            account_id=l_dict.get("account_id", ""),
            type=l_dict.get("type", ""),
            origination_date=l_dict.get("origination_date"),
            term=l_dict.get("term"),
            interest_rate=l_dict.get("interest_rate"),
            payment_amount=l_dict.get("payment_amount"),
            outstanding_balance=l_dict.get("outstanding_balance"),
            origination_principal=l_dict.get("origination_principal"),
            next_payment_due_date=l_dict.get("next_payment_due_date"),
            details=l_dict.get("details")
        )
        liabilities.append(liability)
    
    # Calculate total debt
    total_debt = sum(l.outstanding_balance or 0 for l in liabilities)
    
    # Calculate monthly debt payments
    monthly_debt_payments = sum(l.payment_amount or 0 for l in liabilities)
    
    # Calculate debt-to-income ratio
    debt_to_income = monthly_debt_payments / input_data.income * 100 if input_data.income > 0 else 0
    
    # Categorize debt by type
    debt_by_type = {}
    for liability in liabilities:
        debt_type = liability.type
        if debt_type not in debt_by_type:
            debt_by_type[debt_type] = []
        debt_by_type[debt_type].append(liability)
    
    # Calculate debt by type
    debt_summary_by_type = {}
    for debt_type, type_liabilities in debt_by_type.items():
        total_balance = sum(l.outstanding_balance or 0 for l in type_liabilities)
        total_payment = sum(l.payment_amount or 0 for l in type_liabilities)
        avg_interest_rate = sum(l.interest_rate or 0 for l in type_liabilities) / len(type_liabilities) if type_liabilities else 0
        
        debt_summary_by_type[debt_type] = {
            "total_balance": total_balance,
            "total_payment": total_payment,
            "average_interest_rate": avg_interest_rate,
            "count": len(type_liabilities),
            "percent_of_total": (total_balance / total_debt * 100) if total_debt > 0 else 0
        }
    
    # Generate debt repayment strategies
    
    # 1. Avalanche method (highest interest first)
    sorted_by_interest = sorted(liabilities, key=lambda x: x.interest_rate or 0, reverse=True)
    avalanche_strategy = []
    
    for liability in sorted_by_interest:
        avalanche_strategy.append({
            "account_id": liability.account_id,
            "type": liability.type,
            "balance": liability.outstanding_balance,
            "interest_rate": liability.interest_rate,
            "priority": len(avalanche_strategy) + 1
        })
    
    # 2. Snowball method (smallest balance first)
    sorted_by_balance = sorted(liabilities, key=lambda x: x.outstanding_balance or float('inf'))
    snowball_strategy = []
    
    for liability in sorted_by_balance:
        snowball_strategy.append({
            "account_id": liability.account_id,
            "type": liability.type,
            "balance": liability.outstanding_balance,
            "interest_rate": liability.interest_rate,
            "priority": len(snowball_strategy) + 1
        })
    
    # Calculate potential savings with avalanche method
    # This is a simplified calculation
    monthly_extra = 100  # Placeholder for extra monthly payment
    avalanche_savings = calculate_debt_repayment_savings(sorted_by_interest, monthly_extra)
    snowball_savings = calculate_debt_repayment_savings(sorted_by_balance, monthly_extra)
    
    return {
        "total_debt": total_debt,
        "monthly_debt_payments": monthly_debt_payments,
        "debt_to_income_ratio": debt_to_income,
        "debt_by_type": debt_summary_by_type,
        "repayment_strategies": {
            "avalanche_method": {
                "description": "Pay highest interest rate debts first",
                "priority_list": avalanche_strategy,
                "potential_savings": avalanche_savings,
                "recommended_for": "Minimizing interest paid"
            },
            "snowball_method": {
                "description": "Pay smallest balance debts first",
                "priority_list": snowball_strategy,
                "potential_savings": snowball_savings,
                "recommended_for": "Building momentum and motivation"
            }
        },
        "debt_status": {
            "status": get_debt_status(debt_to_income),
            "recommendations": get_debt_recommendations(debt_to_income, total_debt, input_data.income)
        },
        "analysis_date": datetime.now().isoformat()
    }


def plan_savings_goal(
    client: PlaidClient,
    input_data: SavingsGoalInput
) -> Dict[str, Any]:
    """
    Plan for achieving a savings goal.
    
    Args:
        client: PlaidClient instance
        input_data: Savings goal parameters
        
    Returns:
        Dictionary containing savings goal plan
    """
    logging.info(f"Planning for savings goal of ${input_data.goal_amount}")
    
    # Calculate time to reach goal with current contribution
    months_to_goal = calculate_months_to_savings_goal(
        goal_amount=input_data.goal_amount,
        current_savings=input_data.current_savings,
        monthly_contribution=input_data.monthly_contribution,
        annual_interest_rate=input_data.interest_rate
    )
    
    # Calculate required monthly contribution to reach goal in different timeframes
    required_contributions = {}
    for months in [12, 24, 36, 60, 120]:
        required_contribution = calculate_required_contribution(
            goal_amount=input_data.goal_amount,
            current_savings=input_data.current_savings,
            months=months,
            annual_interest_rate=input_data.interest_rate
        )
        required_contributions[months] = required_contribution
    
    # Generate monthly savings projection
    projection = []
    balance = input_data.current_savings
    monthly_interest_rate = input_data.interest_rate / 12
    
    for month in range(1, min(int(months_to_goal) + 1, 120) + 1):
        interest_earned = balance * monthly_interest_rate
        balance += interest_earned + input_data.monthly_contribution
        
        projection.append({
            "month": month,
            "balance": balance,
            "interest_earned": interest_earned,
            "contribution": input_data.monthly_contribution,
            "percent_of_goal": (balance / input_data.goal_amount * 100) if input_data.goal_amount > 0 else 0
        })
    
    # Generate recommendations
    recommendations = []
    
    if months_to_goal > 60:
        recommendations.append("Consider increasing your monthly contribution to reach your goal faster")
    
    if input_data.interest_rate < 0.01:  # Less than 1%
        recommendations.append("Look for higher-yield savings options to accelerate your goal")
    
    if input_data.monthly_contribution < input_data.goal_amount * 0.02:  # Less than 2% of goal per month
        recommendations.append("Your current contribution rate is relatively low compared to your goal")
    
    return {
        "goal_amount": input_data.goal_amount,
        "current_savings": input_data.current_savings,
        "monthly_contribution": input_data.monthly_contribution,
        "annual_interest_rate": input_data.interest_rate * 100,  # Convert to percentage
        "time_to_goal": {
            "months": months_to_goal,
            "years": months_to_goal / 12,
            "projected_completion_date": (datetime.now() + timedelta(days=30 * months_to_goal)).strftime("%Y-%m-%d")
        },
        "required_monthly_contributions": {
            "1_year": required_contributions.get(12),
            "2_years": required_contributions.get(24),
            "3_years": required_contributions.get(36),
            "5_years": required_contributions.get(60),
            "10_years": required_contributions.get(120)
        },
        "projection": projection,
        "recommendations": recommendations,
        "plan_date": datetime.now().isoformat()
    }


# Spending Analysis Tools

def analyze_spending(
    client: PlaidClient,
    input_data: SpendingAnalysisInput
) -> Dict[str, Any]:
    """
    Analyze spending patterns.
    
    Args:
        client: PlaidClient instance
        input_data: Spending analysis parameters
        
    Returns:
        Dictionary containing spending analysis
    """
    logging.info(f"Analyzing spending patterns grouped by {input_data.group_by}")
    
    # Convert dictionary transactions to Transaction objects
    transactions = []
    for t_dict in input_data.transactions:
        transaction = Transaction(
            transaction_id=t_dict.get("transaction_id", ""),
            account_id=t_dict.get("account_id", ""),
            amount=t_dict.get("amount", 0.0),
            date=t_dict.get("date", ""),
            name=t_dict.get("name", ""),
            merchant_name=t_dict.get("merchant_name"),
            pending=t_dict.get("pending", False),
            category=t_dict.get("category"),
            category_id=t_dict.get("category_id"),
            location=t_dict.get("location"),
            payment_channel=t_dict.get("payment_channel"),
            authorized_date=t_dict.get("authorized_date"),
            payment_meta=t_dict.get("payment_meta"),
            logo_url=t_dict.get("logo_url"),
            website=t_dict.get("website")
        )
        transactions.append(transaction)
    
    # Filter transactions by date if specified
    filtered_transactions = transactions
    if input_data.start_date:
        filtered_transactions = [t for t in filtered_transactions if t.date >= input_data.start_date]
    if input_data.end_date:
        filtered_transactions = [t for t in filtered_transactions if t.date <= input_data.end_date]
    
    # Filter for spending only (positive amounts are debits/spending in Plaid)
    spending_transactions = [t for t in filtered_transactions if t.amount > 0]
    
    # Group transactions based on specified grouping
    grouped_spending = {}
    
    if input_data.group_by == "category":
        # Categorize transactions
        categorized = client.categorize_transactions(spending_transactions)
        
        for category, category_transactions in categorized.items():
            grouped_spending[category] = {
                "total": sum(t.amount for t in category_transactions),
                "count": len(category_transactions),
                "average": sum(t.amount for t in category_transactions) / len(category_transactions) if category_transactions else 0,
                "transactions": [t.dict() for t in category_transactions]
            }
    
    elif input_data.group_by == "month":
        # Group by month
        for transaction in spending_transactions:
            month = transaction.date[:7]  # YYYY-MM format
            if month not in grouped_spending:
                grouped_spending[month] = {
                    "total": 0,
                    "count": 0,
                    "transactions": []
                }
            
            grouped_spending[month]["total"] += transaction.amount
            grouped_spending[month]["count"] += 1
            grouped_spending[month]["transactions"].append(transaction.dict())
        
        # Calculate averages
        for month, data in grouped_spending.items():
            data["average"] = data["total"] / data["count"] if data["count"] > 0 else 0
    
    elif input_data.group_by == "merchant":
        # Group by merchant
        for transaction in spending_transactions:
            merchant = transaction.merchant_name or transaction.name
            if merchant not in grouped_spending:
                grouped_spending[merchant] = {
                    "total": 0,
                    "count": 0,
                    "transactions": []
                }
            
            grouped_spending[merchant]["total"] += transaction.amount
            grouped_spending[merchant]["count"] += 1
            grouped_spending[merchant]["transactions"].append(transaction.dict())
        
        # Calculate averages
        for merchant, data in grouped_spending.items():
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
            "start": input_data.start_date,
            "end": input_data.end_date
        },
        "analysis_date": datetime.now().isoformat()
    }


def analyze_merchants(
    client: PlaidClient,
    input_data: MerchantAnalysisInput
) -> Dict[str, Any]:
    """
    Analyze spending by merchant.
    
    Args:
        client: PlaidClient instance
        input_data: Merchant analysis parameters
        
    Returns:
        Dictionary containing merchant analysis
    """
    logging.info(f"Analyzing merchant spending for the past {input_data.months} months")
    
    # Convert dictionary transactions to Transaction objects
    transactions = []
    for t_dict in input_data.transactions:
        transaction = Transaction(
            transaction_id=t_dict.get("transaction_id", ""),
            account_id=t_dict.get("account_id", ""),
            amount=t_dict.get("amount", 0.0),
            date=t_dict.get("date", ""),
            name=t_dict.get("name", ""),
            merchant_name=t_dict.get("merchant_name"),
            pending=t_dict.get("pending", False),
            category=t_dict.get("category"),
            category_id=t_dict.get("category_id"),
            location=t_dict.get("location"),
            payment_channel=t_dict.get("payment_channel"),
            authorized_date=t_dict.get("authorized_date"),
            payment_meta=t_dict.get("payment_meta"),
            logo_url=t_dict.get("logo_url"),
            website=t_dict.get("website")
        )
        transactions.append(transaction)
    
    # Filter for recent transactions
    months_ago = datetime.now() - timedelta(days=30 * input_data.months)
    start_date = months_ago.strftime("%Y-%m-%d")
    recent_transactions = [t for t in transactions if t.date >= start_date]
    
    # Filter for spending only (positive amounts are debits/spending in Plaid)
    spending_transactions = [t for t in recent_transactions if t.amount > 0]
    
    # Group by merchant
    merchant_spending = {}
    for transaction in spending_transactions:
        merchant = transaction.merchant_name or transaction.name
        if merchant not in merchant_spending:
            merchant_spending[merchant] = {
                "transactions": [],
                "total": 0,
                "count": 0
            }
        
        merchant_spending[merchant]["transactions"].append(transaction)
        merchant_spending[merchant]["total"] += transaction.amount
        merchant_spending[merchant]["count"] += 1
    
    # Calculate additional metrics for each merchant
    merchant_analysis = {}
    for merchant, data in merchant_spending.items():
        transactions = data["transactions"]
        total = data["total"]
        count = data["count"]
        
        # Calculate average transaction amount
        average_amount = total / count if count > 0 else 0
        
        # Calculate frequency (transactions per month)
        frequency = count / input_data.months
        
        # Calculate first and last transaction dates
        dates = sorted([t.date for t in transactions])
        first_date = dates[0] if dates else None
        last_date = dates[-1] if dates else None
        
        # Calculate average days between transactions
        if len(dates) >= 2:
            date_diffs = [(datetime.strptime(dates[i+1], "%Y-%m-%d") - datetime.strptime(dates[i], "%Y-%m-%d")).days 
                         for i in range(len(dates)-1)]
            avg_days_between = sum(date_diffs) / len(date_diffs)
        else:
            avg_days_between = None
        
        # Get categories
        categories = set()
        for transaction in transactions:
            if transaction.category:
                categories.update(transaction.category)
        
        merchant_analysis[merchant] = {
            "total_spent": total,
            "transaction_count": count,
            "average_amount": average_amount,
            "frequency_per_month": frequency,
            "first_transaction": first_date,
            "last_transaction": last_date,
            "average_days_between": avg_days_between,
            "categories": list(categories)
        }
    
    # Sort merchants by total spent
    sorted_merchants = sorted(merchant_analysis.items(), key=lambda x: x[1]["total_spent"], reverse=True)
    top_merchants = [{"name": merchant, "data": data} for merchant, data in sorted_merchants[:10]]
    
    # Calculate merchant spending distribution
    total_spending = sum(data["total_spent"] for data in merchant_analysis.values())
    merchant_distribution = {merchant: (data["total_spent"] / total_spending * 100) if total_spending > 0 else 0 
                           for merchant, data in merchant_analysis.items()}
    
    return {
        "top_merchants": top_merchants,
        "merchant_analysis": merchant_analysis,
        "merchant_distribution": merchant_distribution,
        "total_merchants": len(merchant_analysis),
        "total_spending": total_spending,
        "analysis_period": {
            "months": input_data.months,
            "start_date": start_date,
            "end_date": datetime.now().strftime("%Y-%m-%d")
        },
        "analysis_date": datetime.now().isoformat()
    }

