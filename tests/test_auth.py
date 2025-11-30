import os
import pytest
import time
import httpx
from unittest.mock import MagicMock
from qontak_mcp.auth import QontakAuth, REFRESH_BUFFER_SECONDS
from qontak_mcp.stores import TokenData
from qontak_mcp.stores.env import EnvTokenStore

@pytest.mark.asyncio
async def test_get_access_token_valid(auth):
    """Test getting a valid cached access token."""
    # The auth fixture already has a valid token
    token = await auth.get_access_token()
    assert token == "valid-access-token"

@pytest.mark.asyncio
async def test_get_access_token_expired_refresh_success(mock_env):
    """Test refreshing an expired access token."""
    from unittest.mock import AsyncMock, patch, MagicMock
    
    # Setup store with expired token
    store = EnvTokenStore()
    expired_time = time.time() - 100  # Expired 100s ago
    store.save(TokenData(
        access_token="old-access",
        refresh_token="valid-refresh",
        expires_at=expired_time
    ))
    
    auth = QontakAuth(store=store)
    
    # Mock HTTP client response
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "access_token": "new-access-token",
        "expires_in": 3600,
        "refresh_token": "valid-refresh"
    }
    mock_response.raise_for_status = MagicMock()
    
    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    
    with patch.object(auth, '_get_http_client', return_value=mock_client):
        token = await auth.get_access_token()
    
    assert token == "new-access-token"
    # Verify store was updated
    data = store.get()
    assert data.access_token == "new-access-token"
    assert data.expires_at > time.time() + 3000

@pytest.mark.asyncio
async def test_get_access_token_no_token_configured():
    """Test error when no token is configured."""
    # Clear the environment variable
    import os
    from unittest.mock import patch
    
    with patch.dict(os.environ, {"QONTAK_REFRESH_TOKEN": ""}, clear=False):
        store = EnvTokenStore()
        # Ensure store is empty
        store._token = None 
        
        auth = QontakAuth(store=store)
        
        with pytest.raises(ValueError, match="No refresh token configured"):
            await auth.get_access_token()

@pytest.mark.asyncio
async def test_get_access_token_refresh_failure(mock_env):
    """Test failure when refreshing token."""
    from unittest.mock import AsyncMock, patch, MagicMock
    
    store = EnvTokenStore()
    expired_time = time.time() - 100
    store.save(TokenData(
        access_token="old-access",
        refresh_token="valid-refresh",
        expires_at=expired_time
    ))
    
    auth = QontakAuth(store=store)
    
    # Mock HTTP client to raise an error
    mock_client = AsyncMock()
    mock_client.post.side_effect = httpx.HTTPStatusError(
        "401 Unauthorized", 
        request=httpx.Request("POST", "https://app.qontak.com/oauth/token"),
        response=httpx.Response(401, json={"error": "invalid_grant"})
    )
    
    with patch.object(auth, '_get_http_client', return_value=mock_client):
        with pytest.raises(httpx.HTTPStatusError):
            await auth.get_access_token()

@pytest.mark.asyncio
async def test_get_auth_headers(auth):
    """Test getting auth headers."""
    headers = await auth.get_auth_headers()
    assert headers == {"Authorization": "Bearer valid-access-token"}

@pytest.mark.asyncio
async def test_get_access_token_with_new_refresh_token(mock_env):
    """Test token refresh when API returns a new refresh_token (token rotation)."""
    from unittest.mock import AsyncMock, patch, MagicMock
    
    store = EnvTokenStore()
    expired_time = time.time() - 100
    store.save(TokenData(
        access_token="old-access",
        refresh_token="old-refresh",
        expires_at=expired_time
    ))
    
    auth = QontakAuth(store=store)
    
    # Mock HTTP client response with new refresh token
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "access_token": "new-access-token",
        "expires_in": 3600,
        "refresh_token": "new-refresh-token"  # API rotates refresh token
    }
    mock_response.raise_for_status = MagicMock()
    
    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    
    with patch.object(auth, '_get_http_client', return_value=mock_client):
        token = await auth.get_access_token()
    
    assert token == "new-access-token"
    # Verify store was updated with NEW refresh token
    data = store.get()
    assert data.access_token == "new-access-token"
    assert data.refresh_token == "new-refresh-token"

