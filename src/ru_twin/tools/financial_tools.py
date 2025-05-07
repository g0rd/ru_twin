"""
Finance Tools for RuTwin Crew (Part 2)

This module continues the finance_tools.py file with additional functions
for recurring expenses, investment tracking, and helper utilities.
"""

import logging
import math
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Union, Any, Tuple
from collections import defaultdict
import statistics

import pandas as pd
from pydantic import BaseModel, Field

from ru_twin.mcp_clients.plaid import (
    PlaidClient, Account, Transaction, Balance, 
    Identity, Investment, Liability, AccountType
)
from ru_twin.tools.tool_registry import ToolRegistry


# Continuing from finance_tools.py - completing the identify_recurring_expenses function

def identify_recurring_expenses(
    client: PlaidClient,
    input_data: RecurringExpensesInput
) -> Dict[str, Any]:
    """
    Identify recurring expenses from transaction history.
    
    Args:
        client: PlaidClient instance
        input_data: Configuration for identifying recurring expenses
        
    Returns:
        Dictionary containing identified recurring expenses
    """
    logging.info(f"Identifying recurring expenses with minimum {input_data.min_occurrences} occurrences")
    
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
    
    # Filter for spending only (positive amounts are debits/spending in Plaid)
    spending_transactions = [t for t in transactions if t.amount > 0]
    
    # Filter for recent transactions
    days_ago = datetime.now() - timedelta(days=input_data.days)
    start_date = days_ago.strftime("%Y-%m-%d")
    recent_transactions = [t for t in spending_transactions if t.date >= start_date]
    
    # Group by merchant
    merchant_transactions = {}
    for transaction in recent_transactions:
        merchant = transaction.merchant_name or transaction.name
        if merchant not in merchant_transactions:
            merchant_transactions[merchant] = []
        merchant_transactions[merchant].append(transaction)
    
    # Identify potential recurring expenses
    recurring_expenses = []
    
    for merchant, merchant_txns in merchant_transactions.items():
        # Skip if not enough occurrences
        if len(merchant_txns) < input_data.min_occurrences:
            continue
        
        # Group transactions by amount (within tolerance)
        amount_groups = defaultdict(list)
        
        for transaction in merchant_txns:
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
                
                recurring_expenses.append({
                    "merchant": merchant,
                    "amount": amount,
                    "occurrences": len(amount_txns),
                    "average_interval_days": avg_interval,
                    "frequency_type": frequency_type,
                    "last_date": sorted_txns[-1].date,
                    "next_expected_date": next_date.strftime("%Y-%m-%d"),
                    "category": sorted_txns[0].category[0] if sorted_txns[0].category else "Uncategorized",
                    "transactions": [t.dict() for t in sorted_txns]
                })
    
    # Sort by amount (descending)
    recurring_expenses.sort(key=lambda x: x["amount"], reverse=True)
    
    # Calculate total recurring expenses
    total_recurring = sum(expense["amount"] for expense in recurring_expenses)
    
    # Group by frequency type
    grouped_by_frequency = {}
    for expense in recurring_expenses:
        frequency = expense["frequency_type"]
        if frequency not in grouped_by_frequency:
            grouped_by_frequency[frequency] = []
        grouped_by_frequency[frequency].append(expense)
    
    # Calculate totals by frequency
    totals_by_frequency = {}
    for frequency, expenses in grouped_by_frequency.items():
        totals_by_frequency[frequency] = sum(expense["amount"] for expense in expenses)
    
    return {
        "recurring_expenses": recurring_expenses,
        "total_recurring_expenses": total_recurring,
        "total_by_frequency": totals_by_frequency,
        "expense_count": len(recurring_expenses),
        "analysis_period": {
            "days": input_data.days,
            "start_date": start_date,
            "end_date": datetime.now().strftime("%Y-%m-%d")
        },
        "analysis_date": datetime.now().isoformat()
    }


# Investment Tracking Tools

