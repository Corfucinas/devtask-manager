"""Tests for tag cloud generator."""
import pytest
from src.tag_cloud import (
    TagCloudItem, generate_tag_cloud, tag_cloud_report,
    filter_by_weight, co_occurrence_matrix, top_co_occurrences, tag_diversity,
)


class FakeTask:
    def __init__(self, id, tags=None):
        self.id = id
        self.tags = tags or []


@pytest.fixture
def tasks():
    return [
        FakeTask(1, ["bug", "auth", "urgent"]),
        FakeTask(2, ["bug", "ui"]),
        FakeTask(3, ["feature", "ui"]),
        FakeTask(4, ["bug", "auth"]),
        FakeTask(5, ["docs"]),
    ]


def test_tag_cloud_item_importance():
    item = TagCloudItem(name="bug", count=10, weight=0.8)
    assert item.importance == "high"


def test_generate_tag_cloud(tasks):
    cloud = generate_tag_cloud(tasks)
    assert len(cloud) == 5
    assert cloud[0].name == "bug"
    assert cloud[0].count == 3


def test_generate_tag_cloud_empty():
    cloud = generate_tag_cloud([])
    assert cloud == []


def test_generate_tag_cloud_min_count(tasks):
    cloud = generate_tag_cloud(tasks, min_count=2)
    assert all(item.count >= 2 for item in cloud)


def test_tag_cloud_report(tasks):
    report = tag_cloud_report(tasks)
    assert report["total_tags"] == 5
    assert report["total_occurrences"] == 9
    assert "most_common" in report
    assert "by_importance" in report


def test_tag_cloud_report_empty():
    report = tag_cloud_report([])
    assert report["total_tags"] == 0


def test_filter_by_weight(tasks):
    cloud = generate_tag_cloud(tasks)
    filtered = filter_by_weight(cloud, min_weight=0.5)
    assert all(item.weight >= 0.5 for item in filtered)


def test_co_occurrence_matrix(tasks):
    matrix = co_occurrence_matrix(tasks)
    assert "bug" in matrix
    assert matrix["bug"]["auth"] == 2


def test_top_co_occurrences(tasks):
    matrix = co_occurrence_matrix(tasks)
    pairs = top_co_occurrences(matrix, n=3)
    assert len(pairs) <= 3
    assert pairs[0]["count"] >= pairs[-1]["count"] if len(pairs) > 1 else True


def test_tag_diversity(tasks):
    d = tag_diversity(tasks)
    assert d > 0


def test_tag_diversity_empty():
    assert tag_diversity([]) == 0.0


def test_tag_diversity_single_tag():
    tasks = [FakeTask(1, ["bug"]), FakeTask(2, ["bug"])]
    d = tag_diversity(tasks)
    assert d == 0.0
