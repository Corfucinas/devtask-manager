"""Tests for milestone tracking."""
import pytest
from datetime import datetime, timezone, timedelta
from src.milestones import (
    Milestone, add_to_milestone, remove_from_milestone,
    milestone_progress, is_milestone_complete, milestone_summary,
    overdue_milestones, upcoming_milestones, tasks_without_milestone,
)


class FakeStatus:
    def __init__(self, value):
        self.value = value


class FakeTask:
    def __init__(self, id, status="todo"):
        self.id = id
        self.status = FakeStatus(status)
        self.milestone_id = None


@pytest.fixture
def milestone():
    return Milestone(id=1, name="MVP", due_date="2026-06-01T00:00:00+00:00")


@pytest.fixture
def tasks():
    return [
        FakeTask(1, "done"),
        FakeTask(2, "done"),
        FakeTask(3, "in-progress"),
        FakeTask(4, "todo"),
    ]


def test_milestone_creation():
    m = Milestone(id=1, name="Release 1.0")
    assert m.id == 1
    assert m.name == "Release 1.0"
    assert m.tasks == []
    assert m.created_at != ""


def test_add_to_milestone(milestone):
    task = FakeTask(1)
    add_to_milestone(task, milestone)
    assert 1 in milestone.tasks
    assert task.milestone_id == 1
    add_to_milestone(task, milestone)
    assert milestone.tasks.count(1) == 1


def test_remove_from_milestone(milestone):
    task = FakeTask(1)
    add_to_milestone(task, milestone)
    assert remove_from_milestone(task, milestone) is True
    assert 1 not in milestone.tasks
    assert remove_from_milestone(task, milestone) is False


def test_milestone_progress(milestone, tasks):
    milestone.tasks = [1, 2, 3, 4]
    progress = milestone_progress(milestone, tasks)
    assert progress["total"] == 4
    assert progress["done"] == 2
    assert progress["percentage"] == 50.0


def test_milestone_progress_empty(milestone):
    progress = milestone_progress(milestone, [])
    assert progress["total"] == 0
    assert progress["percentage"] == 0.0


def test_is_milestone_complete(milestone, tasks):
    milestone.tasks = [1, 2]
    assert is_milestone_complete(milestone, tasks) is False
    for t in tasks:
        if t.id in [1, 2]:
            t.status = FakeStatus("done")
    assert is_milestone_complete(milestone, tasks) is True


def test_milestone_summary(milestone, tasks):
    milestone.tasks = [1, 2, 3, 4]
    m2 = Milestone(id=2, name="Release 2.0")
    m2.tasks = [3]
    summaries = milestone_summary([milestone, m2], tasks)
    assert len(summaries) == 2
    assert summaries[0]["name"] == "MVP"
    assert summaries[0]["percentage"] == 50.0
    assert summaries[1]["done"] == 0


def test_overdue_milestones():
    past = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    future = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    m1 = Milestone(1, "past", due_date=past)
    m2 = Milestone(2, "future", due_date=future)
    overdue = overdue_milestones([m1, m2])
    assert len(overdue) == 1
    assert overdue[0].name == "past"


def test_upcoming_milestones():
    soon = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    far = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    m1 = Milestone(1, "soon", due_date=soon)
    m2 = Milestone(2, "far", due_date=far)
    upcoming = upcoming_milestones([m1, m2], days=7)
    assert len(upcoming) == 1
    assert upcoming[0].name == "soon"


def test_tasks_without_milestone(tasks):
    t1 = FakeTask(1)
    t1.milestone_id = 5
    result = tasks_without_milestone([t1, tasks[1]])
    assert len(result) == 1
    assert result[0].id == 2
