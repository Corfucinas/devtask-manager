"""Tests for task state machine."""
import pytest
from src.task_state import TaskStateMachine, StateTransition, VALID_TRANSITIONS, STATE_INFO


@pytest.fixture
def sm():
    return TaskStateMachine(initial_state="todo")


def test_initial_state():
    sm = TaskStateMachine("todo")
    assert sm.state == "todo"


def test_can_transition_valid(sm):
    assert sm.can_transition("in_progress") is True


def test_can_transition_invalid(sm):
    assert sm.can_transition("done") is False  # can't go todo->done directly


def test_valid_targets(sm):
    targets = sm.valid_targets()
    assert "in_progress" in targets
    assert "cancelled" in targets


def test_transition_valid(sm):
    assert sm.transition("in_progress", reason="Started") is True
    assert sm.state == "in_progress"


def test_transition_invalid(sm):
    assert sm.transition("done") is False
    assert sm.state == "todo"


def test_transition_history(sm):
    sm.transition("in_progress")
    sm.transition("review")
    assert sm.transition_count() == 2
    assert sm.history()[0].from_state == "todo"
    assert sm.history()[1].to_state == "review"


def test_last_transition(sm):
    sm.transition("in_progress", reason="Started")
    last = sm.last_transition()
    assert last is not None
    assert last.reason == "Started"


def test_last_transition_empty():
    sm = TaskStateMachine("todo")
    assert sm.last_transition() is None


def test_is_terminal(sm):
    assert sm.is_terminal() is False


def test_is_terminal_archived():
    sm = TaskStateMachine("archived")
    assert sm.is_terminal() is False  # archived can reopen


def test_state_info(sm):
    info = sm.state_info()
    assert info["label"] == "To Do"
    assert info["order"] == 1


def test_all_states():
    sm = TaskStateMachine("todo")
    states = sm.all_states()
    assert "todo" in states
    assert "done" in states
    assert "archived" in states


def test_reset(sm):
    sm.transition("in_progress")
    sm.reset("todo")
    assert sm.state == "todo"
    assert sm.transition_count() == 0


def test_full_lifecycle():
    sm = TaskStateMachine("backlog")
    assert sm.transition("todo") is True
    assert sm.transition("in_progress") is True
    assert sm.transition("review") is True
    assert sm.transition("done") is True
    assert sm.transition("archived") is True
    assert sm.transition_count() == 5


def test_blocked_lifecycle():
    sm = TaskStateMachine("todo")
    assert sm.transition("blocked") is True
    assert sm.transition("todo") is True  # can unblock
    assert sm.transition("in_progress") is True


def test_actor_tracking(sm):
    sm.transition("in_progress", actor="alice")
    assert sm.last_transition().actor == "alice"
