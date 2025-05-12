"""
Plaid MCP Client for RuTwin Crew

This module provides a client for interacting with the Plaid API to perform
financial operations such as account access, transaction retrieval, balance checking,
transfer management, identity verification, and more.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Union, Any

import requests
from pydantic import BaseModel, Field

from ru_twin.mcp_client import MCPClient
from ru_twin.third_party_gateway import ThirdPartyGateway


class PlaidEnvironment(str, Enum):
    """Plaid API environments"""
    SANDBOX = "sandbox"
    DEVELOPMENT = "development"
    PRODUCTION = "production"


class AccountType(str, Enum):
    """Types of financial accounts"""
    DEPOSITORY = "depository"
    CREDIT = "credit"
    LOAN = "loan"
    INVESTMENT = "investment"
    OTHER = "other"


class AccountSubtype(str, Enum):
    """Subtypes of financial accounts"""
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT_CARD = "credit card"
    MORTGAGE = "mortgage"
    STUDENT = "student"
    BROKERAGE = "brokerage"
    RETIREMENT = "retirement"
    # Many more subtypes exist in Plaid's API


class TransactionCategory(BaseModel):
    """Model for transaction category"""
    primary: str
    detailed: Optional[str] = None


class Account(BaseModel):
    """Model for a financial account"""
    account_id: str
    mask: Optional[str] = None
    name: str
    official_name: Optional[str] = None
    type: AccountType
    subtype: Optional[AccountSubtype] = None
    verification_status: Optional[str] = None
    balances: Dict[str, Any]
    permissions: Optional[List[str]] = None


class Transaction(BaseModel):
    """Model for a financial transaction"""
    transaction_id: str
    account_id: str
    amount: float
    date: str
    name: str
    merchant_name: Optional[str] = None
    pending: bool = False
    category: Optional[List[str]] = None
    category_id: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    payment_channel: Optional[str] = None
    authorized_date: Optional[str] = None
    payment_meta: Optional[Dict[str, Any]] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None


class Balance(BaseModel):
    """Model for account balance"""
    account_id: str
    current: float
    available: Optional[float] = None
    limit: Optional[float] = None
    iso_currency_code: str
    unofficial_currency_code: Optional[str] = None
    last_updated_datetime: Optional[datetime] = None


class Identity(BaseModel):
    """Model for user identity information"""
    account_id: str
    names: List[str]
    emails: List[Dict[str, str]]
    phone_numbers: List[Dict[str, str]]
    addresses: List[Dict[str, Any]]


class Investment(BaseModel):
    """Model for investment holdings"""
    account_id: str
    security_id: str
    name: str
    quantity: float
    price: float
    value: float
    iso_currency_code: str
    institution_value: Optional[float] = None
    cost_basis: Optional[float] = None
    type: Optional[str] = None


class Liability(BaseModel):
    """Model for liability information"""
    account_id: str
    type: str
    origination_date: Optional[str] = None
    term: Optional[int] = None
    interest_rate: Optional[float] = None
    payment_amount: Optional[float] = None
    outstanding_balance: Optional[float] = None
    origination_principal: Optional[float] = None
    next_payment_due_date: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class PlaidClient(MCPClient):
    """
    Client for interacting with Plaid API.
    
    This client handles authentication and provides methods for financial operations
    including account access, transaction retrieval, balance checking, and more.
    """
    
    def __init__(
        self,
        client_id: str,
        secret: str,
        environment: PlaidEnvironment = PlaidEnvironment.DEVELOPMENT,
        gateway: Optional[ThirdPartyGateway] = None,
    ):
        """
        Initialize the Plaid client.
        
        Args:
            client_id: The Plaid client ID
            secret: The Plaid secret key
            environment: The Plaid environment to use (sandbox, development, production)
            gateway: Optional ThirdPartyGateway for routing requests
        """
        super().__init__(gateway)
        self.client_id = client_id
        self.secret = secret
        self.environment = environment
        self.logger = logging.getLogger(__name__)
        
        # API endpoints
        self.base_url = f"https://{environment}.plaid.com"
        
        # Headers for API requests
        self.headers = {
            "Content-Type": "application/json",
            "PLAID-CLIENT-ID": self.client_id,
            "PLAID-SECRET": self.secret
        }
        
        # Rate limiting parameters
        self.max_retries = 5
        self.retry_delay = 1.0
        self.last_request_time = 0
        self.min_request_interval = 0.5  # seconds between requests to avoid rate limits
        
        # Store access tokens for different users
        self.access_tokens = {}

    def _handle_rate_limiting(self) -> None:
        """Handle rate limiting by ensuring minimum time between requests."""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            time.sleep(sleep_time)
            
        self.last_request_time = time.time()

    def _make_request(
        self, 
        endpoint: str, 
        data: Dict[str, Any], 
        method: str = "POST"
    ) -> Dict[str, Any]:
        """
        Make a request to the Plaid API.
        
        Args:
            endpoint: API endpoint path
            data: Request payload
            method: HTTP method (POST, GET, etc.)
            
        Returns:
            API response as a dictionary
            
        Raises:
            Exception: If the API request fails after all retries
        """
        url = f"{self.base_url}{endpoint}"
        
        retries = 0
        while retries < self.max_retries:
            self._handle_rate_limiting()
            
            try:
                if method.upper() == "POST":
                    response = requests.post(url, headers=self.headers, json=data)
                elif method.upper() == "GET":
                    response = requests.get(url, headers=self.headers, params=data)
                else:
                    response = requests.request(method, url, headers=self.headers, json=data)
                
                # Check for rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', self.retry_delay))
                    self.logger.warning(f"Rate limited by Plaid. Retrying after {retry_after} seconds")
                    time.sleep(retry_after)
                    retries += 1
                    continue
                
                # Handle other errors
                if response.status_code != 200:
                    error_data = response.json() if response.content else {"error": {"message": "Unknown error"}}
                    error_message = error_data.get("error", {}).get("message", "Unknown error")
                    error_code = error_data.get("error", {}).get("error_code", "UNKNOWN_ERROR")
                    
                    self.logger.error(f"Plaid API error: {error_code} - {error_message}")
                    
                    # Retryable errors
                    if error_code in ["INTERNAL_SERVER_ERROR", "PLANNED_MAINTENANCE"]:
                        retries += 1
                        time.sleep(self.retry_delay * (2 ** retries))  # Exponential backoff
                        continue
                    
                    raise Exception(f"Plaid API error: {error_code} - {error_message}")
                
                # Parse and return successful response
                return response.json()
                
            except requests.RequestException as e:
                self.logger.error(f"Request error: {e}")
                retries += 1
                time.sleep(self.retry_delay * (2 ** retries))  # Exponential backoff
                
        raise Exception(f"Failed to make Plaid API request after {self.max_retries} retries")

    # Authentication and Link Methods
    
    def create_link_token(
        self,
        user_id: str,
        client_name: str,
        products: List[str],
        country_codes: List[str] = ["US"],
        language: str = "en",
        webhook: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a Link token for initializing Plaid Link.
        
        Args:
            user_id: Client-generated ID for the user
            client_name: Name of your application
            products: List of Plaid products to use
            country_codes: List of country codes
            language: Language to display Link in
            webhook: Webhook URL for notifications
            
        Returns:
            Dictionary containing the link_token
        """
        data = {
            "client_id": self.client_id,
            "secret": self.secret,
            "user": {
                "client_user_id": user_id
            },
            "client_name": client_name,
            "products": products,
            "country_codes": country_codes,
            "language": language
        }
        
        if webhook:
            data["webhook"] = webhook
        
        return self._make_request("/link/token/create", data)

    def exchange_public_token(self, public_token: str) -> Dict[str, Any]:
        """
        Exchange a public token from Link for an access token.
        
        Args:
            public_token: The public token from Plaid Link
            
        Returns:
            Dictionary containing access_token and item_id
        """
        data = {
            "client_id": self.client_id,
            "secret": self.secret,
            "public_token": public_token
        }
        
        response = self._make_request("/item/public_token/exchange", data)
        
        # Store the access token for future use
        if "access_token" in response:
            self.access_tokens[response.get("item_id")] = response.get("access_token")
        
        return response

    def set_access_token(self, item_id: str, access_token: str) -> None:
        """
        Set an access token for a specific item.
        
        Args:
            item_id: The Plaid item ID
            access_token: The Plaid access token
        """
        self.access_tokens[item_id] = access_token

    def get_access_token(self, item_id: str) -> Optional[str]:
        """
        Get an access token for a specific item.
        
        Args:
            item_id: The Plaid item ID
            
        Returns:
            The access token if available, None otherwise
        """
        return self.access_tokens.get(item_id)

    # Account Information Methods
    
    def get_accounts(self, access_token: str) -> List[Account]:
        """
        Get accounts for a specific access token.
        
        Args:
            access_token: The Plaid access token
            
        Returns:
            List of Account objects
        """
        data = {
            "client_id": self.client_id,
            "secret": self.secret,
            "access_token": access_token
        }
        
        response = self._make_request("/accounts/get", data)
        
        accounts = []
        for account_data in response.get("accounts", []):
            account = Account(
                account_id=account_data.get("account_id"),
                mask=account_data.get("mask"),
                name=account_data.get("name"),
                official_name=account_data.get("official_name"),
                type=account_data.get("type"),
                subtype=account_data.get("subtype"),
                verification_status=account_data.get("verification_status"),
                balances=account_data.get("balances", {}),
                permissions=account_data.get("permissions")
            )
            accounts.append(account)
        
        return accounts

    def get_balances(self, access_token: str, account_ids: Optional[List[str]] = None) -> List[Balance]:
        """
        Get balances for accounts.
        
        Args:
            access_token: The Plaid access token
            account_ids: Optional list of account IDs to filter by
            
        Returns:
            List of Balance objects
        """
        data = {
            "client_id": self.client_id,
            "secret": self.secret,
            "access_token": access_token
        }
        
        if account_ids:
            data["options"] = {"account_ids": account_ids}
        
        response = self._make_request("/accounts/balance/get", data)
        
        balances = []
        for account_data in response.get("accounts", []):
            balance_data = account_data.get("balances", {})
            balance = Balance(
                account_id=account_data.get("account_id"),
                current=balance_data.get("current", 0.0),
                available=balance_data.get("available"),
                limit=balance_data.get("limit"),
                iso_currency_code=balance_data.get("iso_currency_code", "USD"),
                unofficial_currency_code=balance_data.get("unofficial_currency_code"),
                last_updated_datetime=datetime.now()
            )
            balances.append(balance)
        
        return balances

    def get_identity(self, access_token: str) -> List[Identity]:
        """
        Get identity information for accounts.
        
        Args:
            access_token: The Plaid access token
            
        Returns:
            List of Identity objects
        """
        data = {
            "client_id": self.client_id,
            "secret": self.secret,
            "access_token": access_token
        }
        
        response = self._make_request("/identity/get", data)
        
        identities = []
        for account_data in response.get("accounts", []):
            account_id = account_data.get("account_id")
            owners = response.get("identity", {}).get("owners", [])
            
            for owner in owners:
                identity = Identity(
                    account_id=account_id,
                    names=owner.get("names", []),
                    emails=owner.get("emails", []),
                    phone_numbers=owner.get("phone_numbers", []),
                    addresses=owner.get("addresses", [])
                )
                identities.append(identity)
        
        return identities

    # Transaction Methods
    
    def get_transactions(
        self,
        access_token: str,
        start_date: str,
        end_date: str,
        account_ids: Optional[List[str]] = None,
        count: int = 100,
        offset: int = 0
    ) -> List[Transaction]:
        """
        Get transactions for accounts.
        
        Args:
            access_token: The Plaid access token
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            account_ids: Optional list of account IDs to filter by
            count: Maximum number of transactions to return
            offset: Number of transactions to skip
            
        Returns:
            List of Transaction objects
        """
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
        
        transactions = []
        for transaction_data in response.get("transactions", []):
            transaction = Transaction(
                transaction_id=transaction_data.get("transaction_id"),
                account_id=transaction_data.get("account_id"),
                amount=transaction_data.get("amount", 0.0),
                date=transaction_data.get("date"),
                name=transaction_data.get("name"),
                merchant_name=transaction_data.get("merchant_name"),
                pending=transaction_data.get("pending", False),
                category=transaction_data.get("category"),
                category_id=transaction_data.get("category_id"),
                location=transaction_data.get("location"),
                payment_channel=transaction_data.get("payment_channel"),
                authorized_date=transaction_data.get("authorized_date"),
                payment_meta=transaction_data.get("payment_meta"),
                logo_url=transaction_data.get("logo_url"),
                website=transaction_data.get("website")
            )
            transactions.append(transaction)
        
        return transactions

    def get_transactions_sync(
        self,
        access_token: str,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get transactions using the sync endpoint (more efficient for large datasets).
        
        Args:
            access_token: The Plaid access token
            cursor: Cursor from a previous sync request
            
        Returns:
            Dictionary containing added, modified, and removed transactions, plus a cursor
        """
        data = {
            "client_id": self.client_id,
            "secret": self.secret,
            "access_token": access_token
        }
        
        if cursor:
            data["cursor"] = cursor
        
        return self._make_request("/transactions/sync", data)

    def categorize_transaction(self, description: str, amount: float) -> List[str]:
        """
        Categorize a transaction based on its description and amount.
        
        Args:
            description: Transaction description
            amount: Transaction amount
            
        Returns:
            List of possible categories
        """
        # Note: Plaid doesn't have a direct endpoint for this.
        # This is a simplified implementation that could be enhanced with ML.
        keywords = {
            "restaurant": ["food", "dining"],
            "grocery": ["grocery", "supermarket", "food"],
            "transportation": ["uber", "lyft", "taxi", "transit", "transport"],
            "shopping": ["amazon", "walmart", "target", "purchase"],
            "utilities": ["electric", "water", "gas", "utility", "utilities"],
            "entertainment": ["netflix", "spotify", "hulu", "movie"],
            "travel": ["hotel", "airbnb", "airline", "flight"],
            "healthcare": ["doctor", "medical", "pharmacy", "health"]
        }
        
        description_lower = description.lower()
        possible_categories = []
        
        for category, terms in keywords.items():
            if any(term in description_lower for term in terms):
                possible_categories.append(category)
        
        if not possible_categories:
            possible_categories.append("other")
        
        return possible_categories

    # Investment Methods
    
    def get_investments_holdings(self, access_token: str) -> List[Investment]:
        """
        Get investment holdings for accounts.
        
        Args:
            access_token: The Plaid access token
            
        Returns:
            List of Investment objects
        """
        data = {
            "client_id": self.client_id,
            "secret": self.secret,
            "access_token": access_token
        }
        
        response = self._make_request("/investments/holdings/get", data)
        
        holdings = []
        for holding_data in response.get("holdings", []):
            security_data = next(
                (s for s in response.get("securities", []) if s.get("security_id") == holding_data.get("security_id")),
                {}
            )
            
            holding = Investment(
                account_id=holding_data.get("account_id"),
                security_id=holding_data.get("security_id"),
                name=security_data.get("name", "Unknown Security"),
                quantity=holding_data.get("quantity", 0.0),
                price=holding_data.get("institution_price", 0.0),
                value=holding_data.get("institution_value", 0.0),
                iso_currency_code=holding_data.get("iso_currency_code", "USD"),
                institution_value=holding_data.get("institution_value"),
                cost_basis=holding_data.get("cost_basis"),
                type=security_data.get("type")
            )
            holdings.append(holding)
        
        return holdings

    def get_investments_transactions(
        self,
        access_token: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Get investment transactions for accounts.
        
        Args:
            access_token: The Plaid access token
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Dictionary containing investment transactions
        """
        data = {
            "client_id": self.client_id,
            "secret": self.secret,
            "access_token": access_token,
            "start_date": start_date,
            "end_date": end_date
        }
        
        return self._make_request("/investments/transactions/get", data)

    # Liability Methods
    
    def get_liabilities(self, access_token: str) -> List[Liability]:
        """
        Get liability information for accounts.
        
        Args:
            access_token: The Plaid access token
            
        Returns:
            List of Liability objects
        """
        data = {
            "client_id": self.client_id,
            "secret": self.secret,
            "access_token": access_token
        }
        
        response = self._make_request("/liabilities/get", data)
        
        liabilities = []
        liabilities_data = response.get("liabilities", {})
        
        # Process student loans
        for loan in liabilities_data.get("student", []):
            account_id = loan.get("account_id")
            liability = Liability(
                account_id=account_id,
                type="student",
                origination_date=loan.get("origination_date"),
                term=loan.get("expected_payoff_date"),
                interest_rate=loan.get("interest_rate_percentage"),
                payment_amount=loan.get("payment_amount"),
                outstanding_balance=loan.get("outstanding_interest_amount"),
                origination_principal=loan.get("origination_principal_amount"),
                next_payment_due_date=loan.get("next_payment_due_date"),
                details=loan
            )
            liabilities.append(liability)
        
        # Process credit cards
        for card in liabilities_data.get("credit", []):
            account_id = card.get("account_id")
            liability = Liability(
                account_id=account_id,
                type="credit",
                interest_rate=card.get("aprs", [{}])[0].get("apr_percentage"),
                payment_amount=card.get("minimum_payment_amount"),
                outstanding_balance=card.get("last_statement_balance"),
                next_payment_due_date=card.get("next_payment_due_date"),
                details=card
            )
            liabilities.append(liability)
        
        # Process mortgages
        for mortgage in liabilities_data.get("mortgage", []):
            account_id = mortgage.get("account_id")
            liability = Liability(
                account_id=account_id,
                type="mortgage",
                origination_date=mortgage.get("origination_date"),
                term=mortgage.get("loan_term"),
                interest_rate=mortgage.get("interest_rate_percentage"),
                payment_amount=mortgage.get("payment_amount"),
                outstanding_balance=mortgage.get("outstanding_principal_balance"),
                origination_principal=mortgage.get("origination_principal_amount"),
                next_payment_due_date=mortgage.get("next_payment_due_date"),
                details=mortgage
            )
            liabilities.append(liability)
        
        return liabilities

    # Transfer Methods
    
    def create_transfer(
        self,
        access_token: str,
        account_id: str,
        amount: str,
        description: str,
        ach_class: str = "ppd",
        type: str = "debit"
    ) -> Dict[str, Any]:
        """
        Create a transfer using the Plaid API.
        
        Args:
            access_token: The Plaid access token
            account_id: The Plaid account ID
            amount: The amount to transfer (as a string, e.g. "100.00")
            description: The transfer description
            ach_class: The ACH class (ppd, ccd, tel, web)
            type: The transfer type (debit or credit)
            
        Returns:
            Dictionary containing transfer information
        """
        data = {
            "client_id": self.client_id,
            "secret": self.secret,
            "access_token": access_token,
            "account_id": account_id,
            "authorization_id": "authorization_id",  # This would need to be obtained separately
            "type": type,
            "network": "ach",
            "amount": amount,
            "description": description,
            "ach_class": ach_class,
            "user": {
                "legal_name": "Legal Name"  # This would need to be obtained separately
            }
        }
        
        return self._make_request("/transfer/create", data)

    # Auth Methods
    
    def get_auth(self, access_token: str) -> Dict[str, Any]:
        """
        Get auth information (account and routing numbers) for accounts.
        
        Args:
            access_token: The Plaid access token
            
        Returns:
            Dictionary containing auth information
        """
        data = {
            "client_id": self.client_id,
            "secret": self.secret,
            "access_token": access_token
        }
        
        return self._make_request("/auth/get", data)

    # Item Management Methods
    
    def get_item(self, access_token: str) -> Dict[str, Any]:
        """
        Get information about an item.
        
        Args:
            access_token: The Plaid access token
            
        Returns:
            Dictionary containing item information
        """
        data = {
            "client_id": self.client_id,
            "secret": self.secret,
            "access_token": access_token
        }
        
        return self._make_request("/item/get", data)

    def get_institution(self, institution_id: str) -> Dict[str, Any]:
        """
        Get information about a financial institution.
        
        Args:
            institution_id: The Plaid institution ID
            
        Returns:
            Dictionary containing institution information
        """
        data = {
            "client_id": self.client_id,
            "secret": self.secret,
            "institution_id": institution_id,
            "country_codes": ["US"]
        }
        
        return self._make_request("/institutions/get_by_id", data)

    def search_institutions(
        self,
        query: str,
        products: Optional[List[str]] = None,
        country_codes: List[str] = ["US"]
    ) -> Dict[str, Any]:
        """
        Search for financial institutions.
        
        Args:
            query: The search query
            products: Optional list of Plaid products to filter by
            country_codes: List of country codes
            
        Returns:
            Dictionary containing matching institutions
        """
        data = {
            "client_id": self.client_id,
            "secret": self.secret,
            "query": query,
            "country_codes": country_codes
        }
        
        if products:
            data["products"] = products
        
        return self._make_request("/institutions/search", data)

    # Utility Methods
    
    def categorize_transactions(self, transactions: List[Transaction]) -> Dict[str, List[Transaction]]:
        """
        Categorize a list of transactions.
        
        Args:
            transactions: List of Transaction objects
            
        Returns:
            Dictionary mapping categories to lists of transactions
        """
        categorized = {}
        
        for transaction in transactions:
            if transaction.category and len(transaction.category) > 0:
                primary_category = transaction.category[0]
                if primary_category not in categorized:
                    categorized[primary_category] = []
                categorized[primary_category].append(transaction)
            else:
                if "Uncategorized" not in categorized:
                    categorized["Uncategorized"] = []
                categorized["Uncategorized"].append(transaction)
        
        return categorized

    def calculate_spending_summary(
        self,
        transactions: List[Transaction],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate a spending summary from transactions.
        
        Args:
            transactions: List of Transaction objects
            start_date: Optional start date filter (YYYY-MM-DD)
            end_date: Optional end date filter (YYYY-MM-DD)
            
        Returns:
            Dictionary containing spending summary
        """
        # Filter transactions by date if specified
        filtered_transactions = transactions
        if start_date:
            filtered_transactions = [t for t in filtered_transactions if t.date >= start_date]
        if end_date:
            filtered_transactions = [t for t in filtered_transactions if t.date <= end_date]
        
        # Calculate total spending (positive amounts are debits in Plaid)
        total_spending = sum(t.amount for t in filtered_transactions if t.amount > 0)
        
        # Categorize spending
        categorized = self.categorize_transactions(filtered_transactions)
        category_totals = {}
        
        for category, category_transactions in categorized.items():
            category_totals[category] = sum(t.amount for t in category_transactions if t.amount > 0)
        
        # Calculate daily spending
        daily_spending = {}
        for transaction in filtered_transactions:
            if transaction.amount > 0:  # Only count debits
                if transaction.date not in daily_spending:
                    daily_spending[transaction.date] = 0
                daily_spending[transaction.date] += transaction.amount
        
        return {
            "total_spending": total_spending,
            "category_totals": category_totals,
            "daily_spending": daily_spending
        }

    def analyze_cash_flow(
        self,
        transactions: List[Transaction],
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze cash flow from transactions.
        
        Args:
            transactions: List of Transaction objects
            period_days: Number of days to analyze
            
        Returns:
            Dictionary containing cash flow analysis
        """
        # Calculate date ranges
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        # Filter transactions within date range
        date_format = "%Y-%m-%d"
        start_date_str = start_date.strftime(date_format)
        filtered_transactions = [t for t in transactions if t.date >= start_date_str]
        
        # Calculate inflows and outflows
        inflows = sum(t.amount for t in filtered_transactions if t.amount < 0)  # Credits are negative in Plaid
        outflows = sum(t.amount for t in filtered_transactions if t.amount > 0)  # Debits are positive in Plaid
        
        # Calculate net cash flow
        net_cash_flow = -inflows - outflows  # Negate inflows because they're stored as negative
        
        # Identify recurring transactions
        # This is a simplified approach - a real implementation would be more sophisticated
        recurring = []
        transaction_dict = {}
        
        for transaction in filtered_transactions:
            merchant = transaction.merchant_name or transaction.name
            if merchant not in transaction_dict:
                transaction_dict[merchant] = []
            transaction_dict[merchant].append(transaction)
        
        for merchant, merchant_transactions in transaction_dict.items():
            if len(merchant_transactions) >= 2:
                amounts = [t.amount for t in merchant_transactions]
                # If all transactions have the same amount, consider it recurring
                if len(set(amounts)) == 1:
                    recurring.append({
                        "merchant": merchant,
                        "amount": amounts[0],
                        "frequency": f"{len(merchant_transactions)} times in {period_days} days",
                        "transactions": merchant_transactions
                    })
        
        return {
            "period_days": period_days,
            "start_date": start_date_str,
            "end_date": end_date.strftime(date_format),
            "inflows": -inflows,  # Negate to make positive
            "outflows": outflows,
            "net_cash_flow": net_cash_flow,
            "recurring_transactions": recurring
        }

    def calculate_financial_health(
        self,
        balances: List[Balance],
        transactions: List[Transaction],
        liabilities: Optional[List[Liability]] = None
    ) -> Dict[str, Any]:
        """
        Calculate financial health metrics.
        
        Args:
            balances: List of Balance objects
            transactions: List of Transaction objects
            liabilities: Optional list of Liability objects
            
        Returns:
            Dictionary containing financial health metrics
        """
        # Calculate total assets (sum of account balances)
        total_assets = sum(b.current for b in balances)
        
        # Calculate total liabilities
        total_liabilities = 0
        if liabilities:
            total_liabilities = sum(l.outstanding_balance or 0 for l in liabilities)
        
        # Calculate net worth
        net_worth = total_assets - total_liabilities
        
        # Calculate monthly income and expenses
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        recent_transactions = [t for t in transactions if t.date >= thirty_days_ago]
        
        monthly_income = sum(-t.amount for t in recent_transactions if t.amount < 0)  # Credits are negative in Plaid
        monthly_expenses = sum(t.amount for t in recent_transactions if t.amount > 0)  # Debits are positive in Plaid
        
        # Calculate savings rate
        savings_rate = 0
        if monthly_income > 0:
            savings_rate = (monthly_income - monthly_expenses) / monthly_income * 100
        
        # Calculate debt-to-income ratio
        debt_to_income = 0
        if monthly_income > 0 and liabilities:
            # Estimate monthly debt payments (simplified)
            monthly_debt_payments = sum(l.payment_amount or 0 for l in liabilities)
            debt_to_income = monthly_debt_payments / monthly_income * 100
        
        # Calculate emergency fund ratio (months of expenses covered by liquid assets)
        emergency_fund_ratio = 0
        if monthly_expenses > 0:
            # Sum only checking and savings account balances
            liquid_assets = sum(
                b.available or b.current for b in balances 
                if b.subtype in ["checking", "savings"]
            )
            emergency_fund_ratio = liquid_assets / monthly_expenses
        
        return {
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "net_worth": net_worth,
            "monthly_income": monthly_income,
            "monthly_expenses": monthly_expenses,
            "savings_rate": savings_rate,
            "debt_to_income_ratio": debt_to_income,
            "emergency_fund_ratio": emergency_fund_ratio,
            "emergency_fund_months": round(emergency_fund_ratio, 1)
        }
