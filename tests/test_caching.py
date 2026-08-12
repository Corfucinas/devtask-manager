"""Tests for in-memory caching."""
import pytest
import time
from src.caching import Cache, CacheEntry, cached, cache_stats, default_cache


@pytest.fixture
def cache():
    return Cache(default_ttl_seconds=300)


def test_set_and_get(cache):
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"


def test_get_missing(cache):
    assert cache.get("nonexistent") is None


def test_delete(cache):
    cache.set("key1", "value1")
    assert cache.delete("key1") is True
    assert cache.get("key1") is None


def test_clear(cache):
    cache.set("a", 1)
    cache.set("b", 2)
    cache.clear()
    assert cache.size() == 0


def test_size(cache):
    cache.set("a", 1)
    cache.set("b", 2)
    assert cache.size() == 2


def test_keys(cache):
    cache.set("c", 3)
    cache.set("a", 1)
    assert cache.keys() == ["a", "c"]


def test_ttl_expiration(cache):
    cache.set("temp", "value", ttl_seconds=1)
    assert cache.get("temp") == "value"
    time.sleep(1.1)
    assert cache.get("temp") is None


def test_no_ttl(cache):
    cache.set("permanent", "value", ttl_seconds=0)
    time.sleep(0.1)
    assert cache.get("permanent") == "value"


def test_invalidate_all(cache):
    cache.set("a", 1)
    cache.set("b", 2)
    assert cache.invalidate() == 2
    assert cache.size() == 0


def test_invalidate_pattern(cache):
    cache.set("task:1", "a")
    cache.set("task:2", "b")
    cache.set("sprint:1", "c")
    assert cache.invalidate("task:") == 2
    assert cache.get("task:1") is None
    assert cache.get("sprint:1") == "c"


def test_stats(cache):
    cache.set("a", 1)
    cache.get("a")
    cache.get("missing")
    stats = cache.stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["hit_rate"] == 50.0


def test_cache_entry_is_expired():
    entry = CacheEntry(key="test", value="val", expires_at="2020-01-01T00:00:00+00:00")
    assert entry.is_expired is True


def test_cache_entry_not_expired():
    entry = CacheEntry(key="test", value="val", expires_at=None)
    assert entry.is_expired is False


def test_cache_entry_touch():
    entry = CacheEntry(key="test", value="val")
    entry.touch()
    assert entry.access_count == 1


def test_cached_decorator():
    c = Cache()
    call_count = 0

    @cached(c, "expensive_op", ttl_seconds=60)
    def expensive_op(x):
        nonlocal call_count
        call_count += 1
        return x * 2

    assert expensive_op(5) == 10
    assert expensive_op(5) == 10
    assert call_count == 1


def test_cached_different_args():
    c = Cache()
    call_count = 0

    @cached(c, "op", ttl_seconds=60)
    def op(x):
        nonlocal call_count
        call_count += 1
        return x + 1

    op(1)
    op(2)
    assert call_count == 2


def test_cache_stats_detailed(cache):
    cache.set("a", 1)
    cache.get("a")
    cache.get("a")
    stats = cache_stats(cache)
    assert stats["total_accesses"] == 2


def test_default_cache():
    c = default_cache()
    c.set("key", "value")
    assert c.get("key") == "value"
