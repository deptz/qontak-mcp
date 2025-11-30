"""
Qontak OAuth authentication with lazy token refresh.
"""

import httpx
from typing import Optional
from datetime import datetime

from .stores import TokenStore, TokenData, get_token_store


# Qontak OAuth configuration
QONTAK_TOKEN_URL = "https://app.qontak.com/oauth/token"
# Access token expires in 21600 seconds (6 hours)
TOKEN_EXPIRY_SECONDS = 21600
# Refresh 5 minutes before actual expiry
REFRESH_BUFFER_SECONDS = 300


class QontakAuth:
    """
    Handles Qontak OAuth authentication with lazy token refresh.
    
    This class manages access tokens by:
    1. Checking if a valid access token exists in the store
    2. If not, refreshing the token using the refresh_token
    3. Caching the new access token with its expiry time
    
    The refresh is "lazy" - it only happens when get_access_token() is called
    and the current token is expired or about to expire.
    """
    
    def __init__(self, store: Optional[TokenStore] = None) -> None:
        """
        Initialize the auth handler.
        
        Args:
            store: Optional token store. If not provided, uses get_token_store()
                  to create the default store based on environment.
        """
        self._store = store or get_token_store()
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None
    
    async def _refresh_token(self, refresh_token: str) -> dict:
        """
        Call Qontak OAuth endpoint to refresh the access token.
        
        Args:
            refresh_token: The refresh token to use
        
        Returns:
            The JSON response from the token endpoint
        
        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        client = await self._get_http_client()
        
        response = await client.post(
            QONTAK_TOKEN_URL,
            json={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def get_access_token(self, user_id: Optional[str] = None) -> str:
        """
        Get a valid access token, refreshing if necessary.
        
        This is the main method to call when you need an access token.
        It handles all the logic of checking cache, refreshing, and storing.
        
        Args:
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            A valid access token string
        
        Raises:
            ValueError: If no refresh token is configured
            httpx.HTTPStatusError: If token refresh fails
        """
        # Get current token data from store
        token_data = self._store.get(user_id)
        
        if token_data is None:
            raise ValueError(
                "No refresh token configured. "
                "Please set QONTAK_REFRESH_TOKEN environment variable."
            )
        
        # Check if we have a valid access token
        if token_data.is_access_token_valid(REFRESH_BUFFER_SECONDS):
            return token_data.access_token  # type: ignore
        
        # Need to refresh
        result = await self._refresh_token(token_data.refresh_token)
        
        # Calculate expiry time
        expires_in = result.get("expires_in", TOKEN_EXPIRY_SECONDS)
        expires_at = datetime.now().timestamp() + expires_in
        
        # Update token data with new refresh token (if provided)
        # OAuth token rotation: the API may return a new refresh_token
        new_refresh_token = result.get("refresh_token", token_data.refresh_token)
        new_token_data = TokenData(
            refresh_token=new_refresh_token,
            access_token=result["access_token"],
            expires_at=expires_at
        )
        
        # Save to store
        self._store.save(new_token_data, user_id)
        
        return result["access_token"]
    
    async def get_auth_headers(self, user_id: Optional[str] = None) -> dict[str, str]:
        """
        Get authorization headers for API requests.
        
        Convenience method that returns headers ready to use with httpx.
        
        Args:
            user_id: Optional user/tenant identifier
        
        Returns:
            Dict with Authorization header
        """
        access_token = await self.get_access_token(user_id)
        return {"Authorization": f"Bearer {access_token}"}
