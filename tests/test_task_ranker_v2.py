"""Tests for task ranker v2."""
import pytest
from datetime import datetime, timezone, timedelta
from src.task_ranker_v2 import (
    ScoringConfig, RankerV2, rank_tasks, ranking_report, default_ranker,
)


class FakePriority:
    def __init__(self, value): self.value = value
class FakeStatus:
    def __init__(self, value): self.value = value
class FakeTask:
    def __init__(self, id, priority="medium", status="todo", due_in_days=None,
                 created_days_ago=1, story_points=5, dependents=None):
        now = datetime.now(timezone.utc)
        self.id = id
        self.priority = FakePriority(priority)
        self.status = FakeStatus(status)
        self.due_date = (now + timedelta(days=due_in_days)).isoformat() if due_in_days else None
        self.created_at = (now - timedelta(days=created_days_ago)).isoformat()
        self.story_points = story_points
        self.dependents = dependents or []


@pytest.fixture
def ranker():
    return RankerV2(ScoringConfig())


@pytest.fixture
def tasks():
    return [
        FakeTask(1, "critical", "todo", due_in_days=1, story_points=3),
        FakeTask(2, "medium", "todo", due_in_days=14, story_points=8),
        FakeTask(3, "low", "done", story_points=2),
        FakeTask(4, "high", "in-progress", due_in_days=3, story_points=5, dependents=[1, 2]),
    ]


def test_score_basic(ranker, tasks):
    score = ranker.score(tasks[0])
    assert score > 0


def test_score_done_is_zero(ranker, tasks):
    assert ranker.score(tasks[2]) == 0.0


def test_score_critical_higher(ranker, tasks):
    assert ranker.score(tasks[0]) > ranker.score(tasks[1])


def test_score_breakdown(ranker, tasks):
    breakdown = ranker.score_breakdown(tasks[0])
    assert "priority" in breakdown
    assert "urgency" in breakdown
    assert "total" in breakdown


def test_rank(ranker, tasks):
    ranked = ranker.rank(tasks)
    assert len(ranked) == 4
    assert ranked[0]["score"] >= ranked[1]["score"]


def test_rank_order(ranker, tasks):
    ranked = ranker.rank(tasks)
    ids = [r["id"] for r in ranked]
    assert ids[0] == 1
    assert ids[-1] == 3


def test_top_n(ranker, tasks):
    top = ranker.top_n(tasks, n=2)
    assert len(top) == 2


def test_bottom_n(ranker, tasks):
    bottom = ranker.bottom_n(tasks, n=2)
    assert len(bottom) == 2
    assert bottom[-1]["score"] == 0.0


def test_custom_factor(ranker, tasks):
    ranker.add_custom_factor("tag_score", lambda t: 50, weight=0.1)
    score = ranker.score(tasks[0])
    assert score > 0


def test_set_weights(ranker):
    ranker.set_weights(priority_weight=0.5)
    assert ranker.config.priority_weight == 0.5


def test_set_config(ranker):
    new_config = ScoringConfig(priority_weight=0.5)
    ranker.set_config(new_config)
    assert ranker.config.priority_weight == 0.5


def test_config_total_weight():
    config = ScoringConfig()
    assert config.total_weight == pytest.approx(1.0, abs=0.01)


def test_rank_tasks_helper(tasks):
    ranked = rank_tasks(tasks)
    assert len(ranked) == 4


def test_ranking_report(ranker, tasks):
    report = ranking_report(ranker, tasks)
    assert report["total_tasks"] == 4
    assert "top_3" in report
    assert "weights" in report


def test_default_ranker():
    r = default_ranker()
    assert r.config.priority_weight == 0.35


def test_score_with_urgency():
    ranker = RankerV2(ScoringConfig(urgency_weight=0.5))
    overdue_task = FakeTask(1, "medium", "todo", due_in_days=-2)
    breakdown = ranker.score_breakdown(overdue_task)
    assert breakdown["urgency"] == 100
