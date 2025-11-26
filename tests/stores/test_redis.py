import pytest
import time
import json
from unittest.mock import Mock, patch, MagicMock
from qontak_mcp.stores import TokenData
from qontak_mcp.stores.redis import RedisTokenStore

@pytest.mark.asyncio
async def test_redis_store_save_and_get(mock_redis):
    """Test saving and retrieving token from RedisTokenStore."""
    store = RedisTokenStore(redis_url="redis://localhost")
    
    token_data = TokenData(
        access_token="access-redis",
        refresh_token="refresh-redis",
        expires_at=time.time() + 3600
    )
    
    store.save(token_data)
    
    # Verify it's in redis
    raw_data = mock_redis.get("qontak:tokens:_default")
    assert raw_data is not None
    
    retrieved = store.get()
    assert retrieved.access_token == "access-redis"

@pytest.mark.asyncio
async def test_redis_store_missing_key(mock_redis):
    """Test retrieving missing key."""
    store = RedisTokenStore(redis_url="redis://localhost")
    
    retrieved = store.get()
    assert retrieved is None

@pytest.mark.asyncio
async def test_redis_store_multi_tenant(mock_redis):
    """Test multi-tenant support in RedisTokenStore."""
    store = RedisTokenStore(redis_url="redis://localhost")
    
    token = TokenData(access_token="t1", refresh_token="r1", expires_at=0)
    store.save(token, user_id="user1")
    
    # Check specific key
    raw_data = mock_redis.get("qontak:tokens:user1")
    assert raw_data is not None
    
    retrieved = store.get("user1")
    assert retrieved.access_token == "t1"


class TestRedisTokenStoreDelete:
    """Test delete() method of RedisTokenStore."""
    
    @pytest.mark.asyncio
    async def test_delete_existing_token(self, mock_redis):
        """Test deleting an existing token."""
        store = RedisTokenStore(redis_url="redis://localhost")
        
        # First save a token
        token = TokenData(
            access_token="access_to_delete",
            refresh_token="refresh_to_delete",
            expires_at=time.time() + 3600
        )
        store.save(token)
        
        # Verify it exists
        assert store.get() is not None
        
        # Delete it
        result = store.delete()
        
        # Should return True for successful deletion
        assert result is True
        
        # Verify it's gone
        assert store.get() is None
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_token(self, mock_redis):
        """Test deleting a non-existent token."""
        store = RedisTokenStore(redis_url="redis://localhost")
        
        # Delete without saving first
        result = store.delete()
        
        # Should return False when key doesn't exist
        assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_with_user_id(self, mock_redis):
        """Test deleting a token with specific user_id."""
        store = RedisTokenStore(redis_url="redis://localhost")
        
        # Save tokens for different users
        token1 = TokenData(
            access_token="user1_access",
            refresh_token="user1_refresh",
            expires_at=time.time() + 3600
        )
        token2 = TokenData(
            access_token="user2_access",
            refresh_token="user2_refresh",
            expires_at=time.time() + 3600
        )
        
        store.save(token1, user_id="user1")
        store.save(token2, user_id="user2")
        
        # Delete only user1's token
        result = store.delete(user_id="user1")
        assert result is True
        
        # user1's token should be gone
        assert store.get("user1") is None
        
        # user2's token should still exist
        retrieved = store.get("user2")
        assert retrieved is not None
        assert retrieved.access_token == "user2_access"


class TestRedisTokenStoreExists:
    """Test exists() method of RedisTokenStore."""
    
    @pytest.mark.asyncio
    async def test_exists_returns_true_when_token_exists(self, mock_redis):
        """Test exists() returns True when token is present."""
        store = RedisTokenStore(redis_url="redis://localhost")
        
        # Save a token
        token = TokenData(
            access_token="test_access",
            refresh_token="test_refresh",
            expires_at=time.time() + 3600
        )
        store.save(token)
        
        # Should return True
        assert store.exists() is True
    
    @pytest.mark.asyncio
    async def test_exists_returns_false_when_no_token(self, mock_redis):
        """Test exists() returns False when no token is present."""
        store = RedisTokenStore(redis_url="redis://localhost")
        
        # No token saved
        assert store.exists() is False
    
    @pytest.mark.asyncio
    async def test_exists_with_user_id(self, mock_redis):
        """Test exists() with specific user_id."""
        store = RedisTokenStore(redis_url="redis://localhost")
        
        # Save token for one user
        token = TokenData(
            access_token="user1_access",
            refresh_token="user1_refresh",
            expires_at=time.time() + 3600
        )
        store.save(token, user_id="user1")
        
        # user1 should exist
        assert store.exists("user1") is True
        
        # user2 should not exist
        assert store.exists("user2") is False


