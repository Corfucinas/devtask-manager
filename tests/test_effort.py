"""Tests for effort scoring."""
import pytest
from src.effort import (
    effort_score, complexity_level, risk_adjusted_effort,
    effort_distribution, total_effort, average_effort,
    highest_effort, effort_by_tag,
)


class FakePriority:
    def __init__(self, value):
        self.value = value


class FakeTask:
    def __init__(self, id, priority="medium", tags=None, description="", subtasks=None):
        self.id = id
        self.priority = FakePriority(priority)
        self.tags = tags or []
        self.description = description
        self.subtasks = subtasks or []


@pytest.fixture
def tasks():
    return [
        FakeTask(1, "high", ["refactor"], "Short desc"),
        FakeTask(2, "low", ["docs"], "x"),
        FakeTask(3, "critical", ["research"], "y" * 250),
        FakeTask(4, "medium", ["bug"], "z", [1, 2, 3]),
    ]


def test_effort_score_basic():
    task = FakeTask(1, "medium", ["bug"], "short")
    score = effort_score(task)
    assert score == 5.0


def test_effort_score_priority(tasks):
    assert effort_score(tasks[0]) > effort_score(tasks[1])


def test_effort_score_subtasks(tasks):
    score = effort_score(tasks[3])
    assert score >= 11.0


def test_complexity_level():
    assert complexity_level(2) == "trivial"
    assert complexity_level(5) == "simple"
    assert complexity_level(10) == "moderate"
    assert complexity_level(20) == "complex"
    assert complexity_level(50) == "research"


def test_risk_adjusted_effort():
    task = FakeTask(1, "medium", [], "x")
    assert risk_adjusted_effort(task, 1.5) == 7.5


def test_effort_distribution(tasks):
    dist = effort_distribution(tasks)
    assert sum(dist.values()) == 4


def test_total_effort(tasks):
    total = total_effort(tasks)
    assert total > 0


def test_average_effort(tasks):
    avg = average_effort(tasks)
    assert avg == pytest.approx(total_effort(tasks) / 4, abs=0.1)


def test_average_effort_empty():
    assert average_effort([]) == 0.0


def test_highest_effort(tasks):
    top = highest_effort(tasks)
    assert top is not None
    assert top.id == 3


def test_highest_effort_empty():
    assert highest_effort([]) is None


def test_effort_by_tag(tasks):
    by_tag = effort_by_tag(tasks)
    assert "refactor" in by_tag
    assert "docs" in by_tag
    assert "research" in by_tag
    assert by_tag["docs"] < by_tag["research"]
