"""Tests for task workflow."""
import pytest
from src.task_workflow_v2 import (
    WorkflowState, WorkflowTransition, TaskWorkflowV2, workflow_report, default_workflow,
)


@pytest.fixture
def workflow():
    wf = TaskWorkflowV2(initial_state="todo")
    wf.add_state("todo", allowed_transitions=["in-progress", "cancelled"], is_initial=True)
    wf.add_state("in-progress", allowed_transitions=["review", "done", "cancelled"])
    wf.add_state("review", allowed_transitions=["done", "in-progress"])
    wf.add_state("done", allowed_transitions=[], is_terminal=True)
    wf.add_state("cancelled", allowed_transitions=[], is_terminal=True)
    return wf


def test_initial_state(workflow):
    assert workflow.state == "todo"


def test_add_state():
    wf = TaskWorkflowV2()
    state = wf.add_state("custom")
    assert state.name == "custom"
    assert wf.state_count() == 1


def test_remove_state(workflow):
    assert workflow.remove_state("cancelled") is True
    assert workflow.state_count() == 4
    assert workflow.remove_state("nonexistent") is False


def test_get_state(workflow):
    state = workflow.get_state("todo")
    assert state is not None
    assert state.is_initial is True


def test_can_transition_valid(workflow):
    assert workflow.can_transition("in-progress") is True


def test_can_transition_invalid(workflow):
    assert workflow.can_transition("done") is False


def test_transition_valid(workflow):
    assert workflow.transition("in-progress", actor="alice") is True
    assert workflow.state == "in-progress"


def test_transition_invalid(workflow):
    assert workflow.transition("done") is False


def test_valid_transitions(workflow):
    transitions = workflow.valid_transitions()
    assert "in-progress" in transitions
    assert "cancelled" in transitions


def test_history(workflow):
    workflow.transition("in-progress", actor="alice")
    workflow.transition("review", actor="bob")
    assert workflow.transition_count() == 2
    assert workflow.history()[0].actor == "alice"


def test_last_transition(workflow):
    workflow.transition("in-progress", actor="alice")
    last = workflow.last_transition()
    assert last.to_state == "in-progress"


def test_last_transition_empty():
    wf = TaskWorkflowV2()
    assert wf.last_transition() is None


def test_is_terminal(workflow):
    assert workflow.is_terminal() is False


def test_is_terminal_done(workflow):
    workflow.transition("in-progress")
    workflow.transition("done")
    assert workflow.is_terminal() is True


def test_reset(workflow):
    workflow.transition("in-progress")
    workflow.reset()
    assert workflow.state == "todo"
    assert workflow.transition_count() == 0


def test_visited_states(workflow):
    workflow.transition("in-progress")
    workflow.transition("review")
    visited = workflow.visited_states()
    assert "todo" in visited
    assert "in-progress" in visited
    assert "review" in visited


def test_transition_path(workflow):
    workflow.transition("in-progress")
    workflow.transition("review")
    workflow.transition("done")
    path = workflow.transition_path()
    assert path == ["todo", "in-progress", "review", "done"]


def test_on_enter_callback(workflow):
    calls = []
    workflow.add_state("testing", on_enter=lambda s, t: calls.append(s))
    workflow.transition("in-progress")
    workflow.transition("review")
    # manually add testing to valid transitions of review
    workflow._states["review"].allowed_transitions.append("testing")
    workflow.transition("testing")
    assert len(calls) > 0


def test_workflow_report(workflow):
    report = workflow_report(workflow)
    assert report["current_state"] == "todo"
    assert report["transition_count"] == 0
    assert "valid_transitions" in report


def test_default_workflow():
    wf = default_workflow()
    assert wf.state_count() == 5
    assert wf.state == "todo"


def test_full_lifecycle(workflow):
    workflow.transition("in-progress")
    workflow.transition("review")
    workflow.transition("done")
    assert workflow.is_terminal() is True
