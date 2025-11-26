"""
Redis-based token store for development and staging environments.

WARNING: This store is intended for DEVELOPMENT and STAGING environments only.
For production deployments, use VaultTokenStore which provides:
- Encryption at rest
- Access audit logging
- Fine-grained access control
- Secret rotation capabilities

Redis stores tokens in plain text (or with basic serialization), which may not
meet security requirements for production environments handling sensitive credentials.
"""

import json
import os
from typing import Optional

from .base import TokenStore, TokenData


class RedisTokenStore(TokenStore):
    """
    Redis-based token store for multi-tenant deployments.
    
    ⚠️  DEVELOPMENT/STAGING USE ONLY ⚠️
    
    This store is suitable for:
    - Local development with multiple test tenants
    - Staging/QA environments
    - Non-production testing scenarios
    
    For production, use VaultTokenStore instead.
    
    Configuration via environment variables:
    - REDIS_URL: Redis connection URL (default: redis://localhost:6379/0)
    - REDIS_KEY_PREFIX: Key prefix for token storage (default: qontak:tokens:)
    - REDIS_TOKEN_TTL: TTL for cached access tokens in seconds (default: 21600 = 6 hours)
    """
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        key_prefix: Optional[str] = None,
        token_ttl: Optional[int] = None,
    ) -> None:
        """
        Initialize the Redis token store.
        
        Args:
            redis_url: Redis connection URL. Falls back to REDIS_URL env var.
            key_prefix: Prefix for Redis keys. Falls back to REDIS_KEY_PREFIX env var.
            token_ttl: TTL for tokens in seconds. Falls back to REDIS_TOKEN_TTL env var.
        """
        try:
            import redis
        except ImportError as e:
            raise ImportError(
                "Redis support is not installed. "
                "Install with: pip install 'qontak-mcp[redis]'"
            ) from e
        
        self._redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._key_prefix = key_prefix or os.getenv("REDIS_KEY_PREFIX", "qontak:tokens:")
        self._token_ttl = token_ttl or int(os.getenv("REDIS_TOKEN_TTL", "21600"))
        
        # Create Redis client
        self._redis = redis.from_url(self._redis_url, decode_responses=True)
    
    def _get_key(self, user_id: Optional[str]) -> str:
        """Get the Redis key for a user's tokens."""
        user_key = user_id if user_id else "_default"
        return f"{self._key_prefix}{user_key}"
    
    def get(self, user_id: Optional[str] = None) -> Optional[TokenData]:
        """
        Retrieve token data from Redis.
        
        Args:
            user_id: User/tenant identifier. Uses "_default" if not provided.
        
        Returns:
            TokenData if found, None otherwise
        """
        key = self._get_key(user_id)
        
        try:
            data = self._redis.get(key)
            if data is None:
                return None
            
            token_dict = json.loads(data)
            return TokenData(
                refresh_token=token_dict["refresh_token"],
                access_token=token_dict.get("access_token"),
                expires_at=token_dict.get("expires_at"),
            )
        except Exception:
            return None
    
    def save(self, token_data: TokenData, user_id: Optional[str] = None) -> None:
        """
        Save token data to Redis.
        
        Args:
            token_data: Token data to save
            user_id: User/tenant identifier. Uses "_default" if not provided.
        """
        key = self._get_key(user_id)
        
        token_dict = {
            "refresh_token": token_data.refresh_token,
            "access_token": token_data.access_token,
            "expires_at": token_data.expires_at,
        }
        
        # Store with TTL matching token expiry
        self._redis.setex(key, self._token_ttl, json.dumps(token_dict))
    
    def delete(self, user_id: Optional[str] = None) -> bool:
        """
        Delete token data from Redis.
        
        Args:
            user_id: User/tenant identifier. Uses "_default" if not provided.
        
        Returns:
            True if a key was deleted, False otherwise
        """
        key = self._get_key(user_id)
        return bool(self._redis.delete(key))
    
    def exists(self, user_id: Optional[str] = None) -> bool:
        """
        Check if token data exists for a user.
        
        Args:
            user_id: User/tenant identifier. Uses "_default" if not provided.
        
        Returns:
            True if token data exists, False otherwise
        """
        key = self._get_key(user_id)
        return bool(self._redis.exists(key))