def get_investment_holdings(
    client: PlaidClient,
    input_data: InvestmentHoldingsInput
) -> Dict[str, Any]:
    """
    Get investment holdings for accounts.
    
    Args:
        client: PlaidClient instance
        input_data: Configuration for getting investment holdings
        
    Returns:
        Dictionary containing investment holdings
    """
    logging.info(f"Getting investment holdings for access token: {input_data.access_token[:10]}...")
    
    holdings = client.get_investments_holdings(input_data.access_token)
    
    # Convert holdings to dictionaries
    holdings_data = [holding.dict() for holding in holdings]
    
    # Calculate total portfolio value
    total_value = sum(holding.value for holding in holdings)
    
    # Group holdings by security type
    holdings_by_type = {}
    for holding in holdings:
        security_type = holding.type or "Unknown"
        if security_type not in holdings_by_type:
            holdings_by_type[security_type] = []
        holdings_by_type[security_type].append(holding.dict())
    
    # Calculate value by security type
    value_by_type = {}
    for security_type, type_holdings in holdings_by_type.items():
        value_by_type[security_type] = sum(holding["value"] for holding in type_holdings)
    
    # Calculate allocation percentages
    allocation = {}
    for security_type, value in value_by_type.items():
        allocation[security_type] = (value / total_value * 100) if total_value > 0 else 0
    
    return {
        "holdings": holdings_data,
        "total_holdings": len(holdings),
        "total_value": total_value,
        "holdings_by_type": holdings_by_type,
        "value_by_type": value_by_type,
        "allocation": allocation,
        "last_updated": datetime.now().isoformat()
    }


def get_investment_transactions(
    client: PlaidClient,
    input_data: InvestmentTransactionsInput
) -> Dict[str, Any]:
    """
    Get investment transactions for accounts.
    
    Args:
        client: PlaidClient instance
        input_data: Configuration for getting investment transactions
        
    Returns:
        Dictionary containing investment transactions
    """
    logging.info(f"Getting investment transactions from {input_data.start_date} to {input_data.end_date}")
    
    result = client.get_investments_transactions(
        access_token=input_data.access_token,
        start_date=input_data.start_date,
        end_date=input_data.end_date
    )
    
    investment_transactions = result.get("investment_transactions", [])
    securities = result.get("securities", [])
    
    # Create a lookup for securities
    securities_by_id = {security["security_id"]: security for security in securities}
    
    # Enhance transactions with security information
    enhanced_transactions = []
    for transaction in investment_transactions:
        security_id = transaction.get("security_id")
        security = securities_by_id.get(security_id, {}) if security_id else {}
        
        enhanced_transaction = {
            **transaction,
            "security_name": security.get("name", "Unknown"),
            "security_type": security.get("type", "Unknown"),
            "ticker_symbol": security.get("ticker_symbol"),
            "iso_currency_code": transaction.get("iso_currency_code", "USD")
        }
        enhanced_transactions.append(enhanced_transaction)
    
    # Group transactions by type
    transactions_by_type = {}
    for transaction in enhanced_transactions:
        txn_type = transaction.get("type", "Unknown")
        if txn_type not in transactions_by_type:
            transactions_by_type[txn_type] = []
        transactions_by_type[txn_type].append(transaction)
    
    # Calculate total by type
    total_by_type = {}
    for txn_type, txns in transactions_by_type.items():
        total_by_type[txn_type] = sum(txn.get("amount", 0) for txn in txns)
    
    return {
        "investment_transactions": enhanced_transactions,
        "total_transactions": len(enhanced_transactions),
        "transactions_by_type": transactions_by_type,
        "total_by_type": total_by_type,
        "securities": securities,
        "date_range": {
            "start_date": input_data.start_date,
            "end_date": input_data.end_date
        }
    }


