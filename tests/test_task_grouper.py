"""Tests for task grouper."""
import pytest
from src.task_grouper import (
    GroupingStrategy, TaskGroup, group_tasks, Grouper,
    grouping_report, multi_group,
)


class FakePriority:
    def __init__(self, value): self.value = value
class FakeStatus:
    def __init__(self, value): self.value = value
class FakeTask:
    def __init__(self, id, priority="medium", status="todo", tags=None,
                 assignee=None, sprint_id=None):
        self.id = id
        self.priority = FakePriority(priority)
        self.status = FakeStatus(status)
        self.tags = tags or []
        self.assignee = assignee
        self.sprint_id = sprint_id


@pytest.fixture
def tasks():
    return [
        FakeTask(1, "high", "todo", ["bug"], "alice", 1),
        FakeTask(2, "medium", "done", ["feature"], "bob", 1),
        FakeTask(3, "low", "in-progress", ["bug", "ui"], "alice", 2),
        FakeTask(4, "critical", "todo", [], None),
    ]


def test_group_by_status(tasks):
    groups = group_tasks(tasks, GroupingStrategy.BY_STATUS)
    assert "todo" in groups
    assert groups["todo"].count == 2
    assert groups["done"].count == 1


def test_group_by_priority(tasks):
    groups = group_tasks(tasks, GroupingStrategy.BY_PRIORITY)
    assert "high" in groups
    assert "critical" in groups


def test_group_by_assignee(tasks):
    groups = group_tasks(tasks, GroupingStrategy.BY_ASSIGNEE)
    assert "alice" in groups
    assert "unassigned" in groups
    assert groups["alice"].count == 2


def test_group_by_tag(tasks):
    groups = group_tasks(tasks, GroupingStrategy.BY_TAG)
    assert "bug" in groups
    assert groups["bug"].count == 2
    assert "untagged" in groups


def test_group_by_sprint(tasks):
    groups = group_tasks(tasks, GroupingStrategy.BY_SPRINT)
    assert "1" in groups
    assert "2" in groups


def test_group_custom(tasks):
    groups = group_tasks(tasks, GroupingStrategy.CUSTOM, key_func=lambda t: str(t.id % 2))
    assert "0" in groups
    assert "1" in groups


def test_grouper_basic(tasks):
    g = Grouper()
    groups = g.group(tasks)
    assert len(groups) > 0


def test_grouper_set_strategy(tasks):
    g = Grouper()
    g.set_strategy(GroupingStrategy.BY_PRIORITY)
    groups = g.group(tasks)
    assert "high" in groups


def test_grouper_custom(tasks):
    g = Grouper()
    g.set_custom(lambda t: "even" if t.id % 2 == 0 else "odd")
    groups = g.group(tasks)
    assert "even" in groups
    assert "odd" in groups


def test_grouper_group_names(tasks):
    g = Grouper(GroupingStrategy.BY_STATUS)
    names = g.group_names(tasks)
    assert "todo" in names


def test_grouper_group_sizes(tasks):
    g = Grouper(GroupingStrategy.BY_STATUS)
    sizes = g.group_sizes(tasks)
    assert sizes["todo"] == 2


def test_grouping_report(tasks):
    groups = group_tasks(tasks, GroupingStrategy.BY_STATUS)
    report = grouping_report(groups)
    assert report["total_groups"] > 0
    assert "avg_group_size" in report
    assert "group_keys" in report


def test_multi_group(tasks):
    result = multi_group(tasks, [GroupingStrategy.BY_STATUS, GroupingStrategy.BY_PRIORITY])
    assert "by_status" in result
    assert "by_priority" in result


def test_task_group_add():
    g = TaskGroup(key="test")
    g.add("task1")
    g.add("task2")
    assert g.count == 2


def test_group_empty():
    groups = group_tasks([], GroupingStrategy.BY_STATUS)
    assert len(groups) == 0
