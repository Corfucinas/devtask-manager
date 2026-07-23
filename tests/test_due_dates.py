"""Tests for due date management."""
import pytest
from datetime import datetime, timezone, timedelta
from src.due_dates import (
    set_due_date, is_overdue, days_until_due, due_soon,
    overdue_tasks, due_summary, remove_due_date, reschedule, reschedule_count,
)


class FakeStatus:
    def __init__(self, value):
        self.value = value


class FakeTask:
    def __init__(self, id, status="todo", due_date=None):
        self.id = id
        self.status = FakeStatus(status)
        self.due_date = due_date
        self.reschedule_history = None


@pytest.fixture
def tasks():
    now = datetime.now(timezone.utc)
    return [
        FakeTask(1, "todo", (now - timedelta(days=2)).isoformat()),
        FakeTask(2, "todo", (now + timedelta(days=2)).isoformat()),
        FakeTask(3, "done", (now - timedelta(days=5)).isoformat()),
        FakeTask(4, "todo"),
        FakeTask(5, "in-progress", (now + timedelta(days=1)).isoformat()),
    ]


def test_set_due_date():
    task = FakeTask(1)
    set_due_date(task, "2026-12-31T00:00:00+00:00")
    assert task.due_date == "2026-12-31T00:00:00+00:00"


def test_is_overdue(tasks):
    assert is_overdue(tasks[0]) is True
    assert is_overdue(tasks[1]) is False
    assert is_overdue(tasks[2]) is False
    assert is_overdue(tasks[3]) is False


def test_days_until_due(tasks):
    assert days_until_due(tasks[0]) < 0
    assert days_until_due(tasks[1]) == 2
    assert days_until_due(tasks[3]) is None


def test_due_soon(tasks):
    soon = due_soon(tasks, within_days=3)
    ids = {t.id for t in soon}
    assert ids == {2, 5}


def test_overdue_tasks(tasks):
    overdue = overdue_tasks(tasks)
    assert len(overdue) == 1
    assert overdue[0].id == 1


def test_due_summary(tasks):
    summary = due_summary(tasks)
    assert summary["overdue"] == 1
    assert summary["due_soon"] == 2
    assert summary["no_due_date"] == 1
    assert summary["total"] == 5


def test_remove_due_date(tasks):
    remove_due_date(tasks[0])
    assert tasks[0].due_date is None


def test_reschedule():
    task = FakeTask(1, due_date="2026-01-01T00:00:00+00:00")
    reschedule(task, "2026-02-01T00:00:00+00:00")
    assert task.due_date == "2026-02-01T00:00:00+00:00"
    assert len(task.reschedule_history) == 1


def test_reschedule_count():
    task = FakeTask(1, due_date="2026-01-01T00:00:00+00:00")
    assert reschedule_count(task) == 0
    reschedule(task, "2026-02-01T00:00:00+00:00")
    reschedule(task, "2026-03-01T00:00:00+00:00")
    assert reschedule_count(task) == 2
