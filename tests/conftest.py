import os
import pytest
import respx
import httpx
import time
from unittest.mock import MagicMock, patch
from typing import AsyncGenerator, Generator

from qontak_mcp.client import QontakClient
from qontak_mcp.auth import QontakAuth
from qontak_mcp.stores import TokenData
from qontak_mcp.stores.env import EnvTokenStore
from qontak_mcp.stores.redis import RedisTokenStore

@pytest.fixture
def mock_env() -> Generator[None, None, None]:
    """Set up dummy environment variables for testing."""
    with patch.dict(os.environ, {
        "QONTAK_CLIENT_ID": "test-client-id",
        "QONTAK_CLIENT_SECRET": "test-client-secret",
        "QONTAK_USERNAME": "test-user",
        "QONTAK_PASSWORD": "test-password",
        "QONTAK_TOKEN_STORE": "env",
        "QONTAK_REFRESH_TOKEN": "valid-refresh-token", # Added this
    }):
        yield

@pytest.fixture
def mock_redis() -> Generator[MagicMock, None, None]:
    """Mock Redis client using fakeredis."""
    # Ensure redis is imported so we can patch it
    import redis
    with patch("redis.from_url") as mock_from_url:
        import fakeredis
        fake_redis = fakeredis.FakeRedis(decode_responses=True)
        mock_from_url.return_value = fake_redis
        # Clear any QONTAK_REFRESH_TOKEN to prevent auto-initialization
        with patch.dict(os.environ, {"QONTAK_REFRESH_TOKEN": ""}, clear=False):
            yield fake_redis

@pytest.fixture
async def auth(mock_env) -> QontakAuth:
    """Create a QontakAuth instance with EnvTokenStore."""
    store = EnvTokenStore()
    # Pre-populate store with a valid token to avoid auto-login in some tests
    store.save(TokenData(
        access_token="valid-access-token",
        refresh_token="valid-refresh-token",
        expires_at=time.time() + 3600
    ))
    return QontakAuth(store=store)

@pytest.fixture
async def client(auth) -> QontakClient:
    """Create a QontakClient instance."""
    return QontakClient(auth=auth)
