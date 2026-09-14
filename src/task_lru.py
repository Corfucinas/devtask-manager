"""LRU cache for expensive computations."""
from collections import OrderedDict
from typing import Any, Callable, Dict, List, Optional, Tuple


class LRUCache:
    """Least-recently-used cache with capacity eviction."""
    def __init__(self, capacity: int = 128):
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self._capacity = capacity
        self._cache: OrderedDict = OrderedDict()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    @property
    def capacity(self) -> int:
        return self._capacity

    def get(self, key) -> Any:
        """Get value; None on miss. Marks key as recently used."""
        if key in self._cache:
            self._cache.move_to_end(key)
            self._hits += 1
            return self._cache[key]
        self._misses += 1
        return None

    def set(self, key, value):
        """Set value; evicts LRU entry if over capacity."""
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        while len(self._cache) > self._capacity:
            self._cache.popitem(last=False)
            self._evictions += 1

    def compute(self, key, factory: Callable) -> Any:
        """Get-or-compute: uses cache on hit, factory on miss."""
        value = self.get(key)
        if value is not None:
            return value
        value = factory()
        self.set(key, value)
        return value

    def has(self, key) -> bool:
        return key in self._cache

    def delete(self, key) -> bool:
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self):
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def size(self) -> int:
        return len(self._cache)

    def keys(self) -> List:
        """Return keys oldest-to-newest."""
        return list(self._cache.keys())

    def peek(self, key) -> Any:
        """Get without affecting recency or stats."""
        return self._cache.get(key)

    def stats(self) -> Dict:
        total = self._hits + self._misses
        return {"size": self.size(), "capacity": self.capacity,
                "hits": self._hits, "misses": self._misses,
                "evictions": self._evictions,
                "hit_rate": round(self._hits / max(total, 1) * 100, 1)}

    def touch(self, key) -> bool:
        """Mark a key recently used without fetching value."""
        if key in self._cache:
            self._cache.move_to_end(key)
            return True
        return False


def cached(capacity: int = 128):
    """Decorator: memoize a single-arg function in an LRU cache."""
    cache = LRUCache(capacity)
    def decorator(func):
        def wrapper(key):
            return cache.compute(key, lambda: func(key))
        wrapper.cache = cache
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator
