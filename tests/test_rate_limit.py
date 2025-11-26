"""
Comprehensive tests for rate limiting module.

Tests token bucket algorithm, per-user and global limits,
rate limit checking with wait functionality, and cleanup.
"""

import pytest
import asyncio
import time
from qontak_mcp.rate_limit import (
    RateLimitConfig,
    TokenBucket,
    RateLimiter,
    get_rate_limiter,
    configure_rate_limiter,
)


class TestTokenBucket:
    """Test the TokenBucket implementation."""
    
    @pytest.mark.asyncio
    async def test_token_bucket_initialization(self):
        """Test token bucket starts with full capacity."""
        bucket = TokenBucket(capacity=10.0, refill_rate=5.0)
        assert bucket.tokens == 10.0
        assert bucket.capacity == 10.0
        assert bucket.refill_rate == 5.0
    
    @pytest.mark.asyncio
    async def test_acquire_success(self):
        """Test successful token acquisition."""
        bucket = TokenBucket(capacity=10.0, refill_rate=5.0)
        assert await bucket.acquire(1.0) is True
        assert bucket.tokens == 9.0
    
    @pytest.mark.asyncio
    async def test_acquire_failure_insufficient_tokens(self):
        """Test acquire fails when not enough tokens."""
        bucket = TokenBucket(capacity=10.0, refill_rate=5.0)
        # Use up all tokens
        assert await bucket.acquire(10.0) is True
        # Next acquire should fail
        assert await bucket.acquire(1.0) is False
    
    @pytest.mark.asyncio
    async def test_acquire_multiple_tokens(self):
        """Test acquiring multiple tokens at once."""
        bucket = TokenBucket(capacity=10.0, refill_rate=5.0)
        assert await bucket.acquire(5.0) is True
        # Allow small floating point error due to time passing
        assert 4.9 < bucket.tokens < 5.1
        assert await bucket.acquire(5.0) is True
        assert bucket.tokens < 0.1  # Near zero, accounting for refill during test
    
    @pytest.mark.asyncio
    async def test_token_refill(self):
        """Test that tokens refill over time."""
        bucket = TokenBucket(capacity=10.0, refill_rate=10.0)  # 10 tokens per second
        
        # Use all tokens
        await bucket.acquire(10.0)
        assert bucket.tokens == 0.0
        
        # Wait for refill (100ms = 1 token)
        await asyncio.sleep(0.1)
        
        # Should have approximately 1 token (allowing for timing variance)
        assert await bucket.acquire(0.5) is True
    
    @pytest.mark.asyncio
    async def test_refill_does_not_exceed_capacity(self):
        """Test that refilled tokens don't exceed capacity."""
        bucket = TokenBucket(capacity=10.0, refill_rate=5.0)
        
        # Wait to refill
        await asyncio.sleep(0.5)
        
        # Try to acquire more than capacity - should fail
        assert await bucket.acquire(15.0) is False
        
        # But we should still have full capacity
        assert await bucket.acquire(10.0) is True
    
    @pytest.mark.asyncio
    async def test_wait_for_token_success(self):
        """Test waiting for tokens to become available."""
        bucket = TokenBucket(capacity=10.0, refill_rate=10.0)  # 10 tokens/sec
        
        # Use all tokens
        await bucket.acquire(10.0)
        
        # Wait for token - should succeed after ~100ms
        start = time.monotonic()
        result = await bucket.wait_for_token(1.0, timeout=1.0)
        elapsed = time.monotonic() - start
        
        assert result is True
        assert elapsed < 0.5  # Should get token relatively quickly
    
    @pytest.mark.asyncio
    async def test_wait_for_token_timeout(self):
        """Test wait_for_token times out when refill is too slow."""
        bucket = TokenBucket(capacity=10.0, refill_rate=1.0)  # 1 token/sec
        
        # Use all tokens
        await bucket.acquire(10.0)
        
        # Try to wait for 5 tokens with short timeout - should timeout
        start = time.monotonic()
        result = await bucket.wait_for_token(5.0, timeout=0.1)
        elapsed = time.monotonic() - start
        
        assert result is False
        assert elapsed >= 0.1  # Should have waited at least the timeout
        assert elapsed < 0.3  # But not much longer
    
    @pytest.mark.asyncio
    async def test_available_tokens_property(self):
        """Test available_tokens property without consuming tokens."""
        bucket = TokenBucket(capacity=10.0, refill_rate=5.0)
        
        # Check initial
        assert bucket.available_tokens == 10.0
        
        # Consume some
        await bucket.acquire(3.0)
        assert 6.9 < bucket.available_tokens < 7.1  # Allow for timing variance
        
        # Property shouldn't consume tokens
        assert 6.9 < bucket.available_tokens < 7.1
    
    @pytest.mark.asyncio
    async def test_concurrent_acquire_thread_safety(self):
        """Test that concurrent acquires are handled safely."""
        bucket = TokenBucket(capacity=10.0, refill_rate=5.0)
        
        # Try to acquire from multiple tasks concurrently
        results = await asyncio.gather(
            bucket.acquire(1.0),
            bucket.acquire(1.0),
            bucket.acquire(1.0),
            bucket.acquire(1.0),
            bucket.acquire(1.0),
        )
        
        # All should succeed
        assert all(results)
        # Allow for small refill during concurrent execution
        assert 4.9 < bucket.tokens < 5.2


