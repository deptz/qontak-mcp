import pytest
import time
from qontak_mcp.stores import TokenData
from qontak_mcp.stores.env import EnvTokenStore

@pytest.mark.asyncio
async def test_env_store_save_and_get(mock_env):
    """Test saving and retrieving token from EnvTokenStore."""
    store = EnvTokenStore()
    
    # Initial state should be empty (or whatever is in env)
    # We'll overwrite it
    
    token_data = TokenData(
        access_token="access-123",
        refresh_token="refresh-123",
        expires_at=time.time() + 3600
    )
    
    store.save(token_data)
    
    retrieved = store.get()
    assert retrieved.access_token == "access-123"
    # Env store caches the refresh token in memory after save
    assert retrieved.refresh_token == "refresh-123"

@pytest.mark.asyncio
async def test_env_store_multi_tenant(mock_env):
    """Test multi-tenant support in EnvTokenStore."""
    store = EnvTokenStore()
    
    token1 = TokenData(access_token="t1", refresh_token="r1", expires_at=0)
    token2 = TokenData(access_token="t2", refresh_token="r2", expires_at=0)
    
    store.save(token1, user_id="user1")
    store.save(token2, user_id="user2")
    
    r1 = store.get("user1")
    r2 = store.get("user2")
    
    assert r1.access_token == "t1"
    assert r2.access_token == "t2"
