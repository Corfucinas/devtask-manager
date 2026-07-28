"""Tests for activity feed."""
import pytest
from datetime import datetime, timezone, timedelta
from src.activity import Activity, ActivityFeed


@pytest.fixture
def feed():
    f = ActivityFeed()
    f.log("created", "alice", target_id=1)
    f.log("updated", "bob", target_id=1)
    f.log("completed", "alice", target_id=2)
    f.log("assigned", "charlie", target_id=1)
    f.log("commented", "bob", target_id=2)
    return f


def test_log():
    f = ActivityFeed()
    a = f.log("created", "alice", target_id=1)
    assert a.id == 1
    assert a.activity_type == "created"
    assert a.actor == "alice"


def test_recent(feed):
    recent = feed.recent(limit=2)
    assert len(recent) == 2
    assert recent[-1].activity_type == "commented"


def test_feed_by_type(feed):
    created = feed.feed_by_type("created")
    assert len(created) == 1


def test_feed_by_actor(feed):
    alice = feed.feed_by_actor("alice")
    assert len(alice) == 2


def test_feed_by_target(feed):
    target1 = feed.feed_by_target(1)
    assert len(target1) == 3


def test_count(feed):
    assert feed.count() == 5


def test_clear(feed):
    feed.clear()
    assert feed.count() == 0


def test_activity_types(feed):
    types = feed.activity_types()
    assert types["created"] == 1


def test_actor_activity(feed):
    actors = feed.actor_activity()
    assert actors["alice"] == 2


def test_search(feed):
    results = feed.search("creat")
    assert len(results) == 1


def test_feed_since(feed):
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    results = feed.feed_since(cutoff)
    assert len(results) == 5


def test_timeline(feed):
    tl = feed.timeline(group_by="day")
    assert len(tl) >= 1


def test_max_size():
    f = ActivityFeed(max_size=3)
    f.log("a", "alice")
    f.log("b", "bob")
    f.log("c", "charlie")
    f.log("d", "alice")
    assert f.count() == 3
    assert f.recent(1)[0].activity_type == "d"
