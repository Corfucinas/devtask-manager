"""Tests for duplicate detection."""
import pytest
from src.duplicates import (
    title_similarity, tag_similarity, similarity_score,
    find_duplicates, merge_tasks, duplicate_report, auto_merge_duplicates,
)


class FakeStatus:
    def __init__(self, value):
        self.value = value


class FakePriority:
    def __init__(self, value):
        self.value = value


class FakeTask:
    def __init__(self, id, title, tags=None, priority="medium", status="todo",
                 description="", notes=None, subtasks=None):
        self.id = id
        self.title = title
        self.tags = tags or []
        self.priority = FakePriority(priority)
        self.status = FakeStatus(status)
        self.description = description
        self.notes = notes
        self.subtasks = subtasks or []


def test_title_similarity_identical():
    assert title_similarity("Fix login bug", "Fix login bug") == 1.0


def test_title_similarity_partial():
    score = title_similarity("Fix login bug", "Fix login error")
    assert 0 < score < 1.0


def test_title_similarity_none():
    assert title_similarity("", "test") == 0.0


def test_tag_similarity_identical():
    assert tag_similarity(["bug", "auth"], ["bug", "auth"]) == 1.0


def test_tag_similarity_empty():
    assert tag_similarity([], ["bug"]) == 0.0


def test_similarity_score_identical():
    a = FakeTask(1, "Fix login bug", ["bug", "auth"], "high", "todo")
    b = FakeTask(2, "Fix login bug", ["bug", "auth"], "high", "todo")
    assert similarity_score(a, b) == 1.0


def test_similarity_score_different():
    a = FakeTask(1, "Fix login bug", ["bug"], "high", "todo")
    b = FakeTask(2, "Add dark mode", ["feature"], "low", "done")
    assert similarity_score(a, b) < 0.3


def test_find_duplicates():
    tasks = [
        FakeTask(1, "Fix login bug", ["bug", "auth"], "high"),
        FakeTask(2, "Fix login bug", ["bug", "auth"], "high"),
        FakeTask(3, "Add dark mode", ["feature"], "low"),
    ]
    dupes = find_duplicates(tasks, threshold=0.7)
    assert len(dupes) == 1


def test_find_duplicates_none():
    tasks = [
        FakeTask(1, "Fix bug", ["bug"]),
        FakeTask(2, "Add feature", ["feature"]),
    ]
    assert find_duplicates(tasks, threshold=0.7) == []


def test_merge_tasks():
    primary = FakeTask(1, "Fix login bug", ["bug"], description="desc1")
    duplicate = FakeTask(2, "Fix login bug", ["auth"], description="desc2",
                         notes=["note1"], subtasks=[5, 6])
    result = merge_tasks(primary, duplicate)
    assert result["primary_id"] == 1
    assert "auth" in result["merged_tags"]
    assert len(result["merged_notes"]) == 1
    assert 5 in primary.subtasks


def test_merge_tasks_takes_description():
    primary = FakeTask(1, "Fix bug", description="")
    duplicate = FakeTask(2, "Fix bug", description="important info")
    result = merge_tasks(primary, duplicate)
    assert result.get("took_description") is True
    assert primary.description == "important info"


def test_duplicate_report():
    tasks = [
        FakeTask(1, "Fix login bug", ["bug"], "high"),
        FakeTask(2, "Fix login bug", ["bug"], "high"),
        FakeTask(3, "Add feature", ["feature"], "low"),
    ]
    report = duplicate_report(tasks, threshold=0.5)
    assert report["total_tasks"] == 3
    assert report["duplicate_pairs"] >= 1


def test_auto_merge_duplicates():
    tasks = [
        FakeTask(1, "Fix login bug", ["bug", "auth"], "high"),
        FakeTask(2, "Fix login bug", ["bug", "auth"], "high"),
        FakeTask(3, "Add feature", ["feature"], "low"),
    ]
    results = auto_merge_duplicates(tasks, threshold=0.85)
    assert len(results) == 1
    assert results[0]["similarity_score"] == 1.0
