"""Tests for completion analysis."""
import pytest
from datetime import datetime, timezone, timedelta
from src.completion import (
    completion_rate, daily_completion_rate, predict_completion,
    CompletionAnalyzer, completion_report, completion_velocity,
    estimated_completion_date,
)


class FakeStatus:
    def __init__(self, value): self.value = value
class FakePriority:
    def __init__(self, value): self.value = value
class FakeTask:
    def __init__(self, id, status="todo", priority="medium", completed_days_ago=None):
        now = datetime.now(timezone.utc)
        self.id = id
        self.status = FakeStatus(status)
        self.priority = FakePriority(priority)
        self.completed_at = (now - timedelta(days=completed_days_ago)).isoformat() if completed_days_ago else None


@pytest.fixture
def tasks():
    return [FakeTask(1, "done", "high", 0), FakeTask(2, "done", "medium", 1),
            FakeTask(3, "done", "low", 2), FakeTask(4, "todo", "critical"),
            FakeTask(5, "in-progress", "medium")]


def test_completion_rate(tasks):
    assert completion_rate(tasks) == 60.0

def test_completion_rate_empty():
    assert completion_rate([]) == 0.0

def test_daily_completion_rate(tasks):
    daily = daily_completion_rate(tasks, days=7)
    assert len(daily) == 7

def test_predict_completion(tasks):
    p = predict_completion(tasks, days=7)
    assert p["remaining_tasks"] == 2

def test_predict_completion_all_done():
    tasks = [FakeTask(1, "done"), FakeTask(2, "done")]
    assert predict_completion(tasks, 7)["remaining_tasks"] == 0

def test_completion_analyzer_record():
    a = CompletionAnalyzer()
    s = a.record([FakeTask(1, "done"), FakeTask(2, "todo")])
    assert s["total"] == 2
    assert s["rate"] == 50.0

def test_completion_analyzer_trend():
    a = CompletionAnalyzer()
    a.record([FakeTask(1, "todo"), FakeTask(2, "todo")])
    a.record([FakeTask(1, "done"), FakeTask(2, "todo")])
    a.record([FakeTask(1, "done"), FakeTask(2, "done")])
    assert a.trend() in ("improving", "stable", "declining")

def test_completion_analyzer_count():
    a = CompletionAnalyzer()
    a.record([FakeTask(1, "done")])
    a.record([FakeTask(1, "todo")])
    assert a.count() == 2

def test_completion_analyzer_latest():
    a = CompletionAnalyzer()
    a.record([FakeTask(1, "done")])
    assert a.latest() is not None

def test_completion_analyzer_average_rate():
    a = CompletionAnalyzer()
    a.record([FakeTask(1, "done"), FakeTask(2, "todo")])
    assert a.average_rate() == 50.0

def test_completion_report(tasks):
    r = completion_report(tasks)
    assert r["total_tasks"] == 5
    assert r["done"] == 3
    assert "prediction" in r

def test_completion_report_empty():
    r = completion_report([])
    assert r["total_tasks"] == 0

def test_completion_velocity(tasks):
    assert completion_velocity(tasks, 7) >= 0

def test_estimated_completion_date(tasks):
    assert estimated_completion_date(tasks, velocity=1.0) is not None

def test_estimated_completion_date_all_done():
    tasks = [FakeTask(1, "done")]
    assert estimated_completion_date(tasks) is None

def test_estimated_completion_date_zero_velocity():
    tasks = [FakeTask(1, "todo")]
    assert estimated_completion_date(tasks, velocity=0) is None
