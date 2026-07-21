"""Tests for workflow state machine."""
import pytest
from src.workflow import Workflow, TRANSITIONS


class FakeStatus:
    def __init__(self, value):
        self.value = value


class FakeTask:
    def __init__(self, status="todo"):
        self.status = FakeStatus(status)


@pytest.fixture
def wf():
    return Workflow()


def test_can_transition_valid(wf):
    assert wf.can_transition("todo", "in-progress") is True
    assert wf.can_transition("in-progress", "done") is True


def test_can_transition_invalid(wf):
    assert wf.can_transition("todo", "review") is False
    assert wf.can_transition("done", "in-progress") is False


def test_next_states(wf):
    states = wf.next_states("todo")
    assert "in-progress" in states
    assert "done" in states
    assert "cancelled" in states


def test_transition_valid(wf):
    task = FakeTask("todo")
    wf.transition(task, "in-progress")
    assert task.status.value == "in-progress"


def test_transition_invalid(wf):
    task = FakeTask("todo")
    with pytest.raises(ValueError, match="Invalid transition"):
        wf.transition(task, "review")


def test_is_terminal(wf):
    assert wf.is_terminal("done") is False
    assert wf.is_terminal("nonexistent") is True


def test_all_statuses(wf):
    statuses = wf.all_statuses()
    assert "todo" in statuses
    assert "done" in statuses
    assert "review" in statuses
    assert "blocked" in statuses


def test_blocked_can_resume(wf):
    assert wf.can_transition("blocked", "in-progress") is True
    assert wf.can_transition("blocked", "todo") is True
