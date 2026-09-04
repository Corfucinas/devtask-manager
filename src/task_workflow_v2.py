"""Task workflow with custom state transitions."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set


@dataclass
class WorkflowState:
    """A state in the workflow."""
    name: str
    allowed_transitions: List[str] = field(default_factory=list)
    is_terminal: bool = False
    is_initial: bool = False
    on_enter: Optional[Callable] = None
    on_exit: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowTransition:
    """A record of a state transition."""
    from_state: str
    to_state: str
    actor: str = ""
    reason: str = ""
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class TaskWorkflowV2:
    """Manages task workflow state transitions."""
    def __init__(self, initial_state: str = "todo"):
        self._states: Dict[str, WorkflowState] = {}
        self._current_state = initial_state
        self._history: List[WorkflowTransition] = []
        self._initial_state = initial_state

    @property
    def state(self) -> str:
        return self._current_state

    def add_state(self, name, allowed_transitions=None, is_terminal=False,
                  is_initial=False, on_enter=None, on_exit=None, **metadata):
        """Add a state to the workflow."""
        state = WorkflowState(
            name=name, allowed_transitions=allowed_transitions or [],
            is_terminal=is_terminal, is_initial=is_initial,
            on_enter=on_enter, on_exit=on_exit, metadata=metadata)
        self._states[name] = state
        return state

    def remove_state(self, name) -> bool:
        if name in self._states:
            del self._states[name]
            return True
        return False

    def get_state(self, name) -> Optional[WorkflowState]:
        return self._states.get(name)

    def all_states(self) -> List[str]:
        return sorted(self._states.keys())

    def state_count(self) -> int:
        return len(self._states)

    def can_transition(self, target: str) -> bool:
        """Check if transition to target is allowed."""
        state = self._states.get(self._current_state)
        if not state:
            return False
        return target in state.allowed_transitions

    def transition(self, target: str, actor: str = "", reason: str = "") -> bool:
        """Execute a state transition."""
        if not self.can_transition(target):
            return False
        current = self._states.get(self._current_state)
        target_state = self._states.get(target)

        if current and current.on_exit:
            try:
                current.on_exit(self._current_state, target)
            except Exception:
                pass

        t = WorkflowTransition(from_state=self._current_state, to_state=target,
                                actor=actor, reason=reason)
        self._history.append(t)
        self._current_state = target

        if target_state and target_state.on_enter:
            try:
                target_state.on_enter(self._current_state, None)
            except Exception:
                pass
        return True

    def valid_transitions(self) -> List[str]:
        """Return allowed next states."""
        state = self._states.get(self._current_state)
        return state.allowed_transitions if state else []

    def history(self) -> List[WorkflowTransition]:
        return list(self._history)

    def transition_count(self) -> int:
        return len(self._history)

    def is_terminal(self) -> bool:
        state = self._states.get(self._current_state)
        return state.is_terminal if state else False

    def last_transition(self) -> Optional[WorkflowTransition]:
        return self._history[-1] if self._history else None

    def reset(self):
        """Reset to initial state and clear history."""
        self._current_state = self._initial_state
        self._history = []

    def visited_states(self) -> List[str]:
        """Return all visited states."""
        visited = [self._initial_state]
        for t in self._history:
            if t.to_state not in visited:
                visited.append(t.to_state)
        return visited

    def transition_path(self) -> List[str]:
        """Return the full transition path."""
        path = [self._initial_state]
        for t in self._history:
            path.append(t.to_state)
        return path


def workflow_report(workflow: TaskWorkflowV2) -> Dict:
    """Generate a workflow report."""
    return {
        "current_state": workflow.state,
        "is_terminal": workflow.is_terminal(),
        "valid_transitions": workflow.valid_transitions(),
        "transition_count": workflow.transition_count(),
        "total_states": workflow.state_count(),
        "states": workflow.all_states(),
        "visited_states": workflow.visited_states(),
    }


def default_workflow() -> TaskWorkflowV2:
    """Create a default task workflow."""
    wf = TaskWorkflowV2(initial_state="todo")
    wf.add_state("todo", allowed_transitions=["in-progress", "cancelled"], is_initial=True)
    wf.add_state("in-progress", allowed_transitions=["review", "done", "cancelled"])
    wf.add_state("review", allowed_transitions=["done", "in-progress"])
    wf.add_state("done", allowed_transitions=[], is_terminal=True)
    wf.add_state("cancelled", allowed_transitions=[], is_terminal=True)
    return wf
