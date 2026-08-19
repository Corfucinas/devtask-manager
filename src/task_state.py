"""Task state machine with transition history."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set


VALID_TRANSITIONS = {
    "backlog": {"todo", "cancelled"},
    "todo": {"in_progress", "cancelled", "blocked"},
    "in_progress": {"review", "done", "blocked", "todo"},
    "review": {"done", "in_progress", "rejected"},
    "blocked": {"todo", "in_progress", "cancelled"},
    "rejected": {"todo", "in_progress"},
    "done": {"reopened", "archived"},
    "reopened": {"todo", "in_progress"},
    "cancelled": {"todo"},
    "archived": {"reopened"},
}

STATE_INFO = {
    "backlog": {"label": "Backlog", "color": "#999", "order": 0},
    "todo": {"label": "To Do", "color": "#0075ca", "order": 1},
    "in_progress": {"label": "In Progress", "color": "#fbca04", "order": 2},
    "review": {"label": "In Review", "color": "#d876e3", "order": 3},
    "blocked": {"label": "Blocked", "color": "#e99695", "order": 4},
    "rejected": {"label": "Rejected", "color": "#d73a4a", "order": 5},
    "done": {"label": "Done", "color": "#0e8a16", "order": 6},
    "reopened": {"label": "Reopened", "color": "#fbca04", "order": 1},
    "cancelled": {"label": "Cancelled", "color": "#b60205", "order": 7},
    "archived": {"label": "Archived", "color": "#999", "order": 8},
}


@dataclass
class StateTransition:
    """A recorded state transition."""
    from_state: str
    to_state: str
    reason: str = ""
    actor: str = ""
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class TaskStateMachine:
    """Manages task state transitions with validation."""
    def __init__(self, initial_state="backlog", transitions=None):
        self._state = initial_state
        self._transitions: Dict[str, Set[str]] = transitions or VALID_TRANSITIONS
        self._history: List[StateTransition] = []

    @property
    def state(self) -> str:
        return self._state

    def can_transition(self, target: str) -> bool:
        """Check if transition is valid."""
        valid = self._transitions.get(self._state, set())
        return target in valid

    def valid_targets(self) -> List[str]:
        """Return valid next states."""
        return sorted(self._transitions.get(self._state, set()))

    def transition(self, target: str, reason="", actor="") -> bool:
        """Execute a state transition."""
        if not self.can_transition(target):
            return False
        t = StateTransition(from_state=self._state, to_state=target,
                             reason=reason, actor=actor)
        self._history.append(t)
        self._state = target
        return True

    def history(self) -> List[StateTransition]:
        """Return transition history."""
        return list(self._history)

    def last_transition(self) -> Optional[StateTransition]:
        """Return the most recent transition."""
        return self._history[-1] if self._history else None

    def transition_count(self) -> int:
        """Return number of transitions."""
        return len(self._history)

    def is_terminal(self) -> bool:
        """Check if current state is terminal (no outgoing)."""
        return not self._transitions.get(self._state, set())

    def state_info(self) -> dict:
        """Return info about current state."""
        return STATE_INFO.get(self._state, {"label": self._state, "color": "#999", "order": 99})

    def all_states(self) -> List[str]:
        """Return all known states."""
        states = set(self._transitions.keys())
        for targets in self._transitions.values():
            states.update(targets)
        return sorted(states)

    def reset(self, state="backlog"):
        """Reset to a state and clear history."""
        self._state = state
        self._history = []
