"""Tests for extended metrics."""
import pytest
from src.metrics_v2 import (
    MetricDefinition, MetricsCollector, metrics_report, default_metrics,
)


@pytest.fixture
def collector():
    c = MetricsCollector()
    c.define("tasks_created", "counter", aggregation="sum")
    c.define("open_tasks", "gauge", aggregation="last")
    return c


def test_define():
    c = MetricsCollector()
    d = c.define("test_metric", "gauge")
    assert d.id == 1
    assert d.name == "test_metric"


def test_get(collector):
    d = collector.get(1)
    assert d is not None
    assert d.name == "tasks_created"
    assert collector.get(999) is None


def test_find_by_name(collector):
    d = collector.find_by_name("open_tasks")
    assert d is not None
    assert collector.find_by_name("nonexistent") is None


def test_record(collector):
    p = collector.record(1, 5.0)
    assert p is not None
    assert p.value == 5.0
    assert p.metric_id == 1


def test_record_by_name(collector):
    p = collector.record_by_name("tasks_created", 3.0)
    assert p is not None
    assert p.value == 3.0


def test_record_invalid_metric(collector):
    assert collector.record(999, 1.0) is None


def test_points_for(collector):
    collector.record(1, 1.0)
    collector.record(1, 2.0)
    collector.record(2, 5.0)
    assert len(collector.points_for(1)) == 2
    assert len(collector.points_for(2)) == 1


def test_aggregate_sum(collector):
    collector.record(1, 1.0)
    collector.record(1, 2.0)
    collector.record(1, 3.0)
    assert collector.aggregate(1) == 6.0


def test_aggregate_last(collector):
    collector.record(2, 10.0)
    collector.record(2, 20.0)
    assert collector.aggregate(2) == 20.0


def test_aggregate_empty(collector):
    assert collector.aggregate(1) == 0.0


def test_aggregate_all(collector):
    collector.record(1, 5.0)
    collector.record(2, 10.0)
    agg = collector.aggregate_all()
    assert agg["tasks_created"] == 5.0
    assert agg["open_tasks"] == 10.0


def test_count(collector):
    assert collector.count() == 2


def test_point_count(collector):
    collector.record(1, 1.0)
    assert collector.point_count() == 1


def test_clear(collector):
    collector.record(1, 1.0)
    collector.clear()
    assert collector.point_count() == 0


def test_metrics_report(collector):
    collector.record(1, 5.0)
    r = metrics_report(collector)
    assert r["metric_count"] == 2
    assert r["total_points"] == 1
    assert "aggregations" in r
    assert "definitions" in r


def test_default_metrics():
    c = default_metrics()
    assert c.count() == 5
    assert c.find_by_name("tasks_created") is not None
    assert c.find_by_name("velocity") is not None
