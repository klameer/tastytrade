"""
Tastytrade API Client
Handles OAuth2 authentication and provides methods to interact with the tastytrade API.
"""

import requests
import time
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from config import config


class TastytradeClient:
    """Client for interacting with the tastytrade API."""
    
    def __init__(self):
        """Initialize the Tastytrade client."""
        self.base_url = config.api_url
        self.client_secret = config.client_secret
        self.refresh_token = config.refresh_token
        
        # Token management
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        
        # Session management
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        # Authenticate on initialization
        self._authenticate()
    
    def _authenticate(self) -> None:
        """
        Authenticate using OAuth2 refresh token to obtain an access token.
        Access tokens are valid for 15 minutes.
        """
        url = f"{self.base_url}/oauth/token"
        
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_secret": self.client_secret
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            self.access_token = data.get('access_token')
            
            # Access tokens are valid for 15 minutes
            # Set expiration time to 14 minutes to refresh before actual expiry
            self.token_expires_at = datetime.now() + timedelta(minutes=14)
            
            # Update session headers with new access token
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}'
            })
            
            print("✓ Authentication successful!")
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Authentication failed: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            raise
    
    def _ensure_authenticated(self) -> None:
        """Ensure we have a valid access token, refreshing if necessary."""
        if not self.access_token or datetime.now() >= self.token_expires_at:
            print("Token expired or missing, refreshing...")
            self._authenticate()
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make an authenticated request to the tastytrade API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., '/customers/me')
            **kwargs: Additional arguments to pass to requests
            
        Returns:
            JSON response as dictionary
        """
        self._ensure_authenticated()
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"✗ API request failed: {method} {endpoint}")
            print(f"Error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            raise
    
    # Account & Customer Methods
    
    def get_customer_info(self) -> Dict[str, Any]:
        """
        Get information about the authenticated customer.
        
        Returns:
            Customer information including name, email, accounts, etc.
        """
        return self._request('GET', '/customers/me')
    
    def get_accounts(self) -> List[Dict[str, Any]]:
        """
        Get all accounts for the authenticated customer.
        
        Returns:
            List of account objects
        """
        response = self._request('GET', '/customers/me/accounts')
        accounts = response.get('data', {}).get('items', [])
        return accounts
    
    def get_account_numbers(self) -> List[str]:
        """
        Get list of account numbers for the customer.
        
        Returns:
            List of account numbers
        """
        accounts = self.get_accounts()
        return [acc.get('account', {}).get('account-number') for acc in accounts if acc.get('account')]
    
    # Balance Methods
    
    def get_balances(self, account_number: str) -> Dict[str, Any]:
        """
        Get account balances including cash, buying power, and net liquidating value.
        
        Args:
            account_number: The account number to fetch balances for
            
        Returns:
            Balance information
        """
        endpoint = f'/accounts/{account_number}/balances'
        return self._request('GET', endpoint)
    
    def get_all_balances(self) -> Dict[str, Dict[str, Any]]:
        """
        Get balances for all accounts.
        
        Returns:
            Dictionary mapping account numbers to their balances
        """
        account_numbers = self.get_account_numbers()
        balances = {}
        
        for account_number in account_numbers:
            try:
                balances[account_number] = self.get_balances(account_number)
            except Exception as e:
                print(f"Failed to fetch balances for {account_number}: {e}")
                
        return balances
    
    # Position Methods
    
    def get_positions(self, account_number: str) -> List[Dict[str, Any]]:
        """
        Get all positions for an account.
        
        Args:
            account_number: The account number to fetch positions for
            
        Returns:
            List of position objects
        """
        endpoint = f'/accounts/{account_number}/positions'
        response = self._request('GET', endpoint)
        return response.get('data', {}).get('items', [])
    
    def get_all_positions(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get positions for all accounts.
        
        Returns:
            Dictionary mapping account numbers to their positions
        """
        account_numbers = self.get_account_numbers()
        positions = {}
        
        for account_number in account_numbers:
            try:
                positions[account_number] = self.get_positions(account_number)
            except Exception as e:
                print(f"Failed to fetch positions for {account_number}: {e}")
                
        return positions
    
    # Order Methods
    
    def get_live_orders(self, account_number: str) -> List[Dict[str, Any]]:
        """
        Get all live (unfilled) orders for an account.
        
        Args:
            account_number: The account number to fetch orders for
            
        Returns:
            List of live order objects
        """
        endpoint = f'/accounts/{account_number}/orders/live'
        response = self._request('GET', endpoint)
        return response.get('data', {}).get('items', [])
    
    def get_orders(self, account_number: str, start_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get order history for an account.
        
        Args:
            account_number: The account number to fetch orders for
            start_date: Optional start date for filtering (YYYY-MM-DD format)
            
        Returns:
            List of order objects
        """
        endpoint = f'/accounts/{account_number}/orders'
        params = {}
        if start_date:
            params['start-date'] = start_date
            
        response = self._request('GET', endpoint, params=params)
        return response.get('data', {}).get('items', [])
    
    # Transaction Methods
    
    def get_transactions(self, account_number: str, start_date: Optional[str] = None, 
                        end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get transaction history for an account.
        
        Args:
            account_number: The account number to fetch transactions for
            start_date: Optional start date for filtering (YYYY-MM-DD format)
            end_date: Optional end date for filtering (YYYY-MM-DD format)
            
        Returns:
            List of transaction objects
        """
        endpoint = f'/accounts/{account_number}/transactions'
        params = {}
        if start_date:
            params['start-date'] = start_date
        if end_date:
            params['end-date'] = end_date
            
        response = self._request('GET', endpoint, params=params)
        return response.get('data', {}).get('items', [])
    
    # Market Data Methods
    
    def get_option_chain(self, symbol: str) -> Dict[str, Any]:
        """
        Get the complete option chain for a given underlying symbol.
        
        Args:
            symbol: The underlying symbol (e.g., 'SPY', 'AAPL')
            
        Returns:
            Option chain data including strikes, expirations, Greeks, etc.
        """
        endpoint = f'/option-chains/{symbol}/nested'
        return self._request('GET', endpoint)
    
    def get_option_chain_compact(self, symbol: str) -> Dict[str, Any]:
        """
        Get a compact version of the option chain.
        
        Args:
            symbol: The underlying symbol (e.g., 'SPY', 'AAPL')
            
        Returns:
            Compact option chain data
        """
        endpoint = f'/option-chains/{symbol}/compact'
        return self._request('GET', endpoint)
    
    def search_symbols(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for symbols by name or ticker.
        
        Args:
            query: Search query (symbol or company name)
            
        Returns:
            List of matching symbols
        """
        endpoint = '/symbols/search'
        params = {'symbol': query}
        response = self._request('GET', endpoint, params=params)
        return response.get('data', {}).get('items', [])
    
    def get_market_metrics(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """
        Get market metrics (IV rank, IV percentile, etc.) for symbols.
        
        Args:
            symbols: List of symbol strings
            
        Returns:
            Market metrics for each symbol
        """
        endpoint = '/market-metrics'
        # Convert list to comma-separated string
        symbols_str = ','.join(symbols)
        params = {'symbols': symbols_str}
        response = self._request('GET', endpoint, params=params)
        return response.get('data', {}).get('items', [])
    
    def get_equity_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get real-time quote for an equity symbol.
        
        Args:
            symbol: The equity symbol
            
        Returns:
            Quote data
        """
        endpoint = f'/instruments/equities/{symbol}'
        return self._request('GET', endpoint)


if __name__ == "__main__":
    """Test the client."""
    try:
        client = TastytradeClient()
        
        print("\n--- Customer Info ---")
        customer = client.get_customer_info()
        print(f"Customer: {customer.get('data', {}).get('email')}")
        
        print("\n--- Accounts ---")
        accounts = client.get_account_numbers()
        print(f"Account Numbers: {accounts}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