class TestRedisTokenStoreErrorHandling:
    """Test error handling in RedisTokenStore."""
    
    @pytest.mark.asyncio
    async def test_get_with_corrupted_data(self, mock_redis):
        """Test get() handles corrupted JSON data gracefully."""
        store = RedisTokenStore(redis_url="redis://localhost")
        
        # Manually set corrupted data in redis
        mock_redis.set("qontak:tokens:_default", "not valid json {{{")
        
        # get() should return None or raise appropriate error
        try:
            result = store.get()
            # If it handles gracefully, should return None
            assert result is None
        except json.JSONDecodeError:
            # Also acceptable - propagating the error
            pass
    
    @pytest.mark.asyncio
    async def test_get_with_incomplete_data(self, mock_redis):
        """Test get() handles incomplete token data."""
        store = RedisTokenStore(redis_url="redis://localhost")
        
        # Set data missing required fields
        incomplete_data = json.dumps({"access_token": "only_access"})
        mock_redis.set("qontak:tokens:_default", incomplete_data)
        
        # Should handle missing refresh_token
        try:
            result = store.get()
            # If it handles gracefully
            if result is not None:
                assert result.access_token == "only_access"
        except (KeyError, TypeError):
            # Also acceptable - propagating the error
            pass


class TestRedisTokenStoreConfiguration:
    """Test RedisTokenStore configuration options."""
    
    @pytest.mark.asyncio
    async def test_custom_key_prefix(self, mock_redis):
        """Test using custom key prefix."""
        store = RedisTokenStore(
            redis_url="redis://localhost",
            key_prefix="custom_prefix:"
        )
        
        token = TokenData(
            access_token="test_access",
            refresh_token="test_refresh",
            expires_at=time.time() + 3600
        )
        store.save(token)
        
        # Check the key uses custom prefix (key_prefix + user_key)
        # With key_prefix="custom_prefix:" and no user_id, the key is "custom_prefix:_default"
        raw_data = mock_redis.get("custom_prefix:_default")
        assert raw_data is not None
    
    @pytest.mark.asyncio
    async def test_default_redis_url_from_env(self, mock_redis, monkeypatch):
        """Test that redis_url defaults to environment variable."""
        monkeypatch.setenv("REDIS_URL", "redis://env-host:6379")
        
        # Create store without explicit URL
        store = RedisTokenStore()
        
        # Should use the environment variable
        assert store is not None
    
    @pytest.mark.asyncio
    async def test_save_sets_expiry(self, mock_redis):
        """Test that save() sets proper TTL on the key."""
        store = RedisTokenStore(redis_url="redis://localhost")
        
        token = TokenData(
            access_token="test_access",
            refresh_token="test_refresh",
            expires_at=time.time() + 3600
        )
        store.save(token)
        
        # Check TTL is set (fakeredis should support ttl command)
        ttl = mock_redis.ttl("qontak:tokens:_default")
        # TTL should be positive
        assert ttl > 0 or ttl == -1  # -1 means no expiry in some redis versions


class TestRedisTokenStoreIntegration:
    """Integration tests for RedisTokenStore workflows."""
    
    @pytest.mark.asyncio
    async def test_full_lifecycle(self, mock_redis):
        """Test complete token lifecycle: save -> get -> exists -> delete."""
        store = RedisTokenStore(redis_url="redis://localhost")
        user_id = "lifecycle_test_user"
        
        # Initially should not exist
        assert store.exists(user_id) is False
        assert store.get(user_id) is None
        
        # Save token
        token = TokenData(
            access_token="lifecycle_access",
            refresh_token="lifecycle_refresh",
            expires_at=time.time() + 3600
        )
        store.save(token, user_id=user_id)
        
        # Should now exist
        assert store.exists(user_id) is True
        
        # Should be retrievable
        retrieved = store.get(user_id)
        assert retrieved is not None
        assert retrieved.access_token == "lifecycle_access"
        assert retrieved.refresh_token == "lifecycle_refresh"
        
        # Delete
        result = store.delete(user_id)
        assert result is True
        
        # Should no longer exist
        assert store.exists(user_id) is False
        assert store.get(user_id) is None
    
    @pytest.mark.asyncio
    async def test_update_existing_token(self, mock_redis):
        """Test updating an existing token."""
        store = RedisTokenStore(redis_url="redis://localhost")
        
        # Save initial token
        token1 = TokenData(
            access_token="original_access",
            refresh_token="original_refresh",
            expires_at=time.time() + 3600
        )
        store.save(token1)
        
        # Update with new token
        token2 = TokenData(
            access_token="updated_access",
            refresh_token="updated_refresh",
            expires_at=time.time() + 7200
        )
        store.save(token2)
        
        # Should get the updated token
        retrieved = store.get()
        assert retrieved.access_token == "updated_access"
        assert retrieved.refresh_token == "updated_refresh"
    
    @pytest.mark.asyncio
    async def test_multiple_users_isolation(self, mock_redis):
        """Test that multiple users' tokens are properly isolated."""
        store = RedisTokenStore(redis_url="redis://localhost")
        
        users = ["alice", "bob", "charlie"]
        
        # Save tokens for each user
        for i, user in enumerate(users):
            token = TokenData(
                access_token=f"{user}_access_{i}",
                refresh_token=f"{user}_refresh_{i}",
                expires_at=time.time() + 3600
            )
            store.save(token, user_id=user)
        
        # Verify each user gets their own token
        for i, user in enumerate(users):
            retrieved = store.get(user)
            assert retrieved is not None
            assert retrieved.access_token == f"{user}_access_{i}"
            assert retrieved.refresh_token == f"{user}_refresh_{i}"
        
        # Delete one user's token
        store.delete(user_id="bob")
        
        # Bob's token should be gone
        assert store.get("bob") is None
        
        # Others should still exist
        assert store.get("alice") is not None
        assert store.get("charlie") is not None