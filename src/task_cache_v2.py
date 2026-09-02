"""Enhanced task cache with LRU eviction."""
from dataclasses import dataclass, field
from collections import OrderedDict
from typing import Any, Callable, Dict, List, Optional


@dataclass
class CacheStats:
    """Cache statistics."""
    size: int = 0
    max_size: int = 0
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    hit_rate: float = 0.0


class TaskCache:
    """LRU cache for task data."""
    def __init__(self, max_size: int = 100, default_ttl_seconds: int = 300):
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl_seconds
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache, moving it to most-recently-used."""
        if key not in self._cache:
            self._misses += 1
            return None
        self._cache.move_to_end(key)
        self._hits += 1
        return self._cache[key]

    def set(self, key: str, value: Any):
        """Set a value in cache."""
        if key in self._cache:
            self._cache.move_to_end(key)
        else:
            if len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)
                self._evictions += 1
        self._cache[key] = value

    def delete(self, key: str) -> bool:
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

    def keys(self) -> List[str]:
        return list(self._cache.keys())

    def has(self, key: str) -> bool:
        return key in self._cache

    def stats(self) -> CacheStats:
        total = self._hits + self._misses
        return CacheStats(
            size=len(self._cache), max_size=self._max_size,
            hits=self._hits, misses=self._misses,
            evictions=self._evictions,
            hit_rate=round(self._hits / max(total, 1) * 100, 1),
        )

    def get_or_set(self, key: str, callback: Callable) -> Any:
        value = self.get(key)
        if value is not None:
            return value
        value = callback()
        self.set(key, value)
        return value

    def touch(self, key: str) -> bool:
        return self.get(key) is not None

    def evict_lru(self, n: int = 1) -> int:
        count = 0
        for _ in range(min(n, len(self._cache))):
            self._cache.popitem(last=False)
            self._evictions += 1
            count += 1
        return count

    def oldest_keys(self, n: int = 5) -> List[str]:
        return list(self._cache.keys())[:n]

    def newest_keys(self, n: int = 5) -> List[str]:
        return list(self._cache.keys())[-n:]

    def warm_up(self, items: Dict[str, Any]):
        for key, value in items.items():
            self.set(key, value)


def cache_stats(cache: TaskCache) -> dict:
    """Return detailed cache statistics."""
    s = cache.stats()
    return {
        "size": s.size, "max_size": s.max_size,
        "hits": s.hits, "misses": s.misses,
        "evictions": s.evictions, "hit_rate": s.hit_rate,
        "utilization": round(s.size / max(s.max_size, 1) * 100, 1),
        "oldest_keys": cache.oldest_keys(5),
        "newest_keys": cache.newest_keys(5),
    }


def default_cache(max_size: int = 100) -> TaskCache:
    return TaskCache(max_size=max_size, default_ttl_seconds=300)
