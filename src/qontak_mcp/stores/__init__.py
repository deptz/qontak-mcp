"""
Token store package - pluggable backends for credential storage.

Available stores:
- EnvTokenStore: Local development only (single-tenant, in-memory)
- RedisTokenStore: Development/Staging (multi-tenant, plain storage)
- VaultTokenStore: Production (multi-tenant, encrypted, audited)

For production deployments, always use VaultTokenStore.
"""

from .base import TokenStore, TokenData
from .env import EnvTokenStore

__all__ = [
    "TokenStore",
    "TokenData",
    "EnvTokenStore",
    "RedisTokenStore",
    "VaultTokenStore",
    "get_token_store",
]


def get_token_store() -> TokenStore:
    """
    Factory function to create the appropriate token store based on environment.
    
    Reads TOKEN_STORE env var to determine which backend to use:
    - "env" (default): Local development only, reads from QONTAK_REFRESH_TOKEN
    - "redis": Development/Staging, multi-tenant storage in Redis
    - "vault": PRODUCTION RECOMMENDED, secure multi-tenant storage in HashiCorp Vault
    
    Environment Recommendations:
    ┌─────────────────┬────────────────┬─────────────────────────────────────┐
    │ Environment     │ TOKEN_STORE    │ Notes                               │
    ├─────────────────┼────────────────┼─────────────────────────────────────┤
    │ Local Dev       │ env (default)  │ Single tenant, env var based        │
    │ Development     │ redis          │ Multi-tenant testing                │
    │ Staging/QA      │ redis          │ Multi-tenant, pre-production        │
    │ Production      │ vault          │ Encrypted, audited, secure          │
    └─────────────────┴────────────────┴─────────────────────────────────────┘
    
    Returns:
        TokenStore: The configured token store instance
    
    Raises:
        ImportError: If the required package for the store is not installed
        ValueError: If TOKEN_STORE is set to an unknown value
    """
    import os
    
    store_type = os.getenv("TOKEN_STORE", "env").lower()
    
    if store_type == "env":
        return EnvTokenStore()
    
    elif store_type == "redis":
        try:
            from .redis import RedisTokenStore
            return RedisTokenStore()
        except ImportError as e:
            raise ImportError(
                "Redis support is not installed. "
                "Install with: pip install 'qontak-mcp[redis]'"
            ) from e

    elif store_type == "vault":
        try:
            from .vault import VaultTokenStore
            return VaultTokenStore()
        except ImportError as e:
            raise ImportError(
                "Vault support is not installed. "
                "Install with: pip install 'qontak-mcp[vault]'"
            ) from e
    
    else:
        raise ValueError(
            f"Unknown TOKEN_STORE type: {store_type}. "
            "Valid options are: env, redis, vault"
        )


# Lazy imports for type checking
def __getattr__(name: str):
    if name == "RedisTokenStore":
        from .redis import RedisTokenStore
        return RedisTokenStore
    elif name == "VaultTokenStore":
        from .vault import VaultTokenStore
        return VaultTokenStore
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
