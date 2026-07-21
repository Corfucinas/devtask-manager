"""Tests for task estimation."""
import pytest
from src.estimation import (
    estimate_task, fibonacci_estimate, confidence_score,
    velocity_by_developer, burndown_remaining,
)


class FakeStatus:
    def __init__(self, value):
        self.value = value


class FakeTask:
    def __init__(self, status="todo", story_points=3, assignee="alice"):
        self.status = FakeStatus(status)
        self.story_points = story_points
        self.assignee = assignee


def test_estimate_simple():
    points = estimate_task("simple", uncertainty=0, dependency_count=0)
    assert points == 2


def test_estimate_with_uncertainty():
    points = estimate_task("moderate", uncertainty=5, dependency_count=0)
    assert points in (5, 8)


def test_estimate_with_dependencies():
    points = estimate_task("complex", uncertainty=0, dependency_count=3)
    assert points >= 8


def test_fibonacci_snap():
    assert fibonacci_estimate(4) == 5
    assert fibonacci_estimate(6) == 5
    assert fibonacci_estimate(7) == 8
    assert fibonacci_estimate(0) == 1


def test_confidence_perfect():
    assert confidence_score(5, 5) == 100


def test_confidence_overestimate():
    assert confidence_score(8, 5) == 62


def test_confidence_underestimate():
    assert confidence_score(3, 5) == 60


def test_velocity_by_developer():
    tasks = [
        FakeTask("done", 5, "alice"),
        FakeTask("done", 3, "alice"),
        FakeTask("done", 8, "bob"),
        FakeTask("todo", 5, "alice"),
    ]
    assert velocity_by_developer(tasks, "alice") == 8


def test_burndown_remaining():
    tasks = [FakeTask("done", 5), FakeTask("todo", 3), FakeTask("in-progress", 8)]
    assert burndown_remaining(tasks, 16) == 11