def analyze_portfolio(
    client: PlaidClient,
    input_data: PortfolioAnalysisInput
) -> Dict[str, Any]:
    """
    Analyze investment portfolio.
    
    Args:
        client: PlaidClient instance
        input_data: Configuration for portfolio analysis
        
    Returns:
        Dictionary containing portfolio analysis
    """
    logging.info(f"Analyzing portfolio with risk tolerance: {input_data.risk_tolerance}")
    
    # Convert dictionary holdings to Investment objects
    holdings = []
    for h_dict in input_data.holdings:
        holding = Investment(
            account_id=h_dict.get("account_id", ""),
            security_id=h_dict.get("security_id", ""),
            name=h_dict.get("name", "Unknown"),
            quantity=h_dict.get("quantity", 0.0),
            price=h_dict.get("price", 0.0),
            value=h_dict.get("value", 0.0),
            iso_currency_code=h_dict.get("iso_currency_code", "USD"),
            institution_value=h_dict.get("institution_value"),
            cost_basis=h_dict.get("cost_basis"),
            type=h_dict.get("type")
        )
        holdings.append(holding)
    
    # Calculate total portfolio value
    total_value = sum(holding.value for holding in holdings)
    
    # Group holdings by security type
    holdings_by_type = {}
    for holding in holdings:
        security_type = holding.type or "Unknown"
        if security_type not in holdings_by_type:
            holdings_by_type[security_type] = []
        holdings_by_type[security_type].append(holding)
    
    # Calculate value by security type
    value_by_type = {}
    for security_type, type_holdings in holdings_by_type.items():
        value_by_type[security_type] = sum(holding.value for holding in type_holdings)
    
    # Calculate allocation percentages
    current_allocation = {}
    for security_type, value in value_by_type.items():
        current_allocation[security_type] = (value / total_value * 100) if total_value > 0 else 0
    
    # Define target allocations based on risk tolerance
    target_allocation = {}
    if input_data.risk_tolerance == "conservative":
        target_allocation = {
            "cash": 10,
            "bond": 50,
            "stock": 30,
            "etf": 10,
            "mutual_fund": 0,
            "other": 0
        }
    elif input_data.risk_tolerance == "moderate":
        target_allocation = {
            "cash": 5,
            "bond": 30,
            "stock": 45,
            "etf": 15,
            "mutual_fund": 5,
            "other": 0
        }
    else:  # aggressive
        target_allocation = {
            "cash": 2,
            "bond": 15,
            "stock": 60,
            "etf": 18,
            "mutual_fund": 5,
            "other": 0
        }
    
    # Calculate allocation differences
    allocation_diff = {}
    for security_type, target_pct in target_allocation.items():
        current_pct = current_allocation.get(security_type, 0)
        allocation_diff[security_type] = current_pct - target_pct
    
    # Generate rebalancing recommendations
    rebalancing = []
    for security_type, diff in allocation_diff.items():
        if abs(diff) >= 5:  # Only recommend changes for significant differences
            action = "reduce" if diff > 0 else "increase"
            amount = abs(diff) / 100 * total_value
            
            rebalancing.append({
                "security_type": security_type,
                "action": action,
                "current_percentage": current_allocation.get(security_type, 0),
                "target_percentage": target_allocation.get(security_type, 0),
                "difference": diff,
                "amount": amount
            })
    
    # Calculate diversification score (0-100)
    # More evenly distributed = higher score
    diversification_score = 100
    
    # Penalize for concentration in single security type
    for security_type, value in value_by_type.items():
        pct = (value / total_value * 100) if total_value > 0 else 0
        if pct > 50:  # More than 50% in one type
            diversification_score -= (pct - 50) * 0.5
    
    # Penalize for too few security types
    if len(value_by_type) < 3:
        diversification_score -= (3 - len(value_by_type)) * 10
    
    diversification_score = max(0, min(100, diversification_score))
    
    # Calculate risk score (0-100)
    # Higher risk assets = higher score
    risk_weights = {
        "cash": 0,
        "bond": 30,
        "stock": 80,
        "etf": 60,
        "mutual_fund": 50,
        "other": 40
    }
    
    risk_score = 0
    for security_type, value in value_by_type.items():
        pct = (value / total_value * 100) if total_value > 0 else 0
        risk_score += pct * risk_weights.get(security_type.lower(), 50) / 100
    
    return {
        "portfolio_value": total_value,
        "holdings_count": len(holdings),
        "current_allocation": current_allocation,
        "target_allocation": target_allocation,
        "allocation_difference": allocation_diff,
        "rebalancing_recommendations": rebalancing,
        "portfolio_metrics": {
            "diversification_score": diversification_score,
            "risk_score": risk_score,
            "risk_level": get_risk_level(risk_score),
            "alignment_with_risk_tolerance": is_aligned_with_risk_tolerance(risk_score, input_data.risk_tolerance)
        },
        "analysis_date": datetime.now().isoformat()
    }


