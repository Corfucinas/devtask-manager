"""Tests for enhanced task tracker."""
import pytest
from src.task_tracker_v2 import TrackerEvent, TaskTrackerV2, tracker_report, default_tracker


@pytest.fixture
def tracker():
    t = TaskTrackerV2()
    t.log_event(1, "created", actor="alice")
    t.log_event(1, "updated", actor="alice", before={"title": "old"}, after={"title": "new"})
    t.log_event(1, "status_changed", actor="bob", before={"status": "todo"}, after={"status": "in-progress"})
    t.log_event(2, "created", actor="bob")
    t.log_event(2, "assigned", actor="charlie", after={"assignee": "charlie"})
    return t


def test_log_event():
    t = TaskTrackerV2()
    e = t.log_event(1, "created", actor="alice")
    assert e.id == 1
    assert e.event_type == "created"
    assert e.actor == "alice"


def test_get_event(tracker):
    assert tracker.get_event(1) is not None
    assert tracker.get_event(1).event_type == "created"
    assert tracker.get_event(999) is None


def test_task_history(tracker):
    history = tracker.task_history(1)
    assert len(history) == 3
    assert history[0].event_type == "created"


def test_task_history_empty(tracker):
    assert tracker.task_history(999) == []


def test_recent_events(tracker):
    recent = tracker.recent_events(limit=2)
    assert len(recent) == 2


def test_all_events(tracker):
    assert len(tracker.all_events()) == 5


def test_event_count(tracker):
    assert tracker.event_count() == 5


def test_by_type(tracker):
    created = tracker.by_type("created")
    assert len(created) == 2


def test_by_actor(tracker):
    alice = tracker.by_actor("alice")
    assert len(alice) == 2


def test_tracked_tasks(tracker):
    assert tracker.tracked_tasks() == [1, 2]


def test_task_count(tracker):
    assert tracker.task_count() == 2


def test_clear(tracker):
    tracker.clear()
    assert tracker.event_count() == 0
    assert tracker.task_count() == 0


def test_search(tracker):
    results = tracker.search("created")
    assert len(results) == 2


def test_event_types(tracker):
    types = tracker.event_types()
    assert "created" in types
    assert "updated" in types


def test_actors(tracker):
    actors = tracker.actors()
    assert "alice" in actors
    assert "bob" in actors


def test_tracker_report(tracker):
    report = tracker_report(tracker)
    assert report["total_events"] == 5
    assert report["tracked_tasks"] == 2
    assert "by_type" in report


def test_default_tracker():
    t = default_tracker()
    assert t.event_count() == 0
    t.log_event(1, "created")
    assert t.event_count() == 1


def test_max_events():
    t = TaskTrackerV2(max_events=3)
    t.log_event(1, "a")
    t.log_event(2, "b")
    t.log_event(3, "c")
    t.log_event(4, "d")
    assert t.event_count() == 3
