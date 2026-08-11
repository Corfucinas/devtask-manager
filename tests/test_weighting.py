"""Tests for weighted scoring."""
import pytest
from datetime import datetime, timezone, timedelta
from src.weighting import (
    WeightProfile, score, rank, top_n, score_breakdown, default_profiles,
)


class FakePriority:
    def __init__(self, value):
        self.value = value


class FakeStatus:
    def __init__(self, value):
        self.value = value


class FakeBlocker:
    def __init__(self, status="active"):
        self.status = status


class FakeTask:
    def __init__(self, id, priority="medium", status="todo", created_days_ago=1,
                 due_in_days=None, story_points=5, dependents=None,
                 dependencies=None, blockers=None):
        now = datetime.now(timezone.utc)
        self.id = id
        self.priority = FakePriority(priority)
        self.status = FakeStatus(status)
        self.created_at = (now - timedelta(days=created_days_ago)).isoformat()
        self.due_date = (now + timedelta(days=due_in_days)).isoformat() if due_in_days else None
        self.story_points = story_points
        self.dependents = dependents or []
        self.dependencies = dependencies or []
        self.blockers = blockers


@pytest.fixture
def tasks():
    return [
        FakeTask(1, "critical", "todo", created_days_ago=5, due_in_days=1, story_points=3),
        FakeTask(2, "medium", "todo", created_days_ago=1, due_in_days=14, story_points=8),
        FakeTask(3, "low", "done", created_days_ago=10, story_points=2),
        FakeTask(4, "high", "in-progress", created_days_ago=3, due_in_days=3, story_points=5,
                 dependents=[1, 2], blockers=[FakeBlocker()]),
    ]


def test_weight_profile_normalize():
    p = WeightProfile(name="test", priority_weight=2, age_weight=2)
    n = p.normalize()
    assert n.priority_weight == pytest.approx(0.5, abs=0.01)


def test_score_basic(tasks):
    assert score(tasks[0]) > 0


def test_score_done_is_zero(tasks):
    assert score(tasks[2]) == 0.0


def test_score_critical_higher(tasks):
    assert score(tasks[0]) > score(tasks[1])


def test_rank(tasks):
    ranked = rank(tasks)
    assert len(ranked) == 4
    assert ranked[0]["score"] >= ranked[1]["score"]


def test_rank_order(tasks):
    ranked = rank(tasks)
    ids = [r["id"] for r in ranked]
    assert ids[0] == 1
    assert ids[-1] == 3


def test_top_n(tasks):
    assert len(top_n(tasks, n=2)) == 2


def test_score_breakdown(tasks):
    b = score_breakdown(tasks[0])
    assert "priority" in b
    assert "total" in b


def test_score_breakdown_priority(tasks):
    assert score_breakdown(tasks[0])["priority"] == 100.0


def test_default_profiles():
    p = default_profiles()
    assert "balanced" in p
    assert "urgency_first" in p
    assert "quick_wins" in p
    assert "critical_path" in p


def test_default_profiles_normalized():
    for name, p in default_profiles().items():
        total = (p.priority_weight + p.age_weight + p.complexity_weight +
                 p.urgency_weight + p.dependency_weight + p.effort_weight)
        assert total == pytest.approx(1.0, abs=0.01)


def test_score_blocked_task(tasks):
    assert score(tasks[3]) > 0


def test_score_breakdown_dependency(tasks):
    assert score_breakdown(tasks[3])["dependency"] > 0
