"""Tests for multi-factor task scorer."""
import pytest
from datetime import datetime, timezone, timedelta
from src.task_scorer import ScoringFactor, TaskScorer, default_scorer


class FakePriority:
    def __init__(self, value): self.value = value
class FakeStatus:
    def __init__(self, value): self.value = value
class FakeTask:
    def __init__(self, id, priority="medium", status="todo", due_in_days=None,
                 created_days_ago=1, story_points=5):
        now = datetime.now(timezone.utc)
        self.id = id
        self.priority = FakePriority(priority)
        self.status = FakeStatus(status)
        self.due_date = (now + timedelta(days=due_in_days)).isoformat() if due_in_days else None
        self.created_at = (now - timedelta(days=created_days_ago)).isoformat()
        self.story_points = story_points


@pytest.fixture
def scorer():
    s = TaskScorer()
    s.add_factor("priority", 0.5, lambda t: {"critical": 100, "high": 75, "medium": 50, "low": 25}.get(t.priority.value, 50))
    s.add_factor("age", 0.5, lambda t: min(100, 10 * getattr(t, "story_points", 1)))
    return s


@pytest.fixture
def tasks():
    return [
        FakeTask(1, "critical", "todo", due_in_days=1, story_points=3),
        FakeTask(2, "medium", "todo", due_in_days=14, story_points=8),
        FakeTask(3, "low", "done", story_points=2),
        FakeTask(4, "high", "in-progress", due_in_days=3, story_points=5),
    ]


def test_add_factor():
    s = TaskScorer()
    f = s.add_factor("test", 0.5, lambda t: 50)
    assert f.name == "test"
    assert f.weight == 0.5


def test_remove_factor(scorer):
    assert scorer.remove_factor("priority") is True
    assert scorer.get_factor("priority") is None


def test_count(scorer):
    assert scorer.count() == 2


def test_total_weight(scorer):
    assert scorer.total_weight() == 1.0


def test_normalize_weights():
    s = TaskScorer()
    s.add_factor("a", 2, lambda t: 50)
    s.add_factor("b", 3, lambda t: 50)
    s.normalize_weights()
    assert s.total_weight() == pytest.approx(1.0, abs=0.01)


def test_score_basic(scorer, tasks):
    s = scorer.score(tasks[0])
    assert s > 0


def test_score_done_is_zero(scorer, tasks):
    assert scorer.score(tasks[2]) == 0.0


def test_score_critical_higher(scorer, tasks):
    assert scorer.score(tasks[0]) > scorer.score(tasks[1])


def test_score_breakdown(scorer, tasks):
    breakdown = scorer.score_breakdown(tasks[0])
    assert "priority" in breakdown
    assert "age" in breakdown
    assert "total" in breakdown


def test_rank_tasks(scorer, tasks):
    ranked = scorer.rank_tasks(tasks)
    assert len(ranked) == 4
    assert ranked[0]["score"] >= ranked[1]["score"]


def test_rank_tasks_order(scorer, tasks):
    ranked = scorer.rank_tasks(tasks)
    ids = [r["id"] for r in ranked]
    assert ids[0] == 1  # critical first
    assert ids[-1] == 3  # done last


def test_top_n(scorer, tasks):
    top = scorer.top_n(tasks, n=2)
    assert len(top) == 2


def test_top_n_more_than_available(scorer, tasks):
    top = scorer.top_n(tasks, n=10)
    assert len(top) == 4


def test_empty_scorer():
    s = TaskScorer()
    task = FakeTask(1)
    assert s.score(task) == 0.0


def test_default_scorer():
    s = default_scorer()
    assert s.count() == 4
    assert s.total_weight() == pytest.approx(1.0, abs=0.01)


def test_default_scorer_score():
    s = default_scorer()
    task = FakeTask(1, "critical", "todo", due_in_days=1, story_points=3)
    assert s.score(task) > 0


def test_scoring_factor_clamp():
    f = ScoringFactor(name="test", weight=1.0, calculator=lambda t: 200, max_score=100)
    assert f.calculate(FakeTask(1)) == 100
