"""Tests for task history."""
import pytest
from src.task_history import HistoryEntry, TaskHistory, history_report, default_history


@pytest.fixture
def history():
    h = TaskHistory()
    h.record(1, "created", actor="alice")
    h.record(1, "status_changed", actor="alice", field_changed="status",
             old_value="todo", new_value="in-progress")
    h.record(1, "assigned", actor="bob", field_changed="assignee",
             old_value=None, new_value="charlie")
    h.record(2, "created", actor="bob")
    return h


def test_record():
    h = TaskHistory()
    entry = h.record(1, "created", actor="alice")
    assert entry.id == 1
    assert entry.task_id == 1
    assert entry.action == "created"


def test_for_task(history):
    entries = history.for_task(1)
    assert len(entries) == 3
    assert entries[0].action == "created"


def test_for_task_empty(history):
    assert history.for_task(999) == []


def test_recent(history):
    recent = history.recent(limit=2)
    assert len(recent) == 2


def test_entry_count(history):
    assert history.entry_count() == 4


def test_task_count(history):
    assert history.task_count() == 2


def test_by_action(history):
    created = history.by_action("created")
    assert len(created) == 2


def test_by_actor(history):
    alice = history.by_actor("alice")
    assert len(alice) == 2


def test_actions(history):
    actions = history.actions()
    assert "created" in actions
    assert "status_changed" in actions


def test_actors(history):
    actors = history.actors()
    assert "alice" in actors
    assert "bob" in actors


def test_clear(history):
    history.clear()
    assert history.entry_count() == 0
    assert history.task_count() == 0


def test_max_entries():
    h = TaskHistory(max_entries=3)
    h.record(1, "a")
    h.record(2, "b")
    h.record(3, "c")
    h.record(4, "d")
    assert h.entry_count() == 3


def test_history_report(history):
    report = history_report(history)
    assert report["total_entries"] == 4
    assert report["tracked_tasks"] == 2
    assert "by_action" in report
    assert "by_actor" in report


def test_default_history():
    h = default_history()
    assert h.entry_count() == 0
    h.record(1, "created")
    assert h.entry_count() == 1
