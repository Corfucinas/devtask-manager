"""Tests for task comparator."""
import pytest
from src.task_comparator import (
    FieldDiff, compare_tasks, similarity_score, changed_fields,
    unchanged_fields, merge_tasks, comparison_report, diff_summary,
)


class FakePriority:
    def __init__(self, value): self.value = value
class FakeStatus:
    def __init__(self, value): self.value = value
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
def tasks():
    return [FakeTask(1, "Bug", priority="high", tags=["bug"]),
            FakeTask(2, "Bug", priority="low", tags=["bug"])]


def test_field_diff_change_type_unchanged():
    d = FieldDiff(field="x", value_a=1, value_b=1, is_different=False)
    assert d.change_type == "unchanged"


def test_field_diff_change_type_modified():
    d = FieldDiff(field="x", value_a=1, value_b=2, is_different=True)
    assert d.change_type == "modified"


def test_field_diff_change_type_added():
    d = FieldDiff(field="x", value_a=None, value_b=2, is_different=True)
    assert d.change_type == "added"


def test_field_diff_change_type_removed():
    d = FieldDiff(field="x", value_a=1, value_b=None, is_different=True)
    assert d.change_type == "removed"


def test_compare_tasks(tasks):
    diffs = compare_tasks(tasks[0], tasks[1])
    assert len(diffs) == 8
    assert all(d.field in ["id", "title", "description", "priority", "status",
                           "tags", "assignee", "due_date"] for d in diffs)


def test_compare_identical():
    a = FakeTask(1, "Same")
    b = FakeTask(1, "Same")
    diffs = compare_tasks(a, b)
    assert all(not d.is_different for d in diffs)


def test_similarity_identical():
    a = FakeTask(1, "Same")
    b = FakeTask(1, "Same")
    assert similarity_score(a, b) == 1.0


def test_similarity_different(tasks):
    score = similarity_score(tasks[0], tasks[1])
    assert 0 <= score <= 1


def test_changed_fields(tasks):
    changed = changed_fields(tasks[0], tasks[1])
    assert "priority" in changed
    assert "id" in changed


def test_unchanged_fields(tasks):
    unchanged = unchanged_fields(tasks[0], tasks[1])
    assert "title" in unchanged
    assert "tags" in unchanged


def test_merge_b_wins(tasks):
    merged = merge_tasks(tasks[0], tasks[1], "b_wins")
    assert merged["priority"] == "low"
    assert merged["_merge_strategy"] == "b_wins"


def test_merge_a_wins(tasks):
    merged = merge_tasks(tasks[0], tasks[1], "a_wins")
    assert merged["priority"] == "high"


def test_merge_prefer_non_none():
    a = FakeTask(1, assignee=None)
    b = FakeTask(2, assignee="alice")
    merged = merge_tasks(a, b, "prefer_non_none")
    assert merged["assignee"] == "alice"


def test_merge_lists():
    a = FakeTask(1, tags=["bug", "auth"])
    b = FakeTask(2, tags=["bug", "ui"])
    merged = merge_tasks(a, b, "merge_lists")
    assert set(merged["tags"]) == {"bug", "auth", "ui"}


def test_comparison_report(tasks):
    report = comparison_report(tasks)
    assert report["total_tasks"] == 2
    assert report["comparisons"] == 1
    assert "average_similarity" in report
    assert "most_similar" in report


def test_comparison_report_single():
    report = comparison_report([FakeTask(1)])
    assert report["comparisons"] == 0


def test_diff_summary(tasks):
    summary = diff_summary(tasks[0], tasks[1])
    assert summary["total_fields"] == 8
    assert summary["changed"] > 0
    assert summary["unchanged"] > 0
    assert "similarity" in summary
    assert "changes" in summary
