"""Tests for task merger."""
import pytest
from src.task_merger import TaskMerger, MergeResult, merge_report, default_merger


class FakeTask:
    def __init__(self, id, title="Task", source=None):
        self.id = id
        self.title = title
        if source:
            self._source = source


@pytest.fixture
def merger():
    return TaskMerger(dedup_key="id")


@pytest.fixture
def list_a():
    return [FakeTask(1, "A"), FakeTask(2, "B")]


@pytest.fixture
def list_b():
    return [FakeTask(2, "B"), FakeTask(3, "C")]


def test_merge_basic(list_a, list_b):
    merged = TaskMerger().merge(list_a, list_b)
    assert len(merged) == 3  # task 2 is dedup'd


def test_merge_no_overlap():
    m = TaskMerger()
    result = m.merge([FakeTask(1)], [FakeTask(2)])
    assert len(result) == 2


def test_merge_empty():
    m = TaskMerger()
    result = m.merge([])
    assert result == []


def test_append():
    m = TaskMerger()
    m.merge([FakeTask(1)])
    m.append([FakeTask(2), FakeTask(1)])  # 1 is dup
    assert m.merged_count() == 2


def test_dedup_key_change():
    m = TaskMerger()
    m.set_dedup_key("title")
    result = m.merge([FakeTask(1, "Same"), FakeTask(2, "Same")])
    assert len(result) == 1


def test_merged_count(list_a, list_b):
    m = TaskMerger()
    m.merge(list_a, list_b)
    assert m.merged_count() == 3


def test_clear(list_a):
    m = TaskMerger()
    m.merge(list_a)
    m.clear()
    assert m.merged_count() == 0


def test_find_duplicates():
    tasks = [FakeTask(1), FakeTask(1), FakeTask(2)]
    m = TaskMerger()
    dups = m.find_duplicates(tasks)
    assert len(dups) == 1


def test_deduplicate():
    tasks = [FakeTask(1), FakeTask(1), FakeTask(2)]
    m = TaskMerger()
    result = m.deduplicate(tasks)
    assert len(result) == 2


def test_count_by_source():
    tasks = [FakeTask(1, source="A"), FakeTask(2, source="B"), FakeTask(3, source="A")]
    m = TaskMerger()
    counts = m.count_by_source(tasks)
    assert counts["A"] == 2
    assert counts["B"] == 1


def test_merge_result():
    r = MergeResult(total_input=5, total_output=3, duplicates_removed=2, sources_merged=2)
    assert r.duplicates_removed == 2


def test_merge_report(list_a, list_b):
    m = TaskMerger()
    m.merge(list_a, list_b)
    report = merge_report(m)
    assert report["merged_count"] == 3
    assert report["sources_merged"] == 2


def test_default_merger():
    m = default_merger()
    assert m.dedup_key == "id"