def analyze_asset_allocation(
    client: PlaidClient,
    input_data: AssetAllocationInput
) -> Dict[str, Any]:
    """
    Analyze asset allocation of investment portfolio.
    
    Args:
        client: PlaidClient instance
        input_data: Configuration for asset allocation analysis
        
    Returns:
        Dictionary containing asset allocation analysis
    """
    logging.info("Analyzing asset allocation")
    
    # Convert dictionary holdings to Investment objects
    holdings = []
    for h_dict in input_data.holdings:
        holding = Investment(
            account_id=h_dict.get("account_id", ""),
            security_id=h_dict.get("security_id", ""),
            name=h_dict.get("name", "Unknown"),
            quantity=h_dict.get("quantity", 0.0),
            price=h_dict.get("price", 0.0),
            value=h_dict.get("value", 0.0),
            iso_currency_code=h_dict.get("iso_currency_code", "USD"),
            institution_value=h_dict.get("institution_value"),
            cost_basis=h_dict.get("cost_basis"),
            type=h_dict.get("type")
        )
        holdings.append(holding)
    
    # Calculate total portfolio value
    total_value = sum(holding.value for holding in holdings)
    
    # Group holdings by security type (asset class)
    holdings_by_type = {}
    for holding in holdings:
        security_type = holding.type or "Unknown"
        if security_type not in holdings_by_type:
            holdings_by_type[security_type] = []
        holdings_by_type[security_type].append(holding)
    
    # Calculate value by security type
    value_by_type = {}
    for security_type, type_holdings in holdings_by_type.items():
        value_by_type[security_type] = sum(holding.value for holding in type_holdings)
    
    # Calculate current allocation percentages
    current_allocation = {}
    for security_type, value in value_by_type.items():
        current_allocation[security_type] = (value / total_value * 100) if total_value > 0 else 0
    
    # Use provided target allocation or default to balanced allocation
    target_allocation = input_data.target_allocation or {
        "cash": 5,
        "bond": 30,
        "stock": 45,
        "etf": 15,
        "mutual_fund": 5
    }
    
    # Calculate allocation differences
    allocation_diff = {}
    for security_type in set(list(current_allocation.keys()) + list(target_allocation.keys())):
        current_pct = current_allocation.get(security_type, 0)
        target_pct = target_allocation.get(security_type, 0)
        allocation_diff[security_type] = current_pct - target_pct
    
    # Calculate rebalancing amounts
    rebalancing = []
    for security_type, diff in allocation_diff.items():
        if abs(diff) >= 1:  # Only include meaningful differences
            action = "reduce" if diff > 0 else "increase"
            amount = abs(diff) / 100 * total_value
            
            rebalancing.append({
                "security_type": security_type,
                "action": action,
                "current_percentage": current_allocation.get(security_type, 0),
                "target_percentage": target_allocation.get(security_type, 0),
                "difference_percentage": abs(diff),
                "amount": amount
            })
    
    # Sort rebalancing by amount (descending)
    rebalancing.sort(key=lambda x: x["amount"], reverse=True)
    
    # Calculate allocation drift score (0-100)
    # Lower drift = higher score
    total_drift = sum(abs(diff) for diff in allocation_diff.values())
    allocation_drift_score = max(0, 100 - total_drift)
    
    return {
        "portfolio_value": total_value,
        "current_allocation": current_allocation,
        "target_allocation": target_allocation,
        "allocation_difference": allocation_diff,
        "rebalancing_recommendations": rebalancing,
        "allocation_metrics": {
            "total_drift_percentage": total_drift,
            "allocation_drift_score": allocation_drift_score,
            "needs_rebalancing": total_drift > 10,  # Suggest rebalancing if total drift > 10%
            "largest_overweight": max(allocation_diff.items(), key=lambda x: x[1]) if allocation_diff else None,
            "largest_underweight": min(allocation_diff.items(), key=lambda x: x[1]) if allocation_diff else None
        },
        "analysis_date": datetime.now().isoformat()
    }


