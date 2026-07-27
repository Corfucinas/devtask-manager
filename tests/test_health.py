"""Tests for project health scoring."""
import pytest
from datetime import datetime, timezone, timedelta
from src.health import (
    completion_rate, stale_ratio, overdue_ratio, blocked_ratio,
    unassigned_ratio, priority_balance, health_score, health_grade,
    health_report,
)


class FakeStatus:
    def __init__(self, value):
        self.value = value


class FakePriority:
    def __init__(self, value):
        self.value = value


class FakeBlocker:
    def __init__(self, status="active"):
        self.status = status


class FakeTask:
    def __init__(self, id, status="todo", priority="medium", updated_days_ago=0,
                 due_in_days=None, assignee=None, blockers=None):
        now = datetime.now(timezone.utc)
        self.id = id
        self.status = FakeStatus(status)
        self.priority = FakePriority(priority)
        self.updated_at = (now - timedelta(days=updated_days_ago)).isoformat()
        if due_in_days is not None:
            self.due_date = (now + timedelta(days=due_in_days)).isoformat()
        else:
            self.due_date = None
        self.assignee = assignee
        self.blockers = blockers


@pytest.fixture
def healthy_tasks():
    return [
        FakeTask(1, "done", "medium", 1, assignee="alice"),
        FakeTask(2, "done", "high", 2, assignee="bob"),
        FakeTask(3, "in-progress", "medium", 0, due_in_days=7, assignee="alice"),
        FakeTask(4, "todo", "low", 1, due_in_days=14, assignee="charlie"),
    ]


@pytest.fixture
def unhealthy_tasks():
    return [
        FakeTask(1, "todo", "critical", 30, due_in_days=-5, assignee=None),
        FakeTask(2, "todo", "critical", 25, due_in_days=-3, assignee=None,
                 blockers=[FakeBlocker("active")]),
        FakeTask(3, "in-progress", "high", 20, assignee="alice"),
        FakeTask(4, "todo", "critical", 30, assignee=None),
    ]


def test_completion_rate(healthy_tasks):
    assert completion_rate(healthy_tasks) == 50.0


def test_completion_rate_empty():
    assert completion_rate([]) == 0.0


def test_stale_ratio(healthy_tasks):
    assert stale_ratio(healthy_tasks, threshold_days=14) == 0.0


def test_stale_ratio_unhealthy(unhealthy_tasks):
    ratio = stale_ratio(unhealthy_tasks, threshold_days=14)
    assert ratio == 75.0


def test_overdue_ratio(unhealthy_tasks):
    assert overdue_ratio(unhealthy_tasks) == 50.0


def test_overdue_ratio_none(healthy_tasks):
    assert overdue_ratio(healthy_tasks) == 0.0


def test_blocked_ratio(unhealthy_tasks):
    assert blocked_ratio(unhealthy_tasks) == 25.0


def test_blocked_ratio_none(healthy_tasks):
    assert blocked_ratio(healthy_tasks) == 0.0


def test_unassigned_ratio(unhealthy_tasks):
    assert unassigned_ratio(unhealthy_tasks) == 75.0


def test_unassigned_ratio_none(healthy_tasks):
    assert unassigned_ratio(healthy_tasks) == 0.0


def test_priority_balance(healthy_tasks):
    balance = priority_balance(healthy_tasks)
    assert balance["medium"] == 2
    assert balance["high"] == 1
    assert balance["low"] == 1


def test_health_score_healthy(healthy_tasks):
    score = health_score(healthy_tasks)
    assert score > 70


def test_health_score_unhealthy(unhealthy_tasks):
    score = health_score(unhealthy_tasks)
    assert score < 50


def test_health_score_empty():
    assert health_score([]) == 100.0


def test_health_grade():
    assert health_grade(95) == "A"
    assert health_grade(85) == "B"
    assert health_grade(75) == "C"
    assert health_grade(65) == "D"
    assert health_grade(45) == "F"


def test_health_report(healthy_tasks):
    report = health_report(healthy_tasks)
    assert report["total_tasks"] == 4
    assert "health_score" in report
    assert "grade" in report
    assert "issues" in report
    assert isinstance(report["issues"], list)


def test_health_report_empty():
    report = health_report([])
    assert report["total_tasks"] == 0
    assert "No tasks" in report["issues"][0]


def test_health_report_issues(unhealthy_tasks):
    report = health_report(unhealthy_tasks)
    issues = report["issues"]
    assert len(issues) > 0
