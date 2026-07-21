"""Workflow state machine for task status transitions."""

TRANSITIONS = {
    "todo": {"in-progress", "done", "cancelled"},
    "in-progress": {"review", "done", "todo", "blocked"},
    "review": {"done", "in-progress"},
    "blocked": {"todo", "in-progress"},
    "done": {"todo"},
    "cancelled": {"todo"},
}


class Workflow:
    """Manages valid task status transitions."""

    def __init__(self, transitions=None):
        self.transitions = transitions or TRANSITIONS

    def can_transition(self, from_status, to_status):
        """Check if a transition is valid."""
        valid = self.transitions.get(from_status, set())
        return to_status in valid

    def next_states(self, status):
        """Return valid next states from current status."""
        return sorted(self.transitions.get(status, set()))

    def transition(self, task, new_status):
        """Perform a validated status transition on a task."""
        current = task.status.value if hasattr(task.status, "value") else task.status
        if not self.can_transition(current, new_status):
            raise ValueError(
                f"Invalid transition: {current} -> {new_status}. "
                f"Valid: {', '.join(self.next_states(current))}"
            )
        if hasattr(task.status, "value"):
            from src.models import Status
            task.status = Status(new_status)
        else:
            task.status = new_status
        return task

    def is_terminal(self, status):
        """Check if a status is terminal (no outgoing transitions)."""
        return status not in self.transitions or not self.transitions[status]

    def all_statuses(self):
        """Return all known statuses."""
        statuses = set(self.transitions.keys())
        for targets in self.transitions.values():
            statuses.update(targets)
        return sorted(statuses)
