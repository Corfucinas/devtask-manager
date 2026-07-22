"""Tests for advanced filter CLI."""
import pytest
from datetime import datetime, timezone, timedelta
from src.filter_cli import (
    filter_by_date_range, filter_by_tags, filter_by_assignee,
    filter_by_priority, compose_filters, filter_inactive,
    filter_overdue, sort_by_created,
)


class FakeStatus:
    def __init__(self, value):
        self.value = value


class FakePriority:
    def __init__(self, value):
        self.value = value


class FakeTask:
    def __init__(self, id, tags=None, assignee=None, priority="medium",
                 created_days_ago=1, updated_days_ago=0, due_in_days=None, status="todo"):
        now = datetime.now(timezone.utc)
        self.id = id
        self.tags = tags or []
        self.assignee = assignee
        self.priority = FakePriority(priority)
        self.status = FakeStatus(status)
        self.created_at = (now - timedelta(days=created_days_ago)).isoformat()
        self.updated_at = (now - timedelta(days=updated_days_ago)).isoformat()
        if due_in_days is not None:
            self.due_date = (now + timedelta(days=due_in_days)).isoformat()
        else:
            self.due_date = None


@pytest.fixture
def tasks():
    return [
        FakeTask(1, tags=["bug", "auth"], assignee="alice", priority="high", created_days_ago=5),
        FakeTask(2, tags=["feature"], assignee="bob", priority="low", created_days_ago=10),
        FakeTask(3, tags=["bug", "ui"], assignee="alice", priority="critical", created_days_ago=2),
        FakeTask(4, tags=["docs"], assignee=None, priority="medium", created_days_ago=40, updated_days_ago=40),
    ]


def test_filter_by_date_range(tasks):
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=15)).isoformat()
    end = now.isoformat()
    results = filter_by_date_range(tasks, start, end)
    assert len(results) == 3
    assert {t.id for t in results} == {1, 2, 3}


def test_filter_by_tags_any(tasks):
    results = filter_by_tags(tasks, ["bug"], mode="any")
    assert len(results) == 2
    assert {t.id for t in results} == {1, 3}


def test_filter_by_tags_all(tasks):
    results = filter_by_tags(tasks, ["bug", "auth"], mode="all")
    assert len(results) == 1
    assert results[0].id == 1


def test_filter_by_tags_empty(tasks):
    results = filter_by_tags(tasks, [])
    assert len(results) == 4


def test_filter_by_assignee(tasks):
    results = filter_by_assignee(tasks, "alice")
    assert len(results) == 2
    assert {t.id for t in results} == {1, 3}


def test_filter_by_priority(tasks):
    results = filter_by_priority(tasks, ["high", "critical"])
    assert len(results) == 2
    assert {t.id for t in results} == {1, 3}


def test_compose_filters(tasks):
    results = compose_filters(
        tasks,
        lambda t: filter_by_assignee(t, "alice"),
        lambda t: filter_by_priority(t, ["high"]),
    )
    assert len(results) == 1
    assert results[0].id == 1


def test_filter_inactive(tasks):
    results = filter_inactive(tasks, days=30)
    assert len(results) == 1
    assert results[0].id == 4


def test_filter_overdue(tasks):
    overdue_task = FakeTask(5, due_in_days=-2, status="todo")
    results = filter_overdue(tasks + [overdue_task])
    assert len(results) == 1
    assert results[0].id == 5


def test_filter_overdue_done_excluded():
    task = FakeTask(1, due_in_days=-2, status="done")
    assert filter_overdue([task]) == []


def test_sort_by_created(tasks):
    sorted_tasks = sort_by_created(tasks)
    assert sorted_tasks[0].id == 3
    assert sorted_tasks[-1].id == 4


def test_sort_by_created_descending(tasks):
    sorted_tasks = sort_by_created(tasks, descending=True)
    assert sorted_tasks[0].id == 4