@pytest.mark.asyncio
async def test_get_access_token_without_expires_in(mock_env):
    """Test token refresh when API doesn't return expires_in."""
    from unittest.mock import AsyncMock, patch, MagicMock
    from qontak_mcp.auth import TOKEN_EXPIRY_SECONDS
    
    store = EnvTokenStore()
    expired_time = time.time() - 100
    store.save(TokenData(
        access_token="old-access",
        refresh_token="valid-refresh",
        expires_at=expired_time
    ))
    
    auth = QontakAuth(store=store)
    
    # Mock HTTP client response without expires_in
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "access_token": "new-access-token",
        # No expires_in field
    }
    mock_response.raise_for_status = MagicMock()
    
    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    
    with patch.object(auth, '_get_http_client', return_value=mock_client):
        token = await auth.get_access_token()
    
    assert token == "new-access-token"
    # Verify store was updated with default expiry
    data = store.get()
    assert data.expires_at > time.time() + TOKEN_EXPIRY_SECONDS - 10

@pytest.mark.asyncio
async def test_get_access_token_with_user_id(mock_env):
    """Test getting access token for specific user (multi-tenant)."""
    from unittest.mock import AsyncMock, patch
    
    store = EnvTokenStore()
    store.save(TokenData(
        access_token="user-token",
        refresh_token="user-refresh",
        expires_at=time.time() + 3600
    ), user_id="user123")
    
    auth = QontakAuth(store=store)
    
    token = await auth.get_access_token(user_id="user123")
    assert token == "user-token"

@pytest.mark.asyncio
async def test_get_auth_headers_with_user_id(mock_env):
    """Test getting auth headers for specific user."""
    store = EnvTokenStore()
    store.save(TokenData(
        access_token="user-token",
        refresh_token="user-refresh",
        expires_at=time.time() + 3600
    ), user_id="user123")
    
    auth = QontakAuth(store=store)
    
    headers = await auth.get_auth_headers(user_id="user123")
    assert headers == {"Authorization": "Bearer user-token"}

@pytest.mark.asyncio
async def test_http_client_creation():
    """Test HTTP client is created on first call."""
    from qontak_mcp.auth import QontakAuth
    from qontak_mcp.stores.env import EnvTokenStore
    from unittest.mock import patch
    
    with patch.dict(os.environ, {"QONTAK_REFRESH_TOKEN": "test-token"}):
        store = EnvTokenStore()
        store.save(TokenData(
            access_token="test",
            refresh_token="test",
            expires_at=time.time() + 3600
        ))
        auth = QontakAuth(store=store)
        
        assert auth._http_client is None
        
        client = await auth._get_http_client()
        assert client is not None
        assert not client.is_closed
        
        # Second call should return same client
        client2 = await auth._get_http_client()
        assert client2 is client
        
        await auth.close()

@pytest.mark.asyncio
async def test_http_client_recreated_after_close():
    """Test HTTP client is recreated if closed externally."""
    from qontak_mcp.auth import QontakAuth
    from qontak_mcp.stores.env import EnvTokenStore
    from unittest.mock import patch
    
    with patch.dict(os.environ, {"QONTAK_REFRESH_TOKEN": "test-token"}):
        store = EnvTokenStore()
        store.save(TokenData(
            access_token="test",
            refresh_token="test",
            expires_at=time.time() + 3600
        ))
        auth = QontakAuth(store=store)
        
        client1 = await auth._get_http_client()
        await client1.aclose()
        
        # Should create new client
        client2 = await auth._get_http_client()
        assert client2 is not client1
        assert not client2.is_closed
        
        await auth.close()

@pytest.mark.asyncio
async def test_close_when_client_none():
    """Test close() works when _http_client is None."""
    from qontak_mcp.auth import QontakAuth
    from qontak_mcp.stores.env import EnvTokenStore
    from unittest.mock import patch
    
    with patch.dict(os.environ, {"QONTAK_REFRESH_TOKEN": "test-token"}):
        store = EnvTokenStore()
        auth = QontakAuth(store=store)
        
        # Should not raise error
        await auth.close()
        assert auth._http_client is None

@pytest.mark.asyncio
async def test_close_when_already_closed():
    """Test close() works when client is already closed."""
    from qontak_mcp.auth import QontakAuth
    from qontak_mcp.stores.env import EnvTokenStore
    from unittest.mock import patch
    
    with patch.dict(os.environ, {"QONTAK_REFRESH_TOKEN": "test-token"}):
        store = EnvTokenStore()
        store.save(TokenData(
            access_token="test",
            refresh_token="test",
            expires_at=time.time() + 3600
        ))
        auth = QontakAuth(store=store)
        
        client = await auth._get_http_client()
        await client.aclose()
        
        # Should not raise error
        await auth.close()
        # The client reference remains but is closed (close() checks is_closed)
        assert auth._http_client is client
        assert auth._http_client.is_closed