# Helper Functions

def calculate_coefficient_of_variation(values: List[float]) -> float:
    """
    Calculate the coefficient of variation (CV) for a list of values.
    
    Args:
        values: List of numeric values
        
    Returns:
        Coefficient of variation (standard deviation / mean)
    """
    if not values or sum(values) == 0:
        return 0
        
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    std_dev = math.sqrt(variance)
    
    return std_dev / mean if mean != 0 else 0


def is_income_stable(monthly_income: List[float]) -> bool:
    """
    Determine if income is stable based on coefficient of variation.
    
    Args:
        monthly_income: List of monthly income values
        
    Returns:
        True if income is stable, False otherwise
    """
    cv = calculate_coefficient_of_variation(monthly_income)
    return cv < 0.2  # Less than 20% variation is considered stable


def calculate_monthly_growth_rate(months: List[str], monthly_totals: Dict[str, float]) -> float:
    """
    Calculate monthly income growth rate.
    
    Args:
        months: List of months in YYYY-MM format
        monthly_totals: Dictionary mapping months to income totals
        
    Returns:
        Monthly growth rate as a percentage
    """
    if len(months) < 2:
        return 0
        
    sorted_months = sorted(months)
    first_month = sorted_months[0]
    last_month = sorted_months[-1]
    
    first_income = monthly_totals[first_month]
    last_income = monthly_totals[last_month]
    
    if first_income <= 0:
        return 0
        
    # Calculate number of months between first and last
    first_date = datetime.strptime(first_month, "%Y-%m")
    last_date = datetime.strptime(last_month, "%Y-%m")
    months_diff = (last_date.year - first_date.year) * 12 + (last_date.month - first_date.month)
    
    if months_diff <= 0:
        return 0
        
    # Calculate compound monthly growth rate
    growth_rate = (last_income / first_income) ** (1 / months_diff) - 1
    
    return growth_rate * 100  # Convert to percentage


def detect_pay_frequency(income_transactions: List[Transaction]) -> str:
    """
    Detect the frequency of income payments.
    
    Args:
        income_transactions: List of income transactions
        
    Returns:
        Detected pay frequency (weekly, biweekly, monthly, etc.)
    """
    if not income_transactions:
        return "unknown"
        
    # Sort transactions by date
    sorted_txns = sorted(income_transactions, key=lambda t: t.date)
    
    # Calculate intervals between transactions
    intervals = []
    for i in range(len(sorted_txns) - 1):
        date1 = datetime.strptime(sorted_txns[i].date, "%Y-%m-%d")
        date2 = datetime.strptime(sorted_txns[i+1].date, "%Y-%m-%d")
        interval = (date2 - date1).days
        intervals.append(interval)
    
    if not intervals:
        return "unknown"
        
    # Calculate average interval
    avg_interval = sum(intervals) / len(intervals)
    
    # Determine frequency based on average interval
    if 6 <= avg_interval <= 8:
        return "weekly"
    elif 13 <= avg_interval <= 15:
        return "biweekly"
    elif 28 <= avg_interval <= 31:
        return "monthly"
    elif 13 <= avg_interval <= 16:
        return "semi-monthly"
    elif 85 <= avg_interval <= 95:
        return "quarterly"
    elif 350 <= avg_interval <= 380:
        return "annual"
    else:
        return "irregular"


