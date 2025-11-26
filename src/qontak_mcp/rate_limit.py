"""
Rate limiting implementation using token bucket algorithm.

This module provides rate limiting to protect against:
- API abuse and DoS attacks
- Qontak API rate limit exhaustion
- Resource exhaustion
"""

import time
import asyncio
from typing import Optional
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    
    # Requests per second (token refill rate)
    requests_per_second: float = 10.0
    
    # Maximum burst size (bucket capacity)
    burst_size: int = 20
    
    # Enable per-user rate limiting
    per_user: bool = True
    
    # Global rate limit (shared across all users)
    global_requests_per_second: float = 50.0
    global_burst_size: int = 100


@dataclass
class TokenBucket:
    """Token bucket implementation for rate limiting."""
    
    capacity: float
    refill_rate: float  # tokens per second
    tokens: float = field(default=0.0)
    last_refill: float = field(default_factory=time.monotonic)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)
    
    def __post_init__(self):
        # Start with full bucket
        self.tokens = self.capacity
    
    async def acquire(self, tokens: float = 1.0) -> bool:
        """
        Try to acquire tokens from the bucket.
        
        Args:
            tokens: Number of tokens to acquire (default: 1)
            
        Returns:
            True if tokens were acquired, False if rate limited
        """
        async with self._lock:
            now = time.monotonic()
            
            # Refill tokens based on elapsed time
            elapsed = now - self.last_refill
            self.tokens = min(
                self.capacity,
                self.tokens + (elapsed * self.refill_rate)
            )
            self.last_refill = now
            
            # Check if we have enough tokens
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            return False
    
    async def wait_for_token(self, tokens: float = 1.0, timeout: float = 30.0) -> bool:
        """
        Wait until tokens are available or timeout.
        
        Args:
            tokens: Number of tokens needed
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if tokens were acquired, False if timed out
        """
        start = time.monotonic()
        
        while True:
            if await self.acquire(tokens):
                return True
            
            elapsed = time.monotonic() - start
            if elapsed >= timeout:
                return False
            
            # Calculate time until enough tokens are available
            async with self._lock:
                tokens_needed = tokens - self.tokens
                wait_time = min(
                    tokens_needed / self.refill_rate,
                    timeout - elapsed,
                    0.1  # Max 100ms between checks
                )
            
            await asyncio.sleep(max(0.01, wait_time))
    
    @property
    def available_tokens(self) -> float:
        """Get current available tokens (without acquiring)."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        return min(self.capacity, self.tokens + (elapsed * self.refill_rate))


class RateLimiter:
    """
    Rate limiter with per-user and global limits.
    
    Uses token bucket algorithm for smooth rate limiting.
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None) -> None:
        """
        Initialize the rate limiter.
        
        Args:
            config: Rate limit configuration (uses defaults if not provided)
        """
        self.config = config or RateLimitConfig()
        
        # Per-user buckets
        self._user_buckets: dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(
                capacity=self.config.burst_size,
                refill_rate=self.config.requests_per_second
            )
        )
        
        # Global bucket
        self._global_bucket = TokenBucket(
            capacity=self.config.global_burst_size,
            refill_rate=self.config.global_requests_per_second
        )
        
        # Lock for bucket creation
        self._lock = asyncio.Lock()
    
    async def acquire(self, user_id: Optional[str] = None) -> bool:
        """
        Try to acquire a rate limit token.
        
        Checks both per-user and global limits.
        
        Args:
            user_id: Optional user identifier for per-user limiting
            
        Returns:
            True if request is allowed, False if rate limited
        """
        # Check global limit first
        if not await self._global_bucket.acquire():
            return False
        
        # Check per-user limit if enabled and user_id provided
        if self.config.per_user and user_id:
            async with self._lock:
                bucket = self._user_buckets[user_id]
            
            if not await bucket.acquire():
                # Refund global token since user is rate limited
                self._global_bucket.tokens = min(
                    self._global_bucket.capacity,
                    self._global_bucket.tokens + 1
                )
                return False
        
        return True
    
    async def check_rate_limit(
        self,
        user_id: Optional[str] = None,
        wait: bool = False,
        timeout: float = 30.0
    ) -> tuple[bool, Optional[str]]:
        """
        Check rate limit and optionally wait for availability.
        
        Args:
            user_id: Optional user identifier
            wait: Whether to wait for token availability
            timeout: Maximum time to wait if wait=True
            
        Returns:
            Tuple of (allowed: bool, error_message: Optional[str])
        """
        if wait:
            # Try to wait for global limit
            if not await self._global_bucket.wait_for_token(timeout=timeout):
                return False, "Rate limit exceeded. Please try again later."
            
            # Try to wait for per-user limit
            if self.config.per_user and user_id:
                async with self._lock:
                    bucket = self._user_buckets[user_id]
                
                if not await bucket.wait_for_token(timeout=timeout):
                    return False, "Rate limit exceeded for your account. Please try again later."
            
            return True, None
        else:
            if await self.acquire(user_id):
                return True, None
            return False, "Rate limit exceeded. Please try again later."
    
    def get_user_stats(self, user_id: str) -> dict:
        """
        Get rate limit statistics for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict with available tokens and limit info
        """
        if user_id in self._user_buckets:
            bucket = self._user_buckets[user_id]
            return {
                "available_tokens": bucket.available_tokens,
                "capacity": bucket.capacity,
                "refill_rate": bucket.refill_rate,
            }
        return {
            "available_tokens": self.config.burst_size,
            "capacity": self.config.burst_size,
            "refill_rate": self.config.requests_per_second,
        }
    
    def get_global_stats(self) -> dict:
        """Get global rate limit statistics."""
        return {
            "available_tokens": self._global_bucket.available_tokens,
            "capacity": self._global_bucket.capacity,
            "refill_rate": self._global_bucket.refill_rate,
        }
    
    def cleanup_old_buckets(self, max_age_seconds: float = 3600.0) -> int:
        """
        Remove old per-user buckets to free memory.
        
        Args:
            max_age_seconds: Remove buckets not used for this long
            
        Returns:
            Number of buckets removed
        """
        now = time.monotonic()
        to_remove = []
        
        for user_id, bucket in self._user_buckets.items():
            if now - bucket.last_refill > max_age_seconds:
                to_remove.append(user_id)
        
        for user_id in to_remove:
            del self._user_buckets[user_id]
        
        return len(to_remove)


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def configure_rate_limiter(config: RateLimitConfig) -> RateLimiter:
    """Configure and return the global rate limiter."""
    global _rate_limiter
    _rate_limiter = RateLimiter(config)
    return _rate_limiter
