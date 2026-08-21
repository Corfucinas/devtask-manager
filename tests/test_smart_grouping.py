"""Tests for smart task grouping."""
import pytest
from src.smart_grouping import (
    GroupConfig, TaskGroup, task_similarity, SmartGrouper, grouping_report,
)


class FakePriority:
    def __init__(self, value): self.value = value
class FakeStatus:
    def __init__(self, value): self.value = value
class FakeTask:
    def __init__(self, id, title="task", tags=None, priority="medium", assignee=None):
        self.id = id
        self.title = title
        self.tags = tags or []
        self.priority = FakePriority(priority)
        self.status = FakeStatus("todo")
        self.assignee = assignee


@pytest.fixture
def tasks():
    return [
        FakeTask(1, "Fix login bug auth", ["bug", "auth"], "high", "alice"),
        FakeTask(2, "Fix auth bug login", ["bug", "auth"], "high", "alice"),
        FakeTask(3, "Add dark mode feature", ["feature", "ui"], "medium", "bob"),
        FakeTask(4, "Add theme switcher", ["feature", "ui"], "medium", "bob"),
        FakeTask(5, "Write docs readme", ["docs"], "low", None),
    ]


def test_task_similarity_identical():
    a = FakeTask(1, "Fix bug auth", ["bug"], "high")
    b = FakeTask(2, "Fix bug auth", ["bug"], "high")
    assert task_similarity(a, b) > 0.5


def test_task_similarity_different():
    a = FakeTask(1, "Fix bug", ["bug"], "high", "alice")
    b = FakeTask(2, "Add feature", ["feature"], "low", "bob")
    assert task_similarity(a, b) < 0.3


def test_task_similarity_same_assignee():
    a = FakeTask(1, "Task A", [], "medium", "alice")
    b = FakeTask(2, "Task B", [], "medium", "alice")
    assert task_similarity(a, b) > 0.1  # boosted by same assignee


def test_smart_grouper_basic(tasks):
    grouper = SmartGrouper(GroupConfig(min_similarity=0.2))
    groups = grouper.group_tasks(tasks)
    assert len(groups) >= 2


def test_smart_grouper_group_count(tasks):
    grouper = SmartGrouper(GroupConfig(min_similarity=0.2))
    grouper.group_tasks(tasks)
    assert grouper.group_count() >= 2


def test_smart_grouper_all_groups(tasks):
    grouper = SmartGrouper()
    grouper.group_tasks(tasks)
    all_g = grouper.all_groups()
    assert len(all_g) >= 1


def test_smart_grouper_max_size():
    tasks = [FakeTask(i, f"Same task {i}", ["tag"], "medium") for i in range(20)]
    grouper = SmartGrouper(GroupConfig(min_similarity=0.1, max_group_size=5))
    grouper.group_tasks(tasks)
    assert all(len(g.task_ids) <= 5 for g in grouper.all_groups())


def test_grouping_report(tasks):
    grouper = SmartGrouper(GroupConfig(min_similarity=0.2))
    grouper.group_tasks(tasks)
    report = grouping_report(grouper)
    assert report["total_groups"] >= 2
    assert "avg_group_size" in report
    assert "groups_by_size" in report


def test_grouping_report_empty():
    grouper = SmartGrouper()
    report = grouping_report(grouper)
    assert report["total_groups"] == 0


def test_task_group_shared_tags():
    g = TaskGroup(id=1, name="test", task_ids=[1, 2], shared_tags=["bug", "auth"])
    assert g.shared_tags == ["bug", "auth"]
    assert g.similarity_score == 0.0


def test_config_defaults():
    c = GroupConfig()
    assert c.min_similarity == 0.3
    assert c.max_group_size == 10
