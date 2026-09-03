"""Tests for task health indicator."""
import pytest
from datetime import datetime, timezone, timedelta
from src.task_health import (
    HealthIndicator, assess_health, assess_batch,
    health_report, healthiest_tasks, unhealthy_tasks,
)


class FakePriority:
    def __init__(self, value): self.value = value
class FakeStatus:
    def __init__(self, value): self.value = value
class FakeBlocker:
    def __init__(self, status="active"): self.status = status
class FakeTask:
    def __init__(self, id, priority="medium", status="todo", created_days_ago=1,
                 updated_days_ago=1, assignee=None, due_in_days=None,
                 tags=None, blockers=None):
        now = datetime.now(timezone.utc)
        self.id = id
        self.priority = FakePriority(priority)
        self.status = FakeStatus(status)
        self.created_at = (now - timedelta(days=created_days_ago)).isoformat()
        self.updated_at = (now - timedelta(days=updated_days_ago)).isoformat()
        self.assignee = assignee
        self.due_date = (now + timedelta(days=due_in_days)).isoformat() if due_in_days else None
        self.tags = tags or []
        self.blockers = blockers


def test_health_done_task():
    task = FakeTask(1, status="done")
    h = assess_health(task)
    assert h.score == 100.0
    assert h.grade == "A"
    assert h.is_healthy is True


def test_health_fresh_assigned():
    task = FakeTask(1, created_days_ago=1, updated_days_ago=0,
                    assignee="alice", due_in_days=7, tags=["bug"])
    h = assess_health(task)
    assert h.score > 50


def test_health_stale_unassigned():
    task = FakeTask(1, created_days_ago=60, updated_days_ago=60, assignee=None)
    h = assess_health(task)
    assert h.score < 50


def test_health_blocked():
    task = FakeTask(1, blockers=[FakeBlocker("active")], created_days_ago=1)
    h = assess_health(task)
    assert h.factors["blocking"] == 50


def test_health_overdue():
    task = FakeTask(1, due_in_days=-5, created_days_ago=1)
    h = assess_health(task)
    assert h.factors["due_date"] == 20


def test_health_no_due_date():
    task = FakeTask(1, created_days_ago=1)
    h = assess_health(task)
    assert h.factors["due_date"] == 50


def test_health_no_tags():
    task = FakeTask(1, tags=[], created_days_ago=1)
    h = assess_health(task)
    assert h.factors["tags"] == 40


def test_health_good_tags():
    task = FakeTask(1, tags=["bug", "auth"], created_days_ago=1)
    h = assess_health(task)
    assert h.factors["tags"] == 100


def test_health_too_many_tags():
    task = FakeTask(1, tags=["a", "b", "c", "d", "e", "f"], created_days_ago=1)
    h = assess_health(task)
    assert h.factors["tags"] == 50


def test_health_assess_batch():
    tasks = [FakeTask(1), FakeTask(2), FakeTask(3)]
    results = assess_batch(tasks)
    assert len(results) == 3


def test_health_report():
    tasks = [FakeTask(1), FakeTask(2, status="done"), FakeTask(3)]
    report = health_report(tasks)
    assert report["total_tasks"] == 3
    assert "average_score" in report
    assert "healthy" in report
    assert "grade_distribution" in report


def test_health_report_empty():
    report = health_report([])
    assert report["total_tasks"] == 0


def test_healthiest_tasks():
    tasks = [FakeTask(1, created_days_ago=1, assignee="alice", tags=["bug"]),
             FakeTask(2, created_days_ago=60, assignee=None)]
    top = healthiest_tasks(tasks, n=1)
    assert len(top) == 1
    assert top[0].score > 50


def test_unhealthy_tasks():
    tasks = [FakeTask(1, created_days_ago=90, updated_days_ago=90)]
    unhealthy = unhealthy_tasks(tasks, threshold=40)
    assert len(unhealthy) >= 1


def test_health_indicator_properties():
    h = HealthIndicator(task_id=1, score=50)
    assert h.is_critical is False
    assert h.needs_attention is True
    assert h.is_healthy is False
    h2 = HealthIndicator(task_id=2, score=20)
    assert h2.is_critical is True
    assert h2.needs_attention is False


def test_health_critical():
    task = FakeTask(1, created_days_ago=100, updated_days_ago=100,
                    assignee=None, tags=["a", "b", "c", "d", "e", "f", "g"])
    h = assess_health(task)
    assert h.score < 50
