"""Tests for analytics engine."""
import pytest
from datetime import datetime, timezone, timedelta
from src.analytics import (
    throughput_analysis, bottleneck_analysis, trend_analysis,
    cycle_time_distribution, assignee_workload_analysis, insights_report,
)


class FakeStatus:
    def __init__(self, value):
        self.value = value


class FakePriority:
    def __init__(self, value):
        self.value = value


class FakeTask:
    def __init__(self, id, status="todo", priority="medium", assignee=None,
                 created_days_ago=1, completed_days_ago=None, started_days_ago=None,
                 blockers=None):
        now = datetime.now(timezone.utc)
        self.id = id
        self.status = FakeStatus(status)
        self.priority = FakePriority(priority)
        self.assignee = assignee
        self.created_at = (now - timedelta(days=created_days_ago)).isoformat()
        if completed_days_ago is not None:
            self.completed_at = (now - timedelta(days=completed_days_ago)).isoformat()
        else:
            self.completed_at = None
        if started_days_ago is not None:
            self.started_at = (now - timedelta(days=started_days_ago)).isoformat()
        else:
            self.started_at = None
        self.blockers = blockers


@pytest.fixture
def tasks():
    return [
        FakeTask(1, "done", "high", "alice", created_days_ago=5, completed_days_ago=1, started_days_ago=3),
        FakeTask(2, "done", "medium", "bob", created_days_ago=4, completed_days_ago=2, started_days_ago=3),
        FakeTask(3, "in-progress", "medium", "alice", created_days_ago=3),
        FakeTask(4, "todo", "low", None, created_days_ago=1),
        FakeTask(5, "in-progress", "high", "charlie", created_days_ago=2),
    ]


def test_throughput_analysis(tasks):
    data = throughput_analysis(tasks, period="daily", days=7)
    assert len(data) == 7
    assert all("created" in d and "completed" in d for d in data)


def test_bottleneck_analysis(tasks):
    result = bottleneck_analysis(tasks)
    assert "status_distribution" in result
    assert "bottlenecks" in result
    assert isinstance(result["bottlenecks"], list)


def test_trend_analysis(tasks):
    result = trend_analysis(tasks, metric="completion", days=7)
    assert result["trend"] in ("increasing", "decreasing", "stable")
    assert "values" in result


def test_cycle_time_distribution(tasks):
    result = cycle_time_distribution(tasks)
    assert result["count"] == 2
    assert result["average"] > 0


def test_cycle_time_distribution_empty():
    result = cycle_time_distribution([])
    assert result["count"] == 0


def test_assignee_workload_analysis(tasks):
    result = assignee_workload_analysis(tasks)
    assert result["assignee_count"] == 3
    assert "alice" in result["assignees"]


def test_assignee_workload_unassigned(tasks):
    result = assignee_workload_analysis(tasks)
    assert result["unassigned_count"] == 1


def test_insights_report(tasks):
    report = insights_report(tasks)
    assert report["total_tasks"] == 5
    assert "completion_rate" in report
    assert "insights" in report


def test_insights_report_empty():
    report = insights_report([])
    assert report["total_tasks"] == 0
    assert report["completion_rate"] == 0.0
