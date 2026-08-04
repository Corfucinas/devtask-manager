"""Tests for task diff comparison."""
import pytest
from src.diff import (
    TaskDiff, diff_tasks, apply_diff, format_diff,
    diff_summary, has_changes, revert_diff, merge_diffs,
)


class FakeStatus:
    def __init__(self, value):
        self.value = value


class FakePriority:
    def __init__(self, value):
        self.value = value


class FakeTask:
    def __init__(self, id=1, title="Task", description="Desc", priority="medium",
                 status="todo", tags=None, assignee=None, due_date=None):
        self.id = id
        self.title = title
        self.description = description
        self.priority = FakePriority(priority)
        self.status = FakeStatus(status)
        self.tags = tags or []
        self.assignee = assignee
        self.due_date = due_date


@pytest.fixture
def old_task():
    return FakeTask(1, "Original Title", "Original desc", "medium", "todo", ["bug"])


@pytest.fixture
def new_task():
    return FakeTask(1, "Updated Title", "Original desc", "high", "in-progress", ["bug", "urgent"])


def test_task_diff_added():
    d = TaskDiff(field="x", old_value=None, new_value=5, change_type="added")
    assert d.is_added is True


def test_task_diff_removed():
    d = TaskDiff(field="x", old_value=5, new_value=None, change_type="removed")
    assert d.is_removed is True


def test_task_diff_modified():
    d = TaskDiff(field="x", old_value=1, new_value=2, change_type="modified")
    assert d.is_modified is True
    assert d.changed is True


def test_diff_tasks(old_task, new_task):
    diffs = diff_tasks(old_task, new_task)
    fields = {d.field for d in diffs}
    assert "title" in fields
    assert "priority" in fields


def test_diff_tasks_no_changes(old_task):
    new = FakeTask(1, "Original Title", "Original desc", "medium", "todo", ["bug"])
    assert len(diff_tasks(old_task, new)) == 0


def test_apply_diff(old_task):
    diffs = [TaskDiff(field="title", old_value="Old", new_value="New", change_type="modified")]
    apply_diff(old_task, diffs)
    assert old_task.title == "New"


def test_apply_diff_status(old_task):
    diffs = [TaskDiff(field="status", old_value="todo", new_value="done", change_type="modified")]
    apply_diff(old_task, diffs)
    assert old_task.status.value == "done"


def test_format_diff(old_task, new_task):
    diffs = diff_tasks(old_task, new_task)
    formatted = format_diff(diffs)
    assert "~" in formatted
    assert "title" in formatted


def test_diff_summary(old_task, new_task):
    diffs = diff_tasks(old_task, new_task)
    summary = diff_summary(diffs)
    assert summary["total_changes"] > 0
    assert "title" in summary["fields_changed"]


def test_has_changes(old_task, new_task):
    diffs = diff_tasks(old_task, new_task)
    assert has_changes(diffs) is True


def test_revert_diff(old_task, new_task):
    diffs = diff_tasks(old_task, new_task)
    reverted = revert_diff(diffs)
    for orig, rev in zip(diffs, reverted):
        assert rev.old_value == orig.new_value
        assert rev.new_value == orig.old_value


def test_merge_diffs():
    diffs_a = [TaskDiff(field="title", old_value="A", new_value="B")]
    diffs_b = [TaskDiff(field="status", old_value="todo", new_value="done")]
    merged = merge_diffs(diffs_a, diffs_b)
    assert len(merged) == 2


def test_merge_diffs_conflict():
    diffs_a = [TaskDiff(field="title", old_value="A", new_value="B")]
    diffs_b = [TaskDiff(field="title", old_value="B", new_value="C")]
    merged = merge_diffs(diffs_a, diffs_b)
    assert len(merged) == 1
    assert merged[0].new_value == "C"
