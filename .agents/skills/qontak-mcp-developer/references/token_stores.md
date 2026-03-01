# Token Store Backend Guide

## Overview

Token stores handle OAuth token persistence. The protocol enables multi-tenant deployments where each user/tenant has isolated tokens.

## TokenStore Protocol

```python
class TokenStore(Protocol):
    def get(self, user_id: Optional[str] = None) -> Optional[TokenData]: ...
    def save(self, token_data: TokenData, user_id: Optional[str] = None) -> None: ...
```

### TokenData Structure

```python
@dataclass
class TokenData:
    refresh_token: str
    access_token: Optional[str] = None
    expires_at: Optional[float] = None  # Unix timestamp
    
    def is_access_token_valid(self, buffer_seconds: int = 300) -> bool:
        if not self.access_token or not self.expires_at:
            return False
        return (self.expires_at - buffer_seconds) > datetime.now().timestamp()
```

## Creating a New Token Store

### Step 1: Create Store Module

Create `src/qontak_mcp/stores/{store_name}.py`:

```python
"""
{Backend} token store implementation.
"""

from typing import Optional
from .base import TokenData, TokenStore


class NewTokenStore:
    """
    Token store using {Backend}.
    
    Features:
    - Multi-tenant isolation via user_id
    - {Specific features}
    """
    
    def __init__(self, connection_params: dict) -> None:
        """
        Initialize store.
        
        Args:
            connection_params: Configuration for backend connection
        """
        self._connection = self._connect(connection_params)
        self._key_prefix = "qontak:tokens:"
    
    def _get_key(self, user_id: Optional[str]) -> str:
        """Generate storage key for user."""
        user_part = user_id or "default"
        return f"{self._key_prefix}{user_part}"
    
    def get(self, user_id: Optional[str] = None) -> Optional[TokenData]:
        """Retrieve token data for user."""
        key = self._get_key(user_id)
        data = self._connection.get(key)
        
        if not data:
            return None
        
        return TokenData(
            refresh_token=data["refresh_token"],
            access_token=data.get("access_token"),
            expires_at=data.get("expires_at")
        )
    
    def save(self, token_data: TokenData, user_id: Optional[str] = None) -> None:
        """Save token data for user."""
        key = self._get_key(user_id)
        data = {
            "refresh_token": token_data.refresh_token,
            "access_token": token_data.access_token,
            "expires_at": token_data.expires_at,
        }
        self._connection.set(key, data)
```

### Step 2: Register in Store Factory

Update `src/qontak_mcp/stores/__init__.py`:

```python
def get_token_store() -> TokenStore:
    """Factory function to create appropriate token store."""
    store_type = os.getenv("TOKEN_STORE", "env").lower()
    
    if store_type == "newstore":
        from .new_store import NewTokenStore
        return NewTokenStore(
            host=os.getenv("NEWSTORE_HOST"),
            port=int(os.getenv("NEWSTORE_PORT", "8080")),
        )
    
    # ... existing stores
```

### Step 3: Add Tests

Create `tests/stores/test_new_store.py`:

```python
import pytest
from qontak_mcp.stores.new_store import NewTokenStore
from qontak_mcp.stores.base import TokenData


class TestNewTokenStore:
    def test_get_existing_token(self):
        store = NewTokenStore(connection_params={"test": True})
        # Setup test data
        
        token_data = store.get(user_id="user-123")
        
        assert token_data is not None
        assert token_data.refresh_token == "test-refresh-token"
    
    def test_get_missing_token(self):
        store = NewTokenStore(connection_params={"test": True})
        
        token_data = store.get(user_id="nonexistent")
        
        assert token_data is None
    
    def test_save_token(self):
        store = NewTokenStore(connection_params={"test": True})
        token_data = TokenData(
            refresh_token="new-refresh",
            access_token="new-access",
            expires_at=1234567890.0
        )
        
        store.save(token_data, user_id="user-456")
        
        # Verify stored
        retrieved = store.get(user_id="user-456")
        assert retrieved.refresh_token == "new-refresh"
    
    def test_multi_tenant_isolation(self):
        store = NewTokenStore(connection_params={"test": True})
        
        store.save(
            TokenData(refresh_token="user-a-token"),
            user_id="user-a"
        )
        store.save(
            TokenData(refresh_token="user-b-token"),
            user_id="user-b"
        )
        
        assert store.get("user-a").refresh_token == "user-a-token"
        assert store.get("user-b").refresh_token == "user-b-token"
```

### Step 4: Document Configuration

Add to `.env.example`:

```bash
# NewStore Configuration
NEWSTORE_HOST=localhost
NEWSTORE_PORT=8080
NEWSTORE_API_KEY=your_api_key
```

Update `README.md` token store table:

```markdown
| Environment | TOKEN_STORE | Package | Security Level |
|-------------|-------------|---------|----------------|
| ... | ... | ... | ... |
| **Custom** | `newstore` | `[newstore]` | ⚡ Your description |
```

