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
