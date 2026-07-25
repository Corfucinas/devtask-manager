"""Tests for audit log trail."""
import pytest
from datetime import datetime, timezone, timedelta
from src.audit import AuditLog, AuditEntry


@pytest.fixture
def log():
    log = AuditLog()
    log.log_action(1, "created", "alice", after={"title": "Task 1"})
    log.log_action(1, "status_changed", "bob",
                   before={"status": "todo"}, after={"status": "in-progress"})
    log.log_action(1, "assigned", "alice", after={"assignee": "charlie"})
    log.log_action(2, "created", "bob", after={"title": "Task 2"})
    return log


def test_log_action():
    log = AuditLog()
    entry = log.log_action(1, "created", "alice", after={"title": "Test"})
    assert entry.id == 1
    assert entry.task_id == 1
    assert entry.action == "created"
    assert entry.actor == "alice"
    assert entry.timestamp != ""


def test_audit_trail(log):
    trail = log.audit_trail(1)
    assert len(trail) == 3
    assert trail[0].action == "created"
    assert trail[-1].action == "assigned"


def test_audit_trail_empty(log):
    assert log.audit_trail(999) == []


def test_audit_by_actor(log):
    alice_entries = log.audit_by_actor("alice")
    assert len(alice_entries) == 2
    assert all(e.actor == "alice" for e in alice_entries)


def test_audit_by_action(log):
    created = log.audit_by_action("created")
    assert len(created) == 2
    assert all(e.action == "created" for e in created)


def test_recent_entries(log):
    recent = log.recent_entries(limit=2)
    assert len(recent) == 2
    assert recent[-1].action == "created"
    assert recent[-1].task_id == 2


def test_entry_count(log):
    assert log.entry_count() == 4
    assert log.entry_count(task_id=1) == 3
    assert log.entry_count(task_id=2) == 1


def test_first_entry(log):
    first = log.first_entry(1)
    assert first is not None
    assert first.action == "created"
    assert log.first_entry(999) is None


def test_last_entry(log):
    last = log.last_entry(1)
    assert last is not None
    assert last.action == "assigned"
    assert log.last_entry(999) is None


def test_to_dict(log):
    entries = log.to_dict()
    assert len(entries) == 4
    assert "id" in entries[0]
    assert "action" in entries[0]
    assert "actor" in entries[0]


def test_before_after_tracking(log):
    trail = log.audit_trail(1)
    status_change = trail[1]
    assert status_change.before == {"status": "todo"}
    assert status_change.after == {"status": "in-progress"}


def test_entries_between(log):
    now = datetime.now(timezone.utc)
    start = (now - timedelta(hours=1)).isoformat()
    end = (now + timedelta(hours=1)).isoformat()
    entries = log.entries_between(start, end)
    assert len(entries) == 4
