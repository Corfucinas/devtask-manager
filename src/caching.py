"""In-memory caching layer for task queries."""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Dict, List, Optional


@dataclass
class CacheEntry:
    """A single cache entry with TTL."""
    key: str
    value: Any
    expires_at: Optional[str] = None
    created_at: str = ""
    access_count: int = 0
    last_accessed: Optional[str] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    @property
    def is_expired(self):
        if not self.expires_at:
            return False
        try:
            exp = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
            return datetime.now(timezone.utc) > exp
        except (ValueError, TypeError):
            return False

    def touch(self):
        self.access_count += 1
        self.last_accessed = datetime.now(timezone.utc).isoformat()


class Cache:
    """In-memory cache with TTL support."""
    def __init__(self, default_ttl_seconds=300):
        self._entries = {}
        self._default_ttl = default_ttl_seconds
        self._hits = 0
        self._misses = 0

    def get(self, key):
        entry = self._entries.get(key)
        if entry is None:
            self._misses += 1
            return None
        if entry.is_expired:
            del self._entries[key]
            self._misses += 1
            return None
        entry.touch()
        self._hits += 1
        return entry.value

    def set(self, key, value, ttl_seconds=None):
        if ttl_seconds is None:
            ttl_seconds = self._default_ttl
        expires_at = None
        if ttl_seconds > 0:
            expires_at = (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).isoformat()
        self._entries[key] = CacheEntry(key=key, value=value, expires_at=expires_at)

    def delete(self, key):
        if key in self._entries:
            del self._entries[key]
            return True
        return False

    def clear(self):
        self._entries.clear()

    def size(self):
        self._purge_expired()
        return len(self._entries)

    def keys(self):
        self._purge_expired()
        return sorted(self._entries.keys())

    def invalidate(self, pattern=None):
        if pattern is None:
            count = len(self._entries)
            self._entries.clear()
            return count
        to_remove = [k for k in self._entries if k.startswith(pattern)]
        for k in to_remove:
            del self._entries[k]
        return len(to_remove)

    def stats(self):
        self._purge_expired()
        total = self._hits + self._misses
        return {"size": len(self._entries), "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(self._hits / max(total, 1) * 100, 1),
                "total_requests": total}

    def _purge_expired(self):
        expired = [k for k, e in self._entries.items() if e.is_expired]
        for k in expired:
            del self._entries[k]


def cached(cache, key, ttl_seconds=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache_key = f"{key}:{hash(str(args) + str(sorted(kwargs.items())))}"
            result = cache.get(cache_key)
            if result is not None:
                return result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl_seconds)
            return result
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator


def cache_stats(cache):
    stats = cache.stats()
    entries = cache._entries
    total_access = sum(e.access_count for e in entries.values())
    most_accessed = sorted([(k, e.access_count) for k, e in entries.items()],
                           key=lambda x: x[1], reverse=True)[:5]
    return {**stats, "total_accesses": total_access,
            "most_accessed": [{"key": k, "accesses": v} for k, v in most_accessed]}


def default_cache():
    return Cache(default_ttl_seconds=300)