def analyze_day_of_month_pattern(income_transactions: List[Transaction]) -> Dict[str, Any]:
    """
    Analyze the day of month pattern for income transactions.
    
    Args:
        income_transactions: List of income transactions
        
    Returns:
        Dictionary with day of month pattern analysis
    """
    if not income_transactions:
        return {"pattern": "unknown"}
        
    # Extract day of month for each transaction
    days_of_month = []
    for transaction in income_transactions:
        date_obj = datetime.strptime(transaction.date, "%Y-%m-%d")
        days_of_month.append(date_obj.day)
    
    # Count occurrences of each day
    day_counts = {}
    for day in days_of_month:
        if day not in day_counts:
            day_counts[day] = 0
        day_counts[day] += 1
    
    # Find the most common day(s)
    max_count = max(day_counts.values()) if day_counts else 0
    common_days = [day for day, count in day_counts.items() if count == max_count]
    
    # Determine if there's a clear pattern
    if max_count >= len(income_transactions) * 0.7:  # 70% of transactions on same day
        if len(common_days) == 1:
            day = common_days[0]
            if day <= 5:
                return {"pattern": "beginning_of_month", "day": day}
            elif 10 <= day <= 20:
                return {"pattern": "middle_of_month", "day": day}
            elif day >= 25:
                return {"pattern": "end_of_month", "day": day}
            else:
                return {"pattern": "specific_day", "day": day}
        elif len(common_days) == 2 and sorted(common_days)[0] <= 15 and sorted(common_days)[1] >= 15:
            return {"pattern": "twice_monthly", "days": common_days}
    
    # Check for last day of month pattern
    last_day_count = sum(1 for transaction in income_transactions if is_last_day_of_month(transaction.date))
    if last_day_count >= len(income_transactions) * 0.7:
        return {"pattern": "last_day_of_month"}
    
    # No clear pattern
    return {
        "pattern": "irregular",
        "day_distribution": day_counts
    }


def is_last_day_of_month(date_str: str) -> bool:
    """
    Check if a date is the last day of the month.
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        
    Returns:
        True if date is the last day of the month, False otherwise
    """
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    next_day = date_obj + timedelta(days=1)
    return date_obj.month != next_day.month


def calculate_debt_repayment_savings(
    liabilities: List[Liability],
    monthly_extra: float
) -> Dict[str, Any]:
    """
    Calculate potential savings from debt repayment strategy.
    
    Args:
        liabilities: List of liabilities
        monthly_extra: Extra monthly payment amount
        
    Returns:
        Dictionary with savings analysis
    """
    if not liabilities:
        return {
            "total_interest_saved": 0,
            "months_saved": 0
        }
    
    # This is a simplified calculation
    # In a real implementation, this would use amortization schedules
    
    # Calculate total interest without extra payments
    total_interest_standard = 0
    for liability in liabilities:
        if liability.interest_rate and liability.outstanding_balance and liability.payment_amount:
            # Simple interest calculation (very approximate)
            years_to_payoff = liability.outstanding_balance / (liability.payment_amount * 12)
            total_interest_standard += liability.outstanding_balance * liability.interest_rate / 100 * years_to_payoff
    
    # Calculate total interest with extra payments
    # Distribute extra payment proportionally to highest interest rate first
    total_interest_accelerated = total_interest_standard * 0.8  # Simplified approximation
    
    # Calculate months saved
    months_saved = 12  # Simplified approximation
    
    return {
        "total_interest_saved": total_interest_standard - total_interest_accelerated,
        "months_saved": months_saved,
        "percent_interest_saved": (1 - total_interest_accelerated / total_interest_standard) * 100 if total_interest_standard > 0 else 0
    }


def get_debt_status(debt_to_income: float) -> str:
    """
    Get debt status based on debt-to-income ratio.
    
    Args:
        debt_to_income: Debt-to-income ratio as a percentage
        
    Returns:
        Debt status description
    """
    if debt_to_income < 20:
        return "excellent"
    elif debt_to_income < 36:
        return "good"
    elif debt_to_income < 43:
        return "fair"
    elif debt_to_income < 50:
        return "poor"
    else:
        return "critical"


