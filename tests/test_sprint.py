"""Tests for sprint planning."""
import pytest
from datetime import datetime, timezone, timedelta
from src.sprint import (
    Sprint, add_to_sprint, sprint_capacity, sprint_velocity,
    active_sprint, sprint_completion_rate,
)


class FakeStatus:
    def __init__(self, value):
        self.value = value


class FakeTask:
    def __init__(self, id, status="todo", story_points=3):
        self.id = id
        self.status = FakeStatus(status)
        self.story_points = story_points
        self.sprint_id = None


@pytest.fixture
def sprint():
    return Sprint(
        id=1, name="Sprint 1",
        start_date="2026-01-01", end_date="2026-01-14",
        capacity=20,
    )


@pytest.fixture
def tasks():
    return [
        FakeTask(1, "done", 5),
        FakeTask(2, "done", 3),
        FakeTask(3, "in-progress", 8),
        FakeTask(4, "todo", 5),
    ]


def test_sprint_from_dict():
    data = {"id": 1, "name": "S1", "start_date": "2026-01-01", "end_date": "2026-01-14"}
    s = Sprint.from_dict(data)
    assert s.name == "S1"
    assert s.capacity == 0


def test_sprint_to_dict(sprint):
    d = sprint.to_dict()
    assert d["id"] == 1
    assert d["name"] == "Sprint 1"
    assert d["capacity"] == 20


def test_duration_days(sprint):
    assert sprint.duration_days() == 13


def test_add_to_sprint(sprint):
    task = FakeTask(1)
    add_to_sprint(task, sprint)
    assert 1 in sprint.tasks
    assert task.sprint_id == 1
    add_to_sprint(task, sprint)
    assert sprint.tasks.count(1) == 1


def test_sprint_capacity(sprint, tasks):
    sprint.tasks = [1, 2, 3, 4]
    cap = sprint_capacity(sprint, tasks)
    assert cap["used"] == 21
    assert cap["total"] == 20
    assert cap["over_capacity"] is True
    assert cap["remaining"] == 0


def test_sprint_velocity(sprint, tasks):
    sprint.tasks = [1, 2, 3, 4]
    assert sprint_velocity(sprint, tasks) == 8


def test_active_sprint():
    past = (datetime.now(timezone.utc) - timedelta(days=30)).date().isoformat()
    future = (datetime.now(timezone.utc) + timedelta(days=30)).date().isoformat()
    s2 = Sprint(2, "active", (datetime.now(timezone.utc) - timedelta(days=5)).date().isoformat(), future)
    active = active_sprint([s2])
    assert active is not None
    assert active.name == "active"


def test_sprint_completion_rate(sprint, tasks):
    sprint.tasks = [1, 2, 3, 4]
    rate = sprint_completion_rate(sprint, tasks)
    assert rate == 50.0