## Reference Implementations

### EnvTokenStore (Simplest)

```python
class EnvTokenStore:
    """Reads refresh token from environment."""
    
    def get(self, user_id: Optional[str] = None) -> Optional[TokenData]:
        refresh_token = os.getenv("QONTAK_REFRESH_TOKEN")
        if not refresh_token:
            return None
        return TokenData(refresh_token=refresh_token)
    
    def save(self, token_data: TokenData, user_id: Optional[str] = None) -> None:
        pass  # No-op - env vars are read-only
```

### RedisTokenStore (Caching)

```python
class RedisTokenStore:
    """Redis-backed token store with TTL."""
    
    def __init__(self, url: str = "redis://localhost:6379/0"):
        import redis
        self._client = redis.from_url(url)
        self._ttl = int(os.getenv("REDIS_TOKEN_TTL", "21600"))
        self._prefix = os.getenv("REDIS_KEY_PREFIX", "qontak:tokens:")
    
    def get(self, user_id: Optional[str] = None) -> Optional[TokenData]:
        key = f"{self._prefix}{user_id or 'default'}"
        data = self._client.get(key)
        if not data:
            return None
        parsed = json.loads(data)
        return TokenData(**parsed)
    
    def save(self, token_data: TokenData, user_id: Optional[str] = None) -> None:
        key = f"{self._prefix}{user_id or 'default'}"
        data = {
            "refresh_token": token_data.refresh_token,
            "access_token": token_data.access_token,
            "expires_at": token_data.expires_at,
        }
        self._client.setex(key, self._ttl, json.dumps(data))
```

### VaultTokenStore (Enterprise)

```python
class VaultTokenStore:
    """HashiCorp Vault token store with encryption."""
    
    def __init__(self, addr: str, token: str, mount_path: str = "secret"):
        import hvac
        self._client = hvac.Client(url=addr, token=token)
        self._mount = mount_path
        self._path = os.getenv("VAULT_SECRET_PATH", "qontak/tokens")
    
    def _get_path(self, user_id: Optional[str]) -> str:
        user_part = user_id or "default"
        return f"{self._path}/{user_part}"
    
    def get(self, user_id: Optional[str] = None) -> Optional[TokenData]:
        try:
            response = self._client.secrets.kv.v2.read_secret_version(
                path=self._get_path(user_id),
                mount_point=self._mount
            )
            data = response["data"]["data"]
            return TokenData(**data)
        except hvac.exceptions.InvalidPath:
            return None
    
    def save(self, token_data: TokenData, user_id: Optional[str] = None) -> None:
        data = {
            "refresh_token": token_data.refresh_token,
            "access_token": token_data.access_token,
            "expires_at": token_data.expires_at,
        }
        self._client.secrets.kv.v2.create_or_update_secret(
            path=self._get_path(user_id),
            secret=data,
            mount_point=self._mount
        )
```

## Design Considerations

### Multi-Tenancy

Always use `user_id` as a namespace:

```python
def _get_key(self, user_id: Optional[str]) -> str:
    # Ensure isolation between tenants
    return f"{self._prefix}{user_id or 'default'}"
```

### Token Rotation

OAuth may return new refresh_token on refresh. Always save the new tokens:

```python
new_refresh_token = result.get("refresh_token", old_refresh_token)
```

### Error Handling

Stores should handle connection failures gracefully:

```python
def get(self, user_id: Optional[str] = None) -> Optional[TokenData]:
    try:
        # ... fetch logic
    except ConnectionError:
        # Log error, but don't crash
        return None
```

### TTL and Caching

For stores that support TTL (Redis, etc.), set it slightly longer than token expiry:

```python
# Token expires in 6 hours, cache for 7 hours
ttl = TOKEN_EXPIRY_SECONDS + 3600
```

## Testing Strategy

| Test | Purpose |
|------|---------|
| `test_get_existing` | Verify retrieval works |
| `test_get_missing` | Verify graceful handling of missing tokens |
| `test_save_and_get` | Verify round-trip persistence |
| `test_multi_tenant` | Verify user isolation |
| `test_connection_failure` | Verify graceful degradation |
| `test_ttl_expiry` | Verify token expiration handling |

## Configuration Pattern

Use environment variables for configuration:

```python
def __init__(self) -> None:
    self._host = os.getenv("STORE_HOST", "localhost")
    self._port = int(os.getenv("STORE_PORT", "8080"))
    self._timeout = int(os.getenv("STORE_TIMEOUT", "30"))
```

Update `pyproject.toml` optional dependencies:

```toml
[project.optional-dependencies]
redis = ["redis==5.2.1"]
vault = ["hvac==2.3.0"]
newstore = ["newstore-client==1.0.0"]
all = ["redis==5.2.1", "hvac==2.3.0", "newstore-client==1.0.0"]
```