def get_debt_recommendations(debt_to_income: float, total_debt: float, income: float) -> List[str]:
    """
    Get debt recommendations based on debt metrics.
    
    Args:
        debt_to_income: Debt-to-income ratio as a percentage
        total_debt: Total debt amount
        income: Monthly income
        
    Returns:
        List of debt recommendations
    """
    recommendations = []
    
    if debt_to_income >= 43:
        recommendations.append("Consider debt consolidation to reduce interest rates")
        recommendations.append("Prioritize paying off high-interest debt first")
    
    if debt_to_income >= 36:
        recommendations.append("Avoid taking on additional debt until DTI ratio improves")
    
    if total_debt > income * 12:  # Debt exceeds annual income
        recommendations.append("Focus on increasing income or reducing expenses to accelerate debt payoff")
    
    if debt_to_income < 20 and total_debt > 0:
        recommendations.append("Consider investing additional funds instead of accelerating low-interest debt payoff")
    
    return recommendations


def calculate_months_to_savings_goal(
    goal_amount: float,
    current_savings: float,
    monthly_contribution: float,
    annual_interest_rate: float
) -> float:
    """
    Calculate months needed to reach a savings goal.
    
    Args:
        goal_amount: Target savings amount
        current_savings: Current savings amount
        monthly_contribution: Monthly contribution amount
        annual_interest_rate: Annual interest rate (as decimal)
        
    Returns:
        Number of months needed to reach goal
    """
    if current_savings >= goal_amount:
        return 0
        
    if monthly_contribution <= 0:
        return float('inf')
        
    # If no interest, simple calculation
    if annual_interest_rate <= 0:
        return math.ceil((goal_amount - current_savings) / monthly_contribution)
    
    # With interest, use compound interest formula
    monthly_rate = annual_interest_rate / 12
    
    # Formula: P(1+r)^n + PMT*((1+r)^n - 1)/r = Goal
    # Solving for n (number of months)
    
    # This is an approximation using logarithms
    numerator = math.log(goal_amount * monthly_rate + monthly_contribution) - math.log(current_savings * monthly_rate + monthly_contribution)
    denominator = math.log(1 + monthly_rate)
    
    months = numerator / denominator
    return math.ceil(months)


def calculate_required_contribution(
    goal_amount: float,
    current_savings: float,
    months: int,
    annual_interest_rate: float
) -> float:
    """
    Calculate required monthly contribution to reach a savings goal.
    
    Args:
        goal_amount: Target savings amount
        current_savings: Current savings amount
        months: Number of months to reach goal
        annual_interest_rate: Annual interest rate (as decimal)
        
    Returns:
        Required monthly contribution
    """
    if current_savings >= goal_amount:
        return 0
        
    if months <= 0:
        return goal_amount - current_savings
        
    # If no interest, simple calculation
    if annual_interest_rate <= 0:
        return (goal_amount - current_savings) / months
    
    # With interest, use compound interest formula
    monthly_rate = annual_interest_rate / 12
    
    # Formula: P(1+r)^n + PMT*((1+r)^n - 1)/r = Goal
    # Solving for PMT (monthly contribution)
    
    future_value_factor = (1 + monthly_rate) ** months
    
    numerator = goal_amount - current_savings * future_value_factor
    denominator = (future_value_factor - 1) / monthly_rate
    
    return numerator / denominator


def get_risk_level(risk_score: float) -> str:
    """
    Get risk level description based on risk score.
    
    Args:
        risk_score: Portfolio risk score (0-100)
        
    Returns:
        Risk level description
    """
    if risk_score < 20:
        return "very_conservative"
    elif risk_score < 40:
        return "conservative"
    elif risk_score < 60:
        return "moderate"
    elif risk_score < 80:
        return "aggressive"
    else:
        return "very_aggressive"


def is_aligned_with_risk_tolerance(risk_score: float, risk_tolerance: str) -> bool:
    """
    Check if portfolio risk is aligned with stated risk tolerance.
    
    Args:
        risk_score: Portfolio risk score (0-100)
        risk_tolerance: Stated risk tolerance (conservative, moderate, aggressive)
        
    Returns:
        True if aligned, False otherwise
    """
    if risk_tolerance == "conservative" and risk_score < 40:
        return True
    elif risk_tolerance == "moderate" and 30 <= risk_score <= 70:
        return True
    elif risk_tolerance == "aggressive" and risk_score > 60:
        return True
    else:
        return False


