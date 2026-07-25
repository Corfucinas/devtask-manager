"""Tests for team capacity planning."""
import pytest
from src.capacity import (
    TeamMember, allocate_task, deallocate_task, team_capacity,
    available_capacity, find_by_skill, most_available, least_busy,
    rebalance_suggestion,
)


class FakeTask:
    def __init__(self, id):
        self.id = id


@pytest.fixture
def team():
    return [
        TeamMember("alice", 40, ["python", "frontend"]),
        TeamMember("bob", 40, ["python", "backend"]),
        TeamMember("charlie", 20, ["devops"]),
    ]


def test_team_member_defaults():
    m = TeamMember("alice")
    assert m.weekly_capacity == 40.0
    assert m.skills == []
    assert m.allocated_hours == 0.0
    assert m.remaining_capacity == 40.0
    assert m.utilization_percentage == 0.0
    assert m.is_overallocated is False


def test_utilization():
    m = TeamMember("alice", 40)
    m.allocated_hours = 30
    assert m.utilization_percentage == 75.0
    assert m.remaining_capacity == 10.0


def test_overallocated():
    m = TeamMember("alice", 40)
    m.allocated_hours = 45
    assert m.is_overallocated is True


def test_allocate_task(team):
    task = FakeTask(1)
    assert allocate_task(team[0], task, 10) is True
    assert team[0].allocated_hours == 10


def test_allocate_over_capacity(team):
    task = FakeTask(1)
    assert allocate_task(team[0], task, 50) is False
    assert team[0].allocated_hours == 0


def test_deallocate_task(team):
    task = FakeTask(1)
    allocate_task(team[0], task, 10)
    assert deallocate_task(team[0], 1) is True
    assert team[0].allocated_hours == 0
    assert deallocate_task(team[0], 999) is False


def test_team_capacity(team):
    allocate_task(team[0], FakeTask(1), 20)
    allocate_task(team[1], FakeTask(2), 35)
    cap = team_capacity(team)
    assert cap["total_capacity"] == 100
    assert cap["total_allocated"] == 55
    assert cap["total_remaining"] == 45
    assert cap["overallocated_members"] == 0


def test_available_capacity(team):
    allocate_task(team[0], FakeTask(1), 35)
    available = available_capacity(team, min_hours=5)
    assert team[1] in available
    assert team[2] in available


def test_find_by_skill(team):
    python_devs = find_by_skill(team, "python")
    assert len(python_devs) == 2
    assert {m.name for m in python_devs} == {"alice", "bob"}
    devops = find_by_skill(team, "devops")
    assert len(devops) == 1


def test_most_available(team):
    allocate_task(team[0], FakeTask(1), 30)
    m = most_available(team)
    assert m is not None
    assert m.name in ("bob", "charlie")


def test_least_busy(team):
    allocate_task(team[0], FakeTask(1), 30)
    m = least_busy(team)
    assert m is not None
    assert m.allocated_hours == 0


def test_most_available_empty():
    assert most_available([]) is None


def test_rebalance_suggestion(team):
    allocate_task(team[0], FakeTask(1), 45)
    allocate_task(team[1], FakeTask(2), 10)
    suggestions = rebalance_suggestion(team)
    assert len(suggestions) > 0
    assert suggestions[0]["from"] == "alice"
    assert suggestions[0]["hours"] > 0