class TestRateLimitConfig:
    """Test RateLimitConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = RateLimitConfig()
        assert config.requests_per_second == 10.0
        assert config.burst_size == 20
        assert config.per_user is True
        assert config.global_requests_per_second == 50.0
        assert config.global_burst_size == 100
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = RateLimitConfig(
            requests_per_second=5.0,
            burst_size=10,
            per_user=False,
            global_requests_per_second=25.0,
            global_burst_size=50
        )
        assert config.requests_per_second == 5.0
        assert config.burst_size == 10
        assert config.per_user is False
        assert config.global_requests_per_second == 25.0
        assert config.global_burst_size == 50


class TestRateLimiter:
    """Test the RateLimiter with per-user and global limits."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_initialization(self):
        """Test rate limiter initializes with config."""
        config = RateLimitConfig(requests_per_second=5.0, burst_size=10)
        limiter = RateLimiter(config)
        assert limiter.config == config
        assert limiter._global_bucket is not None
    
    @pytest.mark.asyncio
    async def test_acquire_no_user_id(self):
        """Test acquiring without user_id (only global limit checked)."""
        config = RateLimitConfig(global_requests_per_second=10.0, global_burst_size=10)
        limiter = RateLimiter(config)
        
        # Should succeed
        assert await limiter.acquire(user_id=None) is True
    
    @pytest.mark.asyncio
    async def test_acquire_with_user_id(self):
        """Test acquiring with user_id (both user and global limits checked)."""
        config = RateLimitConfig(
            requests_per_second=10.0,
            burst_size=10,
            per_user=True
        )
        limiter = RateLimiter(config)
        
        # Should succeed for first user
        assert await limiter.acquire(user_id="user1") is True
        
        # Should succeed for different user
        assert await limiter.acquire(user_id="user2") is True
    
    @pytest.mark.asyncio
    async def test_per_user_rate_limit(self):
        """Test that per-user rate limiting works."""
        config = RateLimitConfig(
            requests_per_second=10.0,
            burst_size=5,  # Small burst for testing
            per_user=True
        )
        limiter = RateLimiter(config)
        
        # Use up user1's tokens
        for _ in range(5):
            assert await limiter.acquire(user_id="user1") is True
        
        # Next request from user1 should fail
        assert await limiter.acquire(user_id="user1") is False
        
        # But user2 should still succeed
        assert await limiter.acquire(user_id="user2") is True
    
    @pytest.mark.asyncio
    async def test_global_rate_limit(self):
        """Test that global rate limiting works across all users."""
        config = RateLimitConfig(
            requests_per_second=100.0,
            burst_size=100,
            global_requests_per_second=100.0,
            global_burst_size=3,  # Very small for testing
            per_user=True
        )
        limiter = RateLimiter(config)
        
        # Use up global tokens with different users
        assert await limiter.acquire(user_id="user1") is True
        assert await limiter.acquire(user_id="user2") is True
        assert await limiter.acquire(user_id="user3") is True
        
        # Next request should fail regardless of user
        assert await limiter.acquire(user_id="user4") is False
        assert await limiter.acquire(user_id="user1") is False
    
    @pytest.mark.asyncio
    async def test_per_user_disabled(self):
        """Test that per-user limiting can be disabled."""
        config = RateLimitConfig(
            per_user=False,
            global_requests_per_second=10.0,
            global_burst_size=5
        )
        limiter = RateLimiter(config)
        
        # Use up global tokens
        for _ in range(5):
            assert await limiter.acquire(user_id="user1") is True
        
        # Should fail for any user (only global limit applies)
        assert await limiter.acquire(user_id="user1") is False
        assert await limiter.acquire(user_id="user2") is False
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_no_wait(self):
        """Test check_rate_limit without waiting."""
        config = RateLimitConfig(global_burst_size=5)
        limiter = RateLimiter(config)
        
        # Should succeed
        allowed, error = await limiter.check_rate_limit(user_id="user1", wait=False)
        assert allowed is True
        assert error is None
        
        # Use up tokens
        for _ in range(4):
            await limiter.acquire(user_id="user1")
        
        # Should fail
        allowed, error = await limiter.check_rate_limit(user_id="user1", wait=False)
        assert allowed is False
        assert error is not None
        assert "Rate limit exceeded" in error
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_with_wait_success(self):
        """Test check_rate_limit with wait succeeds when tokens refill."""
        config = RateLimitConfig(
            requests_per_second=20.0,
            burst_size=5,
            global_requests_per_second=100.0,
            global_burst_size=100
        )
        limiter = RateLimiter(config)
        
        # Use up user tokens
        for _ in range(5):
            await limiter.acquire(user_id="user1")
        
        # Should wait and succeed
        allowed, error = await limiter.check_rate_limit(
            user_id="user1",
            wait=True,
            timeout=1.0
        )
        assert allowed is True
        assert error is None
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_with_wait_timeout(self):
        """Test check_rate_limit with wait times out."""
        config = RateLimitConfig(
            requests_per_second=1.0,  # Very slow refill
            burst_size=2,
            global_requests_per_second=100.0,
            global_burst_size=100
        )
        limiter = RateLimiter(config)
        
        # Use up user tokens
        await limiter.acquire(user_id="user1")
        await limiter.acquire(user_id="user1")
        
        # Should timeout
        start = time.monotonic()
        allowed, error = await limiter.check_rate_limit(
            user_id="user1",
            wait=True,
            timeout=0.1
        )
        elapsed = time.monotonic() - start
        
        assert allowed is False
        assert error is not None
        assert "Rate limit exceeded" in error
        assert elapsed >= 0.1
    
    def test_get_user_stats_existing_user(self):
        """Test getting stats for a user with an existing bucket."""
        config = RateLimitConfig(requests_per_second=10.0, burst_size=20)
        limiter = RateLimiter(config)
        
        # Create bucket for user by acquiring
        import asyncio
        asyncio.run(limiter.acquire(user_id="user1"))
        
        stats = limiter.get_user_stats("user1")
        assert "available_tokens" in stats
        assert "capacity" in stats
        assert "refill_rate" in stats
        assert stats["capacity"] == 20
        assert stats["refill_rate"] == 10.0
        assert stats["available_tokens"] < 20  # Some used
    
    def test_get_user_stats_new_user(self):
        """Test getting stats for a user without a bucket yet."""
        config = RateLimitConfig(requests_per_second=10.0, burst_size=20)
        limiter = RateLimiter(config)
        
        stats = limiter.get_user_stats("new_user")
        assert stats["available_tokens"] == 20
        assert stats["capacity"] == 20
        assert stats["refill_rate"] == 10.0
    
    def test_get_global_stats(self):
        """Test getting global rate limit stats."""
        config = RateLimitConfig(
            global_requests_per_second=50.0,
            global_burst_size=100
        )
        limiter = RateLimiter(config)
        
        stats = limiter.get_global_stats()
        assert "available_tokens" in stats
        assert "capacity" in stats
        assert "refill_rate" in stats
        assert stats["capacity"] == 100
        assert stats["refill_rate"] == 50.0
    
    def test_cleanup_old_buckets(self):
        """Test cleanup of old per-user buckets."""
        config = RateLimitConfig(per_user=True)
        limiter = RateLimiter(config)
        
        # Create some user buckets
        import asyncio
        asyncio.run(limiter.acquire(user_id="user1"))
        asyncio.run(limiter.acquire(user_id="user2"))
        asyncio.run(limiter.acquire(user_id="user3"))
        
        # Should have 3 buckets
        assert len(limiter._user_buckets) == 3
        
        # Cleanup with max_age=0 should remove all
        removed = limiter.cleanup_old_buckets(max_age_seconds=0.0)
        assert removed == 3
        assert len(limiter._user_buckets) == 0
    
    def test_cleanup_preserves_recent_buckets(self):
        """Test cleanup doesn't remove recently used buckets."""
        config = RateLimitConfig(per_user=True)
        limiter = RateLimiter(config)
        
        # Create a bucket
        import asyncio
        asyncio.run(limiter.acquire(user_id="user1"))
        
        # Cleanup with large max_age shouldn't remove anything
        removed = limiter.cleanup_old_buckets(max_age_seconds=3600.0)
        assert removed == 0
        assert len(limiter._user_buckets) == 1


class TestRateLimiterGlobalFunctions:
    """Test global rate limiter instance functions."""
    
    def test_get_rate_limiter_singleton(self):
        """Test get_rate_limiter returns same instance."""
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()
        assert limiter1 is limiter2
    
    def test_configure_rate_limiter(self):
        """Test configure_rate_limiter creates new instance with config."""
        config = RateLimitConfig(requests_per_second=5.0)
        limiter = configure_rate_limiter(config)
        assert limiter.config.requests_per_second == 5.0
        
        # get_rate_limiter should now return the configured instance
        same_limiter = get_rate_limiter()
        assert same_limiter is limiter
    
    def test_configure_replaces_existing(self):
        """Test that configure_rate_limiter replaces existing instance."""
        limiter1 = get_rate_limiter()
        
        config = RateLimitConfig(requests_per_second=15.0)
        limiter2 = configure_rate_limiter(config)
        
        assert limiter1 is not limiter2
        assert limiter2.config.requests_per_second == 15.0