# Register tools with the registry
def register_tools(registry: ToolRegistry) -> None:
    """Register all finance tools with the tool registry."""
    
    # Account Management Tools
    registry.register_tool(
        "create_link_token",
        create_link_token,
        "Create a Link token for initializing Plaid Link",
        AccountLinkInput
    )
    
    registry.register_tool(
        "exchange_public_token",
        exchange_public_token,
        "Exchange a public token from Link for an access token",
        AccessTokenExchangeInput
    )
    
    registry.register_tool(
        "get_accounts",
        get_accounts,
        "Get accounts for a specific access token",
        AccountsGetInput
    )
    
    registry.register_tool(
        "get_account_balances",
        get_account_balances,
        "Get balances for accounts",
        AccountBalancesInput
    )
    
    registry.register_tool(
        "get_account_identity",
        get_account_identity,
        "Get identity information for accounts",
        AccountIdentityInput
    )
    
    # Transaction Analysis Tools
    registry.register_tool(
        "get_transactions",
        get_transactions,
        "Get transactions for accounts",
        TransactionsGetInput
    )
    
    registry.register_tool(
        "categorize_transactions",
        categorize_transactions,
        "Categorize a list of transactions",
        TransactionCategorizeInput
    )
    
    registry.register_tool(
        "search_transactions",
        search_transactions,
        "Search for transactions matching specific criteria",
        TransactionSearchInput
    )
    
    registry.register_tool(
        "enrich_transactions",
        enrich_transactions,
        "Enrich transaction data with additional information",
        TransactionEnrichInput
    )
    
    # Budget Planning Tools
    registry.register_tool(
        "create_budget",
        create_budget,
        "Create a budget plan",
        BudgetCreateInput
    )
    
    registry.register_tool(
        "analyze_budget",
        analyze_budget,
        "Analyze budget performance against actual spending",
        BudgetAnalysisInput
    )
    
    registry.register_tool(
        "forecast_cash_flow",
        forecast_cash_flow,
        "Forecast future cash flow based on historical transactions",
        CashFlowForecastInput
    )
    
    # Income Verification Tools
    registry.register_tool(
        "verify_income",
        verify_income,
        "Verify income based on transaction history",
        IncomeVerificationInput
    )
    
    registry.register_tool(
        "analyze_income_patterns",
        analyze_income_patterns,
        "Analyze income patterns and trends",
        IncomeAnalysisInput
    )
    
    # Financial Health Tools
    registry.register_tool(
        "assess_financial_health",
        assess_financial_health,
        "Assess overall financial health",
        FinancialHealthAssessmentInput
    )
    
    registry.register_tool(
        "analyze_debt",
        analyze_debt,
        "Analyze debt and provide repayment strategies",
        DebtAnalysisInput
    )
    
    registry.register_tool(
        "plan_savings_goal",
        plan_savings_goal,
        "Plan for achieving a savings goal",
        SavingsGoalInput
    )
    
    # Spending Analysis Tools
    registry.register_tool(
        "analyze_spending",
        analyze_spending,
        "Analyze spending patterns",
        SpendingAnalysisInput
    )
    
    registry.register_tool(
        "analyze_merchants",
        analyze_merchants,
        "Analyze spending by merchant",
        MerchantAnalysisInput
    )
    
    registry.register_tool(
        "identify_recurring_expenses",
        identify_recurring_expenses,
        "Identify recurring expenses from transaction history",
        RecurringExpensesInput
    )
    
    # Investment Tracking Tools
    registry.register_tool(
        "get_investment_holdings",
        get_investment_holdings,
        "Get investment holdings for accounts",
        InvestmentHoldingsInput
    )
    
    registry.register_tool(
        "get_investment_transactions",
        get_investment_transactions,
        "Get investment transactions for accounts",
        InvestmentTransactionsInput
    )
    
    registry.register_tool(
        "analyze_portfolio",
        analyze_portfolio,
        "Analyze investment portfolio",
        PortfolioAnalysisInput
    )
    
    registry.register_tool(
        "analyze_asset_allocation",
        analyze_asset_allocation,
        "Analyze asset allocation of investment portfolio",
        AssetAllocationInput
    )
