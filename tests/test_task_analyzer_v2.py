"""Tests for task analyzer v2."""
import pytest
from datetime import datetime, timezone, timedelta
from src.task_analyzer_v2 import (
    Insight, TaskAnalyzerV2, insight_report, trend_summary,
)


class FakePriority:
    def __init__(self, value): self.value = value
class FakeStatus:
    def __init__(self, value): self.value = value
class FakeBlocker:
    def __init__(self, status="active"): self.status = status
class FakeTask:
    def __init__(self, id, priority="medium", status="todo", due_in_days=None,
                 assignee=None, completed_days_ago=None, blockers=None):
        now = datetime.now(timezone.utc)
        self.id = id
        self.priority = FakePriority(priority)
        self.status = FakeStatus(status)
        self.due_date = (now + timedelta(days=due_in_days)).isoformat() if due_in_days else None
        self.assignee = assignee
        if completed_days_ago is not None:
            self.completed_at = (now - timedelta(days=completed_days_ago)).isoformat()
        else:
            self.completed_at = None
        self.blockers = blockers


@pytest.fixture
def tasks():
    return [
        FakeTask(1, "high", "todo", due_in_days=-1, assignee="alice"),
        FakeTask(2, "medium", "in-progress", assignee="bob"),
        FakeTask(3, "low", "done", assignee="alice", completed_days_ago=1),
        FakeTask(4, "critical", "todo", assignee=None),
    ]


def test_analyze_basic(tasks):
    result = TaskAnalyzerV2().analyze(tasks)
    assert result["total_tasks"] == 4
    assert result["done"] == 1
    assert result["open"] == 3


def test_analyze_overdue(tasks):
    result = TaskAnalyzerV2().analyze(tasks)
    assert result["overdue"] == 1


def test_analyze_unassigned(tasks):
    result = TaskAnalyzerV2().analyze(tasks)
    assert result["unassigned"] == 1


def test_analyze_blocked():
    tasks = [FakeTask(1, blockers=[FakeBlocker()]), FakeTask(2, blockers=[])]
    result = TaskAnalyzerV2().analyze(tasks)
    assert result["blocked"] == 1


def test_analyze_status_distribution(tasks):
    result = TaskAnalyzerV2().analyze(tasks)
    assert "todo" in result["status_distribution"]
    assert "done" in result["status_distribution"]


def test_analyze_priority_distribution(tasks):
    result = TaskAnalyzerV2().analyze(tasks)
    assert "critical" in result["priority_distribution"]


def test_analyze_insights_low_completion():
    tasks = [FakeTask(i, status="todo") for i in range(10)]
    result = TaskAnalyzerV2().analyze(tasks)
    assert result["insight_count"] > 0


def test_analyze_insights_all_done():
    tasks = [FakeTask(i, status="done", completed_days_ago=1) for i in range(5)]
    result = TaskAnalyzerV2().analyze(tasks)
    assert result["open"] == 0
    assert any("completed" in i["message"].lower() for i in result["insights"])


def test_analyze_critical_tasks():
    tasks = [FakeTask(i, "critical", "todo") for i in range(5)]
    result = TaskAnalyzerV2().analyze(tasks)
    assert any(i["severity"] in ("critical", "error") for i in result["insights"])


def test_critical_insights():
    tasks = [FakeTask(1, "critical", "todo"), FakeTask(2, "critical", "todo")]
    analyzer = TaskAnalyzerV2()
    analyzer.analyze(tasks)
    critical = analyzer.critical_insights()
    assert len(critical) >= 1


def test_health_trend():
    tasks = [
        FakeTask(1, "medium", "done", completed_days_ago=0),
        FakeTask(2, "medium", "done", completed_days_ago=1),
    ]
    analyzer = TaskAnalyzerV2()
    trend = analyzer.health_trend(tasks, days=7)
    assert len(trend) == 7
    assert trend[-1]["completed"] == 1


def test_trend_summary_improving():
    trend = [{"day": f"2026-01-{i:02d}", "completed": 5 if i > 3 else 1}
             for i in range(1, 8)]
    assert trend_summary(trend) == "improving"


def test_trend_summary_stable():
    trend = [{"day": f"2026-01-{i:02d}", "completed": 5} for i in range(1, 8)]
    assert trend_summary(trend) == "stable"


def test_trend_summary_empty():
    assert trend_summary([]) == "No data"


def test_insight_report(tasks):
    report = insight_report(tasks)
    assert "analysis" in report
    assert "trend" in report
    assert "critical_insights" in report


def test_insight_data():
    insight = Insight(type="risk", message="Test", severity="error", data={"count": 5})
    assert insight.data["count"] == 5


def test_analyze_empty():
    result = TaskAnalyzerV2().analyze([])
    assert result["total_tasks"] == 0
