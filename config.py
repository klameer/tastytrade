"""
Configuration management for Tastytrade API credentials.
Loads credentials from .env file securely.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


class TastytradeConfig:
    """Configuration class for Tastytrade API credentials."""
    
    def __init__(self):
        self.client_secret = os.getenv('TASTYTRADE_CLIENT_SECRET')
        self.refresh_token = os.getenv('TASTYTRADE_REFRESH_TOKEN')
        self.api_url = os.getenv('TASTYTRADE_API_URL', 'https://api.tastytrade.com')
        
        # Validate required credentials
        self._validate()
    
    def _validate(self):
        """Validate that required credentials are present."""
        missing = []
        
        if not self.client_secret:
            missing.append('TASTYTRADE_CLIENT_SECRET')
        if not self.refresh_token:
            missing.append('TASTYTRADE_REFRESH_TOKEN')
        
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}. "
                f"Please add them to your .env file."
            )
    
    @property
    def is_configured(self) -> bool:
        """Check if all required credentials are configured."""
        return bool(self.client_secret and self.refresh_token)


# Create a global config instance
try:
    config = TastytradeConfig()
except ValueError as e:
    # Config not ready yet - will raise error when accessed
    config = None
    print(f"Warning: {e}")


if __name__ == "__main__":
    """Test configuration loading."""
    if config and config.is_configured:
        print("✓ Configuration loaded successfully!")
        print(f"  API URL: {config.api_url}")
        print(f"  Client Secret: {'*' * len(config.client_secret[:8])}... (hidden)")
        print(f"  Refresh Token: {'*' * len(config.refresh_token[:8])}... (hidden)")
    else:
        print("✗ Configuration incomplete. Please add credentials to .env file.")
