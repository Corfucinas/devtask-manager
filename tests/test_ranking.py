"""Tests for task ranking algorithm."""
import pytest
from datetime import datetime, timezone, timedelta
from src.ranking import (
    task_score, rank_tasks, top_n, ranking_report,
    score_breakdown, adjust_weights, default_weights,
)


class FakeStatus:
    def __init__(self, value):
        self.value = value


class FakePriority:
    def __init__(self, value):
        self.value = value


class FakeTask:
    def __init__(self, id, title="task", priority="medium", status="todo",
                 tags=None, due_in_days=None, created_days_ago=1,
                 dependents=None, story_points=None):
        now = datetime.now(timezone.utc)
        self.id = id
        self.title = title
        self.priority = FakePriority(priority)
        self.status = FakeStatus(status)
        self.tags = tags or []
        self.created_at = (now - timedelta(days=created_days_ago)).isoformat()
        self.due_date = (now + timedelta(days=due_in_days)).isoformat() if due_in_days is not None else None
        self.dependents = dependents or []
        self.story_points = story_points


@pytest.fixture
def tasks():
    return [
        FakeTask(1, "Critical bug", "critical", "todo", ["bug", "urgent"], due_in_days=1, story_points=3),
        FakeTask(2, "Add feature", "medium", "todo", ["feature"], due_in_days=14, story_points=8),
        FakeTask(3, "Write docs", "low", "done", ["docs"], story_points=2),
        FakeTask(4, "Fix issue", "high", "in-progress", ["bug"], due_in_days=3, story_points=5),
    ]


def test_task_score_basic(tasks):
    assert task_score(tasks[0]) > 0


def test_task_score_done_is_zero(tasks):
    assert task_score(tasks[2]) == 0.0


def test_task_score_critical_higher(tasks):
    assert task_score(tasks[0]) > task_score(tasks[1])


def test_rank_tasks(tasks):
    ranked = rank_tasks(tasks)
    assert len(ranked) == 4
    assert ranked[0]["score"] >= ranked[1]["score"]


def test_rank_tasks_order(tasks):
    ranked = rank_tasks(tasks)
    ids = [r["id"] for r in ranked]
    assert ids[0] == 1
    assert ids[-1] == 3


def test_top_n(tasks):
    top = top_n(tasks, n=2)
    assert len(top) == 2


def test_ranking_report(tasks):
    report = ranking_report(tasks)
    assert report["total_tasks"] == 4
    assert len(report["ranked"]) == 4
    assert report["ranked"][0]["rank"] == 1


def test_ranking_report_empty():
    report = ranking_report([])
    assert report["total_tasks"] == 0


def test_score_breakdown(tasks):
    breakdown = score_breakdown(tasks[0])
    assert "priority" in breakdown
    assert "urgency" in breakdown
    assert breakdown["priority"] == 100


def test_default_weights():
    weights = default_weights()
    assert sum(weights.values()) == pytest.approx(1.0, abs=0.01)


def test_adjust_weights():
    base = default_weights()
    adjusted = adjust_weights(base, priority=0.1)
    assert sum(adjusted.values()) == pytest.approx(1.0, abs=0.01)


def test_overdue_scores_high():
    task = FakeTask(1, "Overdue", "medium", "todo", due_in_days=-2)
    assert score_breakdown(task)["urgency"] == 100


def test_quick_win_high_effort_score():
    task = FakeTask(1, "Quick", "medium", "todo", story_points=1)
    assert score_breakdown(task)["effort"] == 90
