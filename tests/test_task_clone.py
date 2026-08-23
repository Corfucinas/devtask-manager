"""Tests for task cloning."""
import pytest
from src.task_clone import (
    clone_task, clone_with_modifications, clone_batch,
    clone_report, is_clone, diff_original_clone,
)


class FakePriority:
    def __init__(self, value): self.value = value
class FakeStatus:
    def __init__(self, value): self.value = value
class FakeTask:
    def __init__(self, id=1, title="Task", description="Desc", priority="medium",
                 status="todo", tags=None, assignee=None, created_at="2026-01-01T00:00:00+00:00",
                 updated_at="2026-01-01T00:00:00+00:00", completed_at=None):
        self.id = id
        self.title = title
        self.description = description
        self.priority = FakePriority(priority)
        self.status = FakeStatus(status)
        self.tags = tags or []
        self.assignee = assignee
        self.created_at = created_at
        self.updated_at = updated_at
        self.completed_at = completed_at


@pytest.fixture
def task():
    return FakeTask(1, title="Original Task", tags=["bug", "auth"], assignee="alice")


def test_clone_task(task):
    clone = clone_task(task, new_id=2)
    assert clone.id == 2
    assert clone.title == "Original Task"
    assert clone.tags == ["bug", "auth"]
    assert clone.assignee == "alice"


def test_clone_task_resets_dates(task):
    clone = clone_task(task, new_id=2)
    assert clone.created_at != "2026-01-01T00:00:00+00:00"
    assert clone.completed_at is None


def test_clone_with_modifications(task):
    clone = clone_with_modifications(task, new_id=2, title="Cloned Task", assignee="bob")
    assert clone.id == 2
    assert clone.title == "Cloned Task"
    assert clone.assignee == "bob"


def test_clone_batch():
    tasks = [FakeTask(1, title="A"), FakeTask(2, title="B"), FakeTask(3, title="C")]
    clones = clone_batch(tasks, id_offset=100)
    assert len(clones) == 3
    assert clones[0].id == 101
    assert clones[1].id == 102


def test_clone_report():
    originals = [FakeTask(1), FakeTask(2)]
    clones = [FakeTask(101), FakeTask(102)]
    report = clone_report(originals, clones)
    assert report["originals"] == 2
    assert report["clones"] == 2


def test_is_clone():
    original = FakeTask(1, title="Same")
    clone = FakeTask(2, title="Same")
    assert is_clone(original, clone) is True


def test_is_not_clone():
    original = FakeTask(1, title="A")
    other = FakeTask(2, title="B")
    assert is_clone(original, other) is False


def test_diff_original_clone():
    original = FakeTask(1, title="A", priority="medium", assignee="alice")
    clone = FakeTask(2, title="B", priority="high", assignee="bob")
    diffs = diff_original_clone(original, clone)
    assert "title" in diffs
    assert "priority" in diffs
    assert "assignee" in diffs


def test_diff_no_changes():
    original = FakeTask(1, title="Same", priority="medium")
    clone = FakeTask(2, title="Same", priority="medium")
    diffs = diff_original_clone(original, clone)
    assert diffs == {}


def test_clone_preserves_tags():
    task = FakeTask(1, tags=["a", "b", "c"])
    clone = clone_task(task, new_id=2)
    assert clone.tags == ["a", "b", "c"]
