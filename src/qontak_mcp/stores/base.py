"""
Token store base protocol and data models
"""

from typing import Protocol, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TokenData:
    """
    Token data structure for Qontak OAuth credentials.
    
    Attributes:
        refresh_token: The OAuth refresh token (never expires)
        access_token: The current access token (expires in 6 hours)
        expires_at: When the access token expires (Unix timestamp)
    """
    refresh_token: str
    access_token: Optional[str] = None
    expires_at: Optional[float] = None
    
    def is_access_token_valid(self, buffer_seconds: int = 300) -> bool:
        """
        Check if the access token is still valid.
        
        Args:
            buffer_seconds: Refresh token this many seconds before actual expiry.
                           Default is 300 (5 minutes).
        
        Returns:
            True if access_token exists and won't expire within buffer_seconds
        """
        if not self.access_token or not self.expires_at:
            return False
        
        now = datetime.now().timestamp()
        return (self.expires_at - buffer_seconds) > now


class TokenStore(Protocol):
    """
    Protocol for token storage backends.
    
    Implementations must provide get and save methods for TokenData.
    This protocol enables multi-tenant support by using user_id as a key.
    
    For single-tenant deployments, user_id can be None or a fixed value.
    For multi-tenant deployments, user_id identifies the tenant.
    """
    
    def get(self, user_id: Optional[str] = None) -> Optional[TokenData]:
        """
        Retrieve token data for a user.
        
        Args:
            user_id: Optional user/tenant identifier. 
                    For single-tenant, this can be None.
        
        Returns:
            TokenData if found, None otherwise
        """
        ...
    
    def save(self, token_data: TokenData, user_id: Optional[str] = None) -> None:
        """
        Save token data for a user.
        
        Args:
            token_data: The token data to save
            user_id: Optional user/tenant identifier.
                    For single-tenant, this can be None.
        """
        ...
