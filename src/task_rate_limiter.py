"""Rate limiter for task operations (token bucket)."""
import time as time_module
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TokenBucket:
    """A token bucket for one key."""
    capacity: float
    tokens: float
    refill_rate: float  # tokens per second
    last_refill: float

    def refill(self):
        """Add tokens based on elapsed time."""
        now = time_module.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    def try_consume(self, tokens: float = 1.0) -> bool:
        """Try to consume tokens from the bucket."""
        self.refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False


class RateLimiter:
    """Token-bucket rate limiter for task operations."""
    def __init__(self, rate_per_second: float = 10.0, burst: int = 20):
        self._rate = rate_per_second
        self._burst = burst
        self._buckets: Dict[str, TokenBucket] = {}

    @property
    def rate(self) -> float:
        return self._rate

    def set_rate(self, rate_per_second: float):
        self._rate = rate_per_second
        for bucket in self._buckets.values():
            bucket.refill_rate = rate_per_second

    def _get_bucket(self, key: str = "global") -> TokenBucket:
        if key not in self._buckets:
            self._buckets[key] = TokenBucket(
                capacity=float(self._burst), tokens=float(self._burst),
                refill_rate=self._rate, last_refill=time_module.time())
        return self._buckets[key]

    def can_proceed(self, key: str = "global", tokens: float = 1.0) -> bool:
        """Check if an operation can proceed without consuming."""
        return self._get_bucket(key).tokens >= tokens

    def consume(self, key: str = "global", tokens: float = 1.0) -> bool:
        """Consume tokens; returns False if rate limit exceeded."""
        return self._get_bucket(key).try_consume(tokens)

    def available(self, key: str = "global") -> float:
        """Return available tokens for a key."""
        bucket = self._get_bucket(key)
        bucket.refill()
        return round(bucket.tokens, 2)

    def reset(self, key: str = None):
        """Reset one or all buckets."""
        if key:
            self._buckets.pop(key, None)
        else:
            self._buckets.clear()

    def tracked_keys(self) -> List[str]:
        return sorted(self._buckets.keys())

    def key_count(self) -> int:
        return len(self._buckets)


def limiter_stats(limiter: RateLimiter) -> Dict:
    return {"rate": limiter.rate, "burst": limiter._burst,
            "tracked_keys": limiter.key_count(),
            "available_global": limiter.available()}


def default_limiter() -> RateLimiter:
    return RateLimiter(rate_per_second=5.0, burst=10)
