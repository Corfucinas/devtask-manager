"""Tests for task assignment."""
import pytest
from src.assignments import (
    assign_task, unassign_task, workload, reassign_task,
    assignment_history, current_assignee, team_workload, unassigned_tasks,
)


class FakeStatus:
    def __init__(self, value):
        self.value = value


class FakeTask:
    def __init__(self, id, status="todo"):
        self.id = id
        self.status = FakeStatus(status)
        self.assignee = None
        self.assigned_at = None
        self.assignment_history = None


@pytest.fixture
def tasks():
    t1 = FakeTask(1, "todo")
    t2 = FakeTask(2, "in-progress")
    t3 = FakeTask(3, "done")
    assign_task(t1, "alice")
    assign_task(t2, "alice")
    assign_task(t3, "bob")
    return [t1, t2, t3]


def test_assign_task():
    task = FakeTask(1)
    assign_task(task, "alice")
    assert task.assignee == "alice"
    assert task.assigned_at is not None
    assert len(task.assignment_history) == 1


def test_unassign_task():
    task = FakeTask(1)
    assign_task(task, "alice")
    unassign_task(task)
    assert task.assignee is None
    assert task.assigned_at is None


def test_workload(tasks):
    alice = workload(tasks, "alice")
    assert alice["total"] == 2
    assert alice["open"] == 2
    assert alice["done"] == 0


def test_reassign_task():
    task = FakeTask(1)
    assign_task(task, "alice")
    reassign_task(task, "bob")
    assert task.assignee == "bob"
    assert len(task.assignment_history) == 2


def test_assignment_history():
    task = FakeTask(1)
    assign_task(task, "alice")
    assign_task(task, "bob")
    history = assignment_history(task)
    assert len(history) == 2
    assert history[0]["user"] == "alice"
    assert history[1]["previous"] == "alice"


def test_current_assignee():
    task = FakeTask(1)
    assert current_assignee(task) is None
    assign_task(task, "alice")
    assert current_assignee(task) == "alice"


def test_team_workload(tasks):
    result = team_workload(tasks, ["alice", "bob", "charlie"])
    assert result["alice"]["total"] == 2
    assert result["bob"]["total"] == 1
    assert result["charlie"]["total"] == 0


def test_unassigned_tasks(tasks):
    t4 = FakeTask(4, "todo")
    all_tasks = tasks + [t4]
    unassigned = unassigned_tasks(all_tasks)
    assert len(unassigned) == 1
    assert unassigned[0].id == 4
