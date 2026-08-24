"""Tests for metrics dashboard."""
import pytest
from src.task_metrics_v3 import (
    MetricsDashboard, MetricValue, dashboard_report, default_dashboard,
)


@pytest.fixture
def dashboard():
    d = MetricsDashboard()
    d.record("open_tasks", 10)
    d.record("open_tasks", 8)
    d.record("open_tasks", 5)
    d.record("completed", 3)
    return d


def test_record():
    d = MetricsDashboard()
    mv = d.record("test", 42)
    assert mv.name == "test"
    assert mv.value == 42


def test_get_latest(dashboard):
    assert dashboard.get_latest("open_tasks") == 5
    assert dashboard.get_latest("completed") == 3
    assert dashboard.get_latest("nonexistent") is None


def test_get_history(dashboard):
    history = dashboard.get_history("open_tasks")
    assert len(history) == 3
    assert history[-1].value == 5


def test_get_history_limit(dashboard):
    history = dashboard.get_history("open_tasks", limit=2)
    assert len(history) == 2
    assert history[0].value == 8


def test_all_metrics(dashboard):
    metrics = dashboard.all_metrics()
    assert "open_tasks" in metrics
    assert "completed" in metrics


def test_metric_count(dashboard):
    assert dashboard.metric_count() == 2


def test_total_data_points(dashboard):
    assert dashboard.total_data_points() == 4


def test_average(dashboard):
    avg = dashboard.average("open_tasks")
    assert avg == pytest.approx(7.67, abs=0.1)


def test_average_empty():
    d = MetricsDashboard()
    assert d.average("nonexistent") == 0.0


def test_min_value(dashboard):
    assert dashboard.min_value("open_tasks") == 5


def test_max_value(dashboard):
    assert dashboard.max_value("open_tasks") == 10


def test_snapshot(dashboard):
    snap = dashboard.snapshot()
    assert snap["open_tasks"] == 5
    assert snap["completed"] == 3


def test_clear(dashboard):
    dashboard.clear()
    assert dashboard.metric_count() == 0


def test_remove(dashboard):
    assert dashboard.remove("open_tasks") is True
    assert dashboard.get_latest("open_tasks") is None
    assert dashboard.remove("nonexistent") is False


def test_dashboard_report(dashboard):
    report = dashboard_report(dashboard)
    assert report["metric_count"] == 2
    assert "snapshot" in report
    assert "averages" in report
    assert "ranges" in report


def test_default_dashboard():
    d = default_dashboard()
    assert d.metric_count() == 5
    assert d.get_latest("open_tasks") == 0
