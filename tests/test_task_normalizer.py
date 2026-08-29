"""Tests for task normalizer."""
import pytest
from src.task_normalizer import (
    normalize_task, normalize_batch, normalization_report,
    NormalizerConfig, default_config,
)


class FakePriority:
    def __init__(self, value): self.value = value
class FakeStatus:
    def __init__(self, value): self.value = value
class FakeTask:
    def __init__(self, id=1, title="  Task  ", description="  Desc  ",
                 priority="URGENT", status="OPEN", tags=["Bug", "bug", "  auth  "],
                 assignee="  alice  "):
        self.id = id
        self.title = title
        self.description = description
        self.priority = FakePriority(priority)
        self.status = FakeStatus(status)
        self.tags = list(tags)
        self.assignee = assignee


def test_normalize_whitespace():
    task = FakeTask(title="  Spaced  Title  ")
    changes = normalize_task(task)
    assert "title" in changes
    assert task.title == "Spaced  Title"


def test_normalize_strip_html():
    task = FakeTask(description="<b>Bold</b> text")
    changes = normalize_task(task)
    assert "description" in changes
    assert "<" not in task.description


def test_normalize_tags_lowercase():
    task = FakeTask(tags=["Bug", "Feature", "bug"])
    changes = normalize_task(task)
    assert "tags" in changes
    assert "bug" in task.tags
    assert "feature" in task.tags
    assert task.tags.count("bug") == 1  # deduplicated


def test_normalize_tags_sorted():
    task = FakeTask(tags=["zebra", "alpha", "mango"])
    changes = normalize_task(task)
    assert task.tags == ["alpha", "mango", "zebra"]


def test_normalize_priority():
    task = FakeTask(priority="URGENT")
    changes = normalize_task(task)
    assert "priority" in changes
    assert task.priority.value == "critical"


def test_normalize_status():
    task = FakeTask(status="OPEN")
    changes = normalize_task(task)
    assert "status" in changes
    assert task.status.value == "todo"


def test_normalize_assignee():
    task = FakeTask(assignee="  alice  ")
    changes = normalize_task(task)
    assert "assignee" in changes
    assert task.assignee == "alice"


def test_normalize_no_changes():
    task = FakeTask(title="Clean", description="Clean", priority="medium",
                    status="todo", tags=["bug"], assignee="alice")
    changes = normalize_task(task)
    assert len(changes) == 0


def test_normalize_batch():
    tasks = [FakeTask(1), FakeTask(2)]
    results = normalize_batch(tasks)
    assert len(results) == 2
    assert "task_id" in results[0]
    assert "changes" in results[0]


def test_normalization_report():
    tasks = [FakeTask(1), FakeTask(2)]
    report = normalization_report(tasks)
    assert report["total_tasks"] == 2
    assert "changed_tasks" in report
    assert "by_field" in report
    assert "total_changes" in report


def test_config_disable_normalize():
    config = NormalizerConfig(normalize_priority=False, normalize_status=False)
    task = FakeTask(priority="URGENT", status="OPEN")
    changes = normalize_task(task, config)
    assert "priority" not in changes
    assert "status" not in changes


def test_default_config():
    config = default_config()
    assert config.trim_whitespace is True
    assert config.lowercase_tags is True
