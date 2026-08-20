"""Tests for automatic assignment."""
import pytest
from src.auto_assign import (
    TeamMemberInfo, AssignmentRule, AutoAssigner,
    assignment_report, default_rules,
)


class FakePriority:
    def __init__(self, value): self.value = value
class FakeStatus:
    def __init__(self, value): self.value = value
class FakeTask:
    def __init__(self, id, priority="medium", status="todo", tags=None):
        self.id = id
        self.priority = FakePriority(priority)
        self.status = FakeStatus(status)
        self.tags = tags or []


@pytest.fixture
def team():
    return [
        TeamMemberInfo("alice", skills=["development", "senior"], max_load=3),
        TeamMemberInfo("bob", skills=["testing"], max_load=3),
        TeamMemberInfo("charlie", skills=["development"], max_load=3),
    ]


@pytest.fixture
def assigner():
    a = AutoAssigner()
    a.add_rule("Bug to QA", lambda t: "bug" in (t.tags or []),
               required_skill="testing", priority=10)
    a.add_rule("Any available", lambda t: True, priority=1)
    return a


def test_add_rule():
    a = AutoAssigner()
    r = a.add_rule("test", lambda t: True)
    assert r.id == 1
    assert a.count() == 1


def test_remove_rule(assigner):
    assert assigner.remove_rule(1) is True
    assert assigner.count() == 1


def test_all_rules_sorted(assigner):
    rules = assigner.all_rules()
    assert rules[0].priority >= rules[1].priority


def test_assign_bug_to_qa(assigner, team):
    task = FakeTask(1, tags=["bug"])
    result = assigner.assign(task, team)
    assert result is not None
    assert result["assignee"] == "bob"
    assert result["skill_matched"] == "testing"


def test_assign_fallback(assigner, team):
    task = FakeTask(1, tags=["feature"])
    result = assigner.assign(task, team)
    assert result is not None


def test_assign_no_match():
    a = AutoAssigner()
    a.add_rule("No match", lambda t: False, required_skill="nonexistent")
    task = FakeTask(1)
    team = [TeamMemberInfo("alice", skills=["dev"])]
    assert a.assign(task, team) is None


def test_workload_balancing(assigner):
    team = [
        TeamMemberInfo("alice", skills=["testing"], current_load=2, max_load=5),
        TeamMemberInfo("bob", skills=["testing"], current_load=0, max_load=5),
    ]
    task = FakeTask(1, tags=["bug"])
    result = assigner.assign(task, team)
    assert result["assignee"] == "bob"  # less loaded


def test_assignment_count(assigner, team):
    task = FakeTask(1, tags=["bug"])
    assigner.assign(task, team)
    assert assigner.assignment_count() == 1


def test_clear_assignments(assigner, team):
    assigner.assign(FakeTask(1, tags=["bug"]), team)
    assigner.clear_assignments()
    assert assigner.assignment_count() == 0


def test_assignment_report(assigner, team):
    tasks = [FakeTask(1, tags=["bug"]), FakeTask(2)]
    for t in tasks:
        assigner.assign(t, team)
    report = assignment_report(assigner, tasks, team)
    assert report["total_tasks"] == 2
    assert "team_load" in report


def test_default_rules():
    a = default_rules()
    assert a.count() == 4
    rules = a.all_rules()
    assert rules[0].priority >= rules[-1].priority
