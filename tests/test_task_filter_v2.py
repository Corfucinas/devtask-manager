"""Tests for advanced task filter."""
import pytest
from datetime import datetime, timezone, timedelta
from src.task_filter_v2 import (
    Filter, FilterChain, FilterBuilder, filter_report,
)


class FakePriority:
    def __init__(self, value): self.value = value
class FakeStatus:
    def __init__(self, value): self.value = value
class FakeTask:
    def __init__(self, id, priority="medium", status="todo", tags=None,
                 assignee=None, due_date=None):
        self.id = id
        self.priority = FakePriority(priority)
        self.status = FakeStatus(status)
        self.tags = tags or []
        self.assignee = assignee
        self.due_date = due_date


@pytest.fixture
def tasks():
    now = datetime.now(timezone.utc)
    return [
        FakeTask(1, "high", "todo", ["bug", "auth"], "alice"),
        FakeTask(2, "low", "done", ["docs"], "bob"),
        FakeTask(3, "critical", "in-progress", ["bug"], "alice",
                 due_date=(now - timedelta(days=1)).isoformat()),
        FakeTask(4, "medium", "todo", [], None),
    ]


def test_filter_chain_and(tasks):
    chain = FilterBuilder.all().priority("high")
    result = chain.apply(tasks)
    assert len(result) == 1
    assert result[0].id == 1


def test_filter_chain_or(tasks):
    chain = FilterBuilder.any().priority("high").priority("critical")
    result = chain.apply(tasks)
    assert len(result) == 2


def test_filter_has_tag(tasks):
    chain = FilterBuilder.all().has_tag("bug")
    result = chain.apply(tasks)
    assert len(result) == 2


def test_filter_assigned_to(tasks):
    chain = FilterBuilder.all().assigned_to("alice")
    result = chain.apply(tasks)
    assert len(result) == 2


def test_filter_unassigned(tasks):
    chain = FilterBuilder.all().unassigned()
    result = chain.apply(tasks)
    assert len(result) == 1
    assert result[0].id == 4


def test_filter_overdue(tasks):
    chain = FilterBuilder.all().overdue()
    result = chain.apply(tasks)
    assert len(result) == 1
    assert result[0].id == 3


def test_filter_negate(tasks):
    chain = FilterBuilder.all().priority("high").negate("priority=high")
    result = chain.apply(tasks)
    assert len(result) == 3


def test_filter_sort_by(tasks):
    chain = FilterBuilder.all().sort_by(lambda t: t.id, reverse=True)
    result = chain.apply(tasks)
    assert result[0].id == 4


def test_filter_limit(tasks):
    chain = FilterBuilder.all().limit(2)
    result = chain.apply(tasks)
    assert len(result) == 2


def test_filter_chain_multiple(tasks):
    chain = (FilterBuilder.all()
             .has_tag("bug")
             .priority("critical"))
    result = chain.apply(tasks)
    assert len(result) == 1
    assert result[0].id == 3


def test_preset_high_priority(tasks):
    chain = FilterBuilder.high_priority()
    result = chain.apply(tasks)
    assert len(result) == 1


def test_preset_overdue(tasks):
    chain = FilterBuilder.overdue()
    result = chain.apply(tasks)
    assert len(result) == 1


def test_preset_my_tasks(tasks):
    chain = FilterBuilder.my_tasks("alice")
    result = chain.apply(tasks)
    assert len(result) == 2


def test_filter_count(tasks):
    chain = FilterBuilder.all().priority("high").has_tag("bug")
    assert chain.filter_count == 2


def test_filter_report(tasks):
    chain = FilterBuilder.all().priority("high")
    report = filter_report(tasks, chain)
    assert report["total_tasks"] == 4
    assert report["filtered_count"] == 1
    assert "by_status" in report
    assert "by_priority" in report


def test_filter_report_empty(tasks):
    chain = FilterBuilder.all().priority("nonexistent")
    report = filter_report(tasks, chain)
    assert report["filtered_count"] == 0
    assert report["remaining_percentage"] == 0.0
