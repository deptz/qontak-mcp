"""
Environment-based token store for local development.

WARNING: This store is intended for LOCAL DEVELOPMENT only.
For staging environments, use RedisTokenStore.
For production deployments, use VaultTokenStore which provides:
- Encryption at rest
- Access audit logging
- Fine-grained access control
- Secret rotation capabilities

Environment-based storage keeps tokens in memory and reads refresh tokens
from environment variables, which is not suitable for multi-tenant or
production deployments.
"""

import os
from typing import Optional
from pathlib import Path
from .base import TokenStore, TokenData


class EnvTokenStore(TokenStore):
    """
    Token store that reads refresh token from environment variable.
    
    ⚠️  LOCAL DEVELOPMENT USE ONLY ⚠️
    
    This is the simplest store for single-tenant local development.
    The refresh token is read from QONTAK_REFRESH_TOKEN env var.
    Access token and expiry are cached in memory.
    
    Limitations:
    - Single tenant only (no multi-user support)
    - Tokens stored in memory (lost on restart)
    - No encryption or audit logging
    - Not suitable for production or staging
    
    For staging/QA: Use RedisTokenStore
    For production: Use VaultTokenStore
    
    Note: Access token cache is lost on process restart, which is fine
    since we can always refresh using the refresh_token.
    """
    
    def __init__(self) -> None:
        """Initialize the env token store with in-memory cache."""
        # In-memory cache for access tokens
        # Key: user_id (or "_default" for single-tenant)
        self._cache: dict[str, TokenData] = {}
        
    def _find_env_file(self) -> Optional[Path]:
        """Find the .env file in the current working directory or parent directories."""
        current = Path.cwd()
        for _ in range(5):  # Check up to 5 levels up
            env_file = current / ".env"
            if env_file.exists():
                return env_file
            current = current.parent
        return None
    
    def _update_env_file(self, new_refresh_token: str) -> None:
        """Update the QONTAK_REFRESH_TOKEN in the .env file."""
        env_file = self._find_env_file()
        if not env_file:
            # Can't update file, just log and continue
            # The token will be lost on restart
            return
        
        try:
            # Read current content
            content = env_file.read_text()
            lines = content.splitlines()
            
            # Update or add QONTAK_REFRESH_TOKEN
            updated = False
            for i, line in enumerate(lines):
                if line.strip().startswith("QONTAK_REFRESH_TOKEN="):
                    lines[i] = f"QONTAK_REFRESH_TOKEN={new_refresh_token}"
                    updated = True
                    break
            
            if not updated:
                # Add at the end
                lines.append(f"QONTAK_REFRESH_TOKEN={new_refresh_token}")
            
            # Write back
            env_file.write_text("\n".join(lines) + "\n")
        except Exception:
            # Silently fail - we'll use the cached token until restart
            pass
    
    def _get_cache_key(self, user_id: Optional[str]) -> str:
        """Get the cache key for a user."""
        return user_id if user_id else "_default"
    
    def get(self, user_id: Optional[str] = None) -> Optional[TokenData]:
        """
        Get token data from cache or environment.
        
        Priority:
        1. Return cached TokenData if available (includes rotated refresh token)
        2. Fall back to reading QONTAK_REFRESH_TOKEN from environment
        
        Args:
            user_id: Ignored for env store (single-tenant only)
        
        Returns:
            TokenData with refresh_token from cache or env, and cached access_token
        """
        cache_key = self._get_cache_key(user_id)
        
        # Check if we have cached token data (preferred)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # No cache, read refresh token from environment
        refresh_token = os.getenv("QONTAK_REFRESH_TOKEN")
        if not refresh_token:
            return None
        
        # Return with just the refresh token from env
        return TokenData(refresh_token=refresh_token)
    
    def save(self, token_data: TokenData, user_id: Optional[str] = None) -> None:
        """
        Save token data to in-memory cache and update .env file.
        
        For env store, access_token and expires_at are cached in memory.
        If the refresh_token has changed, we update the .env file to persist it.
        
        Args:
            token_data: Token data to cache
            user_id: Ignored for env store (single-tenant only)
        """
        cache_key = self._get_cache_key(user_id)
        
        # Check if refresh token has changed
        old_refresh_token = os.getenv("QONTAK_REFRESH_TOKEN")
        if token_data.refresh_token != old_refresh_token:
            # Update .env file with new refresh token
            self._update_env_file(token_data.refresh_token)
            # Update the environment variable for current process
            os.environ["QONTAK_REFRESH_TOKEN"] = token_data.refresh_token
        
        # Cache the token data
        self._cache[cache_key] = token_data
