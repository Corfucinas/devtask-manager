"""Tests for blocker tracking."""
import pytest
from datetime import datetime, timezone, timedelta
from src.blockers import (
    Blocker, add_blocker, resolve_blocker, waive_blocker,
    active_blockers, is_blocked, all_active_blockers,
    blockers_by_type, blocker_count, resolution_time,
)


class FakeTask:
    def __init__(self, id):
        self.id = id
        self.blockers = None


@pytest.fixture
def task():
    t = FakeTask(1)
    add_blocker(t, "Waiting on API access", "external")
    add_blocker(t, "Need design review", "dependency")
    return t


def test_add_blocker():
    t = FakeTask(1)
    b = add_blocker(t, "Database down", "technical")
    assert b.id == 1
    assert b.description == "Database down"
    assert b.blocker_type == "technical"
    assert b.status == "active"
    assert len(t.blockers) == 1


def test_resolve_blocker(task):
    assert resolve_blocker(task, 1, resolver="alice", note="Got API access") is True
    assert task.blockers[0].status == "resolved"
    assert task.blockers[0].resolver == "alice"
    assert task.blockers[0].resolved_at is not None
    assert resolve_blocker(task, 999) is False


def test_waive_blocker(task):
    assert waive_blocker(task, 2, reason="No longer needed") is True
    assert task.blockers[1].status == "waived"
    assert task.blockers[1].resolution_note == "No longer needed"


def test_active_blockers(task):
    active = active_blockers(task)
    assert len(active) == 2
    resolve_blocker(task, 1)
    active = active_blockers(task)
    assert len(active) == 1
    assert active[0].id == 2


def test_is_blocked(task):
    assert is_blocked(task) is True
    resolve_blocker(task, 1)
    resolve_blocker(task, 2)
    assert is_blocked(task) is False


def test_is_blocked_no_blockers():
    t = FakeTask(1)
    assert is_blocked(t) is False


def test_all_active_blockers():
    t1 = FakeTask(1)
    add_blocker(t1, "Blocker 1", "external")
    t2 = FakeTask(2)
    add_blocker(t2, "Blocker 2", "technical")
    results = all_active_blockers([t1, t2])
    assert len(results) == 2
    assert results[0]["task_id"] == 1
    assert results[1]["task_id"] == 2


def test_blockers_by_type():
    t1 = FakeTask(1)
    add_blocker(t1, "External", "external")
    add_blocker(t1, "Technical", "technical")
    t2 = FakeTask(2)
    add_blocker(t2, "Also external", "external")
    external = blockers_by_type([t1, t2], "external")
    assert len(external) == 2


def test_blocker_count(task):
    assert blocker_count(task) == 2


def test_blocker_count_empty():
    t = FakeTask(1)
    assert blocker_count(t) == 0


def test_resolution_time():
    b = Blocker(id=1, description="test")
    b.created_at = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    b.resolved_at = datetime.now(timezone.utc).isoformat()
    time_hrs = resolution_time(b)
    assert time_hrs == pytest.approx(2.0, abs=0.1)


def test_resolution_time_unresolved():
    b = Blocker(id=1, description="test")
    assert resolution_time(b) == 0.0
