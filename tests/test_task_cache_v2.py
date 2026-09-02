"""Tests for enhanced task cache."""
import pytest
from src.task_cache_v2 import (
    TaskCache, cache_stats, default_cache,
)


@pytest.fixture
def cache():
    return TaskCache(max_size=5)


def test_get_missing(cache):
    assert cache.get("nonexistent") is None
    assert cache.stats().misses == 1


def test_set_and_get(cache):
    cache.set("a", 1)
    assert cache.get("a") == 1
    assert cache.stats().hits == 1


def test_delete(cache):
    cache.set("a", 1)
    assert cache.delete("a") is True
    assert cache.get("a") is None


def test_clear(cache):
    cache.set("a", 1)
    cache.clear()
    assert cache.size() == 0


def test_size(cache):
    cache.set("a", 1)
    cache.set("b", 2)
    assert cache.size() == 2


def test_has(cache):
    cache.set("a", 1)
    assert cache.has("a") is True


def test_lru_eviction(cache):
    for i in range(5):
        cache.set(f"k{i}", i)
    cache.set("k5", 5)
    assert cache.get("k0") is None
    assert cache.get("k5") == 5


def test_lru_eviction_order():
    c = TaskCache(max_size=3)
    c.set("a", 1)
    c.set("b", 2)
    c.set("c", 3)
    c.get("a")
    c.set("d", 4)
    assert c.get("b") is None
    assert c.get("a") == 1


def test_get_or_set(cache):
    cache.set("a", 100)
    assert cache.get_or_set("a", lambda: 999) == 100
    assert cache.get_or_set("b", lambda: 200) == 200
    assert cache.get("b") == 200


def test_touch(cache):
    cache.set("a", 1)
    assert cache.touch("a") is True
    assert cache.touch("b") is False


def test_evict_lru(cache):
    for i in range(4):
        cache.set(f"k{i}", i)
    assert cache.evict_lru(2) == 2
    assert cache.size() == 2


def test_oldest_keys(cache):
    for i in range(4):
        cache.set(f"k{i}", i)
    assert cache.oldest_keys()[0] == "k0"


def test_warm_up(cache):
    cache.warm_up({"a": 1, "b": 2})
    assert cache.size() == 2


def test_stats(cache):
    cache.set("a", 1)
    cache.get("a")
    cache.get("missing")
    stats = cache.stats()
    assert stats.hits == 1
    assert stats.misses == 1


def test_detailed_stats(cache):
    cache.set("a", 1)
    detailed = cache_stats(cache)
    assert "utilization" in detailed


def test_default_cache():
    c = default_cache()
    assert c._max_size == 100
