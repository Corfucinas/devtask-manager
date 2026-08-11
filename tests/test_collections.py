"""Tests for task collections."""
import pytest
from src.collections import (
    Collection, CollectionManager, add_to_collection, remove_from_collection,
    tasks_in_collection, auto_populate, collection_summary,
    merge_collections, intersect_collections, diff_collections,
    default_collections,
)


class FakeStatus:
    def __init__(self, value):
        self.value = value


class FakePriority:
    def __init__(self, value):
        self.value = value


class FakeTask:
    def __init__(self, id, priority="medium", status="todo", due_date=None):
        self.id = id
        self.priority = FakePriority(priority)
        self.status = FakeStatus(status)
        self.due_date = due_date


@pytest.fixture
def manager():
    m = CollectionManager()
    m.create("Bug Fix", "Bug tasks", color="#d73a4a")
    m.create("Feature", "Feature tasks", color="#a2eeef")
    return m


@pytest.fixture
def tasks():
    return [FakeTask(1, "high", "todo"), FakeTask(2, "critical", "in-progress"),
            FakeTask(3, "medium", "done"), FakeTask(4, "low", "todo")]


def test_collection_create():
    c = Collection(id=1, name="Test")
    assert c.id == 1
    assert c.count() == 0


def test_collection_includes():
    c = Collection(id=1, name="Test", task_ids=[1, 2, 3])
    assert c.includes(1) is True
    assert c.includes(99) is False


def test_manager_create(manager):
    assert manager.count() == 2


def test_manager_get(manager):
    assert manager.get(1) is not None
    assert manager.get(1).name == "Bug Fix"
    assert manager.get(999) is None


def test_manager_find_by_name(manager):
    assert manager.find_by_name("Bug Fix") is not None
    assert manager.find_by_name("BUG FIX") is not None


def test_manager_remove(manager):
    assert manager.remove(1) is True
    assert manager.count() == 1


def test_add_to_collection():
    c = Collection(id=1, name="Test")
    assert add_to_collection(c, 1) is True
    assert add_to_collection(c, 1) is False


def test_remove_from_collection():
    c = Collection(id=1, name="Test", task_ids=[1, 2])
    assert remove_from_collection(c, 1) is True
    assert remove_from_collection(c, 99) is False


def test_tasks_in_collection(tasks):
    c = Collection(id=1, name="Test", task_ids=[1, 3])
    result = tasks_in_collection(c, tasks)
    assert len(result) == 2


def test_auto_populate(tasks):
    def is_high(task, context=None):
        p = task.priority.value if hasattr(task.priority, "value") else task.priority
        return p in ("high", "critical")
    c = Collection(id=1, name="High", filter_fn=is_high)
    count = auto_populate(c, tasks)
    assert count == 2


def test_collection_summary(manager, tasks):
    c = manager.get(1)
    add_to_collection(c, 1)
    add_to_collection(c, 3)
    summary = collection_summary(manager, tasks)
    assert len(summary) == 2
    assert summary[0]["count"] == 2


def test_merge_collections():
    a = Collection(id=1, name="A", task_ids=[1, 2, 3])
    b = Collection(id=2, name="B", task_ids=[3, 4, 5])
    merge_collections(a, b)
    assert a.count() == 5


def test_intersect_collections():
    a = Collection(id=1, name="A", task_ids=[1, 2, 3])
    b = Collection(id=2, name="B", task_ids=[2, 3, 4])
    assert set(intersect_collections(a, b)) == {2, 3}


def test_diff_collections():
    a = Collection(id=1, name="A", task_ids=[1, 2, 3])
    b = Collection(id=2, name="B", task_ids=[2, 3, 4])
    assert set(diff_collections(a, b)) == {1}


def test_default_collections():
    m = default_collections()
    assert m.count() == 3
    assert m.find_by_name("High Priority") is not None
    assert m.find_by_name("Overdue") is not None
