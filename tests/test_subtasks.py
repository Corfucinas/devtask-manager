"""Tests for subtask hierarchy."""
import pytest
from src.subtasks import add_subtask, get_subtasks, get_descendants, is_blocked_by, flatten_hierarchy


class FakeStatus:
    def __init__(self, value):
        self.value = value


class FakeTask:
    def __init__(self, id, title="task", status="todo"):
        self.id = id
        self.title = title
        self.status = FakeStatus(status)
        self.subtasks = None


@pytest.fixture
def tasks():
    parent = FakeTask(1, "Parent")
    child1 = FakeTask(2, "Child 1")
    child2 = FakeTask(3, "Child 2")
    grandchild = FakeTask(4, "Grandchild")
    add_subtask(parent, 2)
    add_subtask(parent, 3)
    add_subtask(child1, 4)
    return [parent, child1, child2, grandchild]


def test_add_subtask():
    parent = FakeTask(1)
    add_subtask(parent, 5)
    assert parent.subtasks == [5]
    add_subtask(parent, 5)
    assert parent.subtasks == [5]


def test_get_subtasks(tasks):
    parent = tasks[0]
    children = get_subtasks(parent, tasks)
    assert len(children) == 2
    assert {c.id for c in children} == {2, 3}


def test_get_descendants(tasks):
    parent = tasks[0]
    desc = get_descendants(parent, tasks)
    ids = {t.id for t in desc}
    assert ids == {2, 3, 4}


def test_is_blocked_by(tasks):
    child = tasks[1]
    assert is_blocked_by(child, tasks) is True
    tasks[0].status = FakeStatus("done")
    assert is_blocked_by(child, tasks) is False


def test_flatten_hierarchy(tasks):
    h = flatten_hierarchy(tasks)
    assert h == {1: 2, 2: 1}
