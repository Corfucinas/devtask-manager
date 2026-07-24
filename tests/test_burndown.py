"""Tests for burndown chart generation."""
import pytest
from datetime import datetime, timezone, timedelta
from src.burndown import (
    ideal_burndown, actual_burndown, burndown_report,
    is_on_track, velocity_trend, projected_completion,
)


class FakeStatus:
    def __init__(self, value):
        self.value = value


class FakeTask:
    def __init__(self, id, completed_days_ago=None, story_points=3, status="done"):
        self.id = id
        self.status = FakeStatus(status)
        self.story_points = story_points
        if completed_days_ago is not None:
            self.completed_at = (datetime.now(timezone.utc) - timedelta(days=completed_days_ago)).isoformat()
        else:
            self.completed_at = None


def test_ideal_burndown():
    points = ideal_burndown(40, 10)
    assert len(points) == 11
    assert points[0]["ideal"] == 40
    assert points[10]["ideal"] == 0


def test_ideal_burndown_zero_days():
    points = ideal_burndown(20, 0)
    assert len(points) == 1
    assert points[0]["ideal"] == 20


def test_actual_burndown():
    start = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    tasks = [
        FakeTask(1, completed_days_ago=4, story_points=5),
        FakeTask(2, completed_days_ago=2, story_points=3),
        FakeTask(3, status="todo", story_points=8),
    ]
    data = actual_burndown(tasks, 16, start)
    assert len(data) >= 1
    assert data[0]["remaining"] == 16
    last = data[-1]
    assert last["remaining"] == 16 - 8


def test_burndown_report():
    start = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
    tasks = [FakeTask(1, completed_days_ago=1, story_points=5)]
    report = burndown_report(tasks, 20, 10, start)
    assert report["total_points"] == 20
    assert report["sprint_days"] == 10
    assert len(report["ideal"]) == 11
    assert "on_track" in report


def test_is_on_track_ahead():
    actual = [{"day": 3, "remaining": 10}]
    ideal = [{"day": 3, "ideal": 15}]
    assert is_on_track(actual, ideal) is True


def test_is_on_track_behind():
    actual = [{"day": 3, "remaining": 20}]
    ideal = [{"day": 3, "ideal": 15}]
    assert is_on_track(actual, ideal) is False


def test_is_on_track_empty():
    assert is_on_track([], []) is True


def test_velocity_trend():
    tasks = [
        FakeTask(1, completed_days_ago=0, story_points=3),
        FakeTask(2, completed_days_ago=1, story_points=5),
    ]
    trend = velocity_trend(tasks, sprint_days=5)
    assert len(trend) == 5
    assert all("velocity" in t for t in trend)


def test_projected_completion():
    tasks = [
        FakeTask(1, completed_days_ago=1, story_points=5),
        FakeTask(2, completed_days_ago=2, story_points=3),
    ]
    projected = projected_completion(tasks, 40, elapsed_days=5)
    assert projected is not None
    assert projected > 5


def test_projected_completion_no_progress():
    tasks = [FakeTask(1, status="todo", story_points=5)]
    assert projected_completion(tasks, 40, 5) is None


def test_projected_completion_zero_days():
    assert projected_completion([], 40, 0) is None
