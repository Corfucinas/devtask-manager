"""Tests for batch operations."""
import pytest
from src.batch_ops import (
    batch_update, batch_delete, batch_assign, batch_change_status,
    batch_add_tag, batch_remove_tag, batch_set_priority, batch_archive,
    batch_summary,
)


class FakeStatus:
    def __init__(self, value):
        self.value = value


class FakePriority:
    def __init__(self, value):
        self.value = value


class FakeTask:
    def __init__(self, id, status="todo", priority="medium", tags=None, assignee=None):
        self.id = id
        self.status = FakeStatus(status)
        self.priority = FakePriority(priority)
        self.tags = tags or []
        self.assignee = assignee


@pytest.fixture
def tasks():
    return [
        FakeTask(1, "todo", "high", ["bug"], None),
        FakeTask(2, "in-progress", "medium", ["feature"], "alice"),
        FakeTask(3, "done", "low", ["docs"], "bob"),
        FakeTask(4, "todo", "critical", ["bug", "urgent"], "charlie"),
    ]


def test_batch_update(tasks):
    result = batch_update(tasks, [1, 2], assignee="new_person")
    assert result["updated"] == 2
    assert tasks[0].assignee == "new_person"


def test_batch_delete(tasks):
    result = batch_delete(tasks, [1, 3])
    assert result["deleted"] == 2
    assert result["remaining"] == 2
    remaining_ids = {t.id for t in tasks}
    assert remaining_ids == {2, 4}


def test_batch_assign(tasks):
    result = batch_assign(tasks, [1, 2], "alice")
    assert result["assigned"] == 2
    assert tasks[0].assignee == "alice"


def test_batch_change_status(tasks):
    result = batch_change_status(tasks, [1, 4], "done")
    assert result["changed"] == 2
    assert tasks[0].status.value == "done"


def test_batch_add_tag(tasks):
    result = batch_add_tag(tasks, [1, 2], "review")
    assert result["tagged"] == 2
    assert "review" in tasks[0].tags


def test_batch_add_tag_no_duplicate(tasks):
    batch_add_tag(tasks, [1], "bug")
    assert tasks[0].tags.count("bug") == 1


def test_batch_remove_tag(tasks):
    result = batch_remove_tag(tasks, [1, 4], "bug")
    assert result["untagged"] == 2
    assert "bug" not in tasks[0].tags
    assert "urgent" in tasks[3].tags


def test_batch_set_priority(tasks):
    result = batch_set_priority(tasks, [2, 3], "high")
    assert result["changed"] == 2
    assert tasks[1].priority.value == "high"


def test_batch_archive(tasks):
    result = batch_archive(tasks, [1, 2])
    assert result["archived"] == 2
    assert tasks[0].status.value == "done"
    assert "archived" in tasks[0].tags


def test_batch_summary(tasks):
    result = batch_summary(tasks, [1, 2, 3])
    assert result["selected"] == 3
    assert result["not_found"] == 0
    assert "todo" in result["by_status"]


def test_batch_summary_not_found(tasks):
    result = batch_summary(tasks, [1, 99])
    assert result["selected"] == 1
    assert result["not_found"] == 1


def test_batch_empty_ids(tasks):
    result = batch_assign(tasks, [], "alice")
    assert result["assigned"] == 0
