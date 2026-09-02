"""Tests for task aggregator."""
import pytest
from src.task_aggregator import (
    TaskSource, TaskAggregator, aggregation_report, default_aggregator,
)


class FakeTask:
    def __init__(self, id, title="Task"):
        self.id = id
        self.title = title


@pytest.fixture
def aggregator():
    a = TaskAggregator()
    a.add_source("Source A", "https://api.a.com")
    a.add_source("Source B", "https://api.b.com")
    return a


@pytest.fixture
def tasks():
    return [FakeTask(1, "Task 1"), FakeTask(2, "Task 2"), FakeTask(3, "Task 3")]


def test_add_source():
    agg = TaskAggregator()
    src = agg.add_source("Test", "https://test.com")
    assert src.id == 1
    assert src.name == "Test"


def test_remove_source(aggregator):
    assert aggregator.remove_source(1) is True
    assert aggregator.get_source(1) is None
    assert aggregator.remove_source(999) is False


def test_get_source(aggregator):
    s = aggregator.get_source(1)
    assert s is not None
    assert s.name == "Source A"


def test_all_sources(aggregator):
    assert len(aggregator.all_sources()) == 2


def test_enabled_sources(aggregator):
    assert len(aggregator.enabled_sources()) == 2


def test_source_count(aggregator):
    assert aggregator.source_count() == 2


def test_register_source_data(aggregator, tasks):
    count = aggregator.register_source_data(1, tasks)
    assert count == 3
    assert aggregator.get_source(1).task_count == 3
    assert aggregator.get_source(1).last_sync is not None


def test_aggregate(aggregator, tasks):
    aggregator.register_source_data(1, tasks)
    assert aggregator.aggregated_count() == 3


def test_clear_aggregated(aggregator, tasks):
    aggregator.register_source_data(1, tasks)
    aggregator.clear_aggregated()
    assert aggregator.aggregated_count() == 0


def test_deduplicate():
    agg = TaskAggregator()
    tasks = [FakeTask(1, "A"), FakeTask(1, "A"), FakeTask(2, "B")]
    agg.register_source_data(1, tasks)
    removed = agg.deduplicate()
    assert removed == 1
    assert agg.aggregated_count() == 2


def test_merge():
    agg1 = TaskAggregator()
    agg1.register_source_data(1, [FakeTask(1)])
    agg2 = TaskAggregator()
    agg2.register_source_data(2, [FakeTask(2)])
    merged = TaskAggregator()
    total = merged.merge(agg1, agg2)
    assert total == 2
    assert merged.aggregated_count() == 2


def test_aggregation_report(aggregator, tasks):
    aggregator.register_source_data(1, tasks)
    report = aggregation_report(aggregator)
    assert report["total_sources"] == 2
    assert report["total_tasks"] == 3
    assert "by_source" in report


def test_default_aggregator():
    agg = default_aggregator()
    assert agg.source_count() == 2
