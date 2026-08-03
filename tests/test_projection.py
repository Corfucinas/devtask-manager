"""Tests for velocity projection."""
import pytest
from datetime import datetime, timezone, timedelta
from src.projection import (
    remaining_tasks, completed_count, velocity_trend, average_velocity,
    velocity_std_dev, confidence_interval, project_completion,
    projection_report, estimate_sprint_completion, burn_rate,
    days_until_empty, velocity_by_day_of_week,
)


class FakeStatus:
    def __init__(self, value):
        self.value = value


class FakeTask:
    def __init__(self, id, status="todo", completed_days_ago=None):
        self.id = id
        self.status = FakeStatus(status)
        if completed_days_ago is not None:
            self.completed_at = (datetime.now(timezone.utc) - timedelta(days=completed_days_ago)).isoformat()
        else:
            self.completed_at = None


@pytest.fixture
def tasks():
    return [
        FakeTask(1, "done", completed_days_ago=0),
        FakeTask(2, "done", completed_days_ago=1),
        FakeTask(3, "done", completed_days_ago=2),
        FakeTask(4, "todo"),
        FakeTask(5, "todo"),
        FakeTask(6, "in-progress"),
    ]


def test_remaining_tasks(tasks):
    assert len(remaining_tasks(tasks)) == 3


def test_completed_count(tasks):
    assert completed_count(tasks) == 3


def test_velocity_trend(tasks):
    trend = velocity_trend(tasks, days=7)
    assert len(trend) == 7


def test_average_velocity(tasks):
    avg = average_velocity(tasks, days=7)
    assert avg > 0


def test_average_velocity_no_completions():
    tasks = [FakeTask(1, "todo")]
    assert average_velocity(tasks, days=7) == 0.0


def test_velocity_std_dev(tasks):
    std = velocity_std_dev(tasks, days=7)
    assert std >= 0


def test_confidence_interval():
    low, high = confidence_interval(5.0, 1.0, "95%")
    assert low < 5.0 < high


def test_project_completion(tasks):
    projection = project_completion(tasks, velocity_per_day=1.0)
    assert projection is not None
    assert projection["remaining_tasks"] == 3
    assert projection["days_needed"] == 3.0


def test_project_completion_zero_velocity(tasks):
    assert project_completion(tasks, 0.0) is None


def test_project_completion_no_remaining():
    tasks = [FakeTask(1, "done", completed_days_ago=1)]
    assert project_completion(tasks, 1.0) is None


def test_projection_report(tasks):
    report = projection_report(tasks, days=7)
    assert report["total_tasks"] == 6
    assert report["completed"] == 3
    assert "trend" in report


def test_estimate_sprint_completion(tasks):
    result = estimate_sprint_completion(tasks, sprint_days=10, velocity=0.5)
    assert result["remaining"] == 3
    assert result["estimated_completable"] == 3


def test_burn_rate(tasks):
    rate = burn_rate(tasks, days=7)
    assert rate >= 0


def test_days_until_empty(tasks):
    days = days_until_empty(tasks, velocity=1.0)
    assert days == 3


def test_days_until_empty_no_velocity(tasks):
    assert days_until_empty(tasks, 0.0) is None


def test_velocity_by_day_of_week(tasks):
    result = velocity_by_day_of_week(tasks)
    assert "Monday" in result
    assert "Sunday" in result
    total = sum(result.values())
    assert total == 3
