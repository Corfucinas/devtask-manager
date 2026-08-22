"""Advanced task filter with chaining."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


def _get_status(task):
    return task.status.value if hasattr(task.status, "value") else task.status


def _get_priority(task):
    return task.priority.value if hasattr(task.priority, "value") else task.priority


@dataclass
class Filter:
    """A single filter condition."""
    name: str
    condition: Callable
    negated: bool = False

    def apply(self, task) -> bool:
        """Apply this filter to a task."""
        result = self.condition(task)
        return not result if self.negated else result


class FilterChain:
    """A chain of filters applied in sequence."""
    def __init__(self, mode: str = "and"):
        """mode: 'and' = all must pass, 'or' = any must pass."""
        self._filters: List[Filter] = []
        self._mode = mode
        self._sort_key: Optional[Callable] = None
        self._sort_reverse: bool = False
        self._limit: Optional[int] = None

    def add(self, name, condition, negated=False):
        """Add a filter to the chain."""
        f = Filter(name=name, condition=condition, negated=negated)
        self._filters.append(f)
        return self

    def status(self, status):
        """Filter by status."""
        return self.add(f"status={status}", lambda t: _get_status(t) == status)

    def priority(self, priority):
        """Filter by priority."""
        return self.add(f"priority={priority}", lambda t: _get_priority(t) == priority)

    def has_tag(self, tag):
        """Filter by having a specific tag."""
        return self.add(f"has_tag={tag}", lambda t: tag in (getattr(t, "tags", []) or []))

    def assigned_to(self, assignee):
        """Filter by assignee."""
        return self.add(f"assignee={assignee}", lambda t: getattr(t, "assignee", None) == assignee)

    def unassigned(self):
        """Filter for unassigned tasks."""
        return self.add("unassigned", lambda t: not getattr(t, "assignee", None))

    def has_due_date(self):
        """Filter for tasks with a due date."""
        return self.add("has_due_date", lambda t: bool(getattr(t, "due_date", None)))

    def overdue(self):
        """Filter for overdue tasks."""
        def is_overdue(t):
            due = getattr(t, "due_date", None)
            if not due or _get_status(t) == "done":
                return False
            try:
                return datetime.fromisoformat(due.replace("Z", "+00:00")) < datetime.now(timezone.utc)
            except (ValueError, TypeError):
                return False
        return self.add("overdue", is_overdue)

    def negate(self, name):
        """Negate the last filter or one by name."""
        for f in reversed(self._filters):
            if name is None or f.name == name:
                f.negated = not f.negated
                return self
        return self

    def sort_by(self, key, reverse=False):
        """Sort results."""
        self._sort_key = key
        self._sort_reverse = reverse
        return self

    def limit(self, n):
        """Limit results."""
        self._limit = n
        return self

    def apply(self, tasks) -> List:
        """Apply the filter chain to tasks."""
        results = []
        for task in tasks:
            if self._mode == "and":
                if all(f.apply(task) for f in self._filters):
                    results.append(task)
            else:
                if any(f.apply(task) for f in self._filters):
                    results.append(task)
        if self._sort_key:
            results.sort(key=self._sort_key, reverse=self._sort_reverse)
        if self._limit is not None:
            results = results[:self._limit]
        return results

    def filter_count(self):
        return len(self._filters)


class FilterBuilder:
    """Fluent builder for filter chains."""
    @staticmethod
    def all():
        """Create an AND filter chain."""
        return FilterChain(mode="and")

    @staticmethod
    def any():
        """Create an OR filter chain."""
        return FilterChain(mode="or")

    @staticmethod
    def high_priority():
        """Preset: high priority tasks."""
        return (FilterBuilder.all()
                .priority("high")
                .add("not_done", lambda t: _get_status(t) != "done"))

    @staticmethod
    def overdue():
        """Preset: overdue tasks."""
        return (FilterBuilder.all()
                .overdue()
                .add("not_done", lambda t: _get_status(t) != "done"))

    @staticmethod
    def my_tasks(assignee):
        """Preset: tasks assigned to me."""
        return (FilterBuilder.all()
                .assigned_to(assignee)
                .add("not_done", lambda t: _get_status(t) != "done")))


def filter_report(tasks, chain):
    """Generate a filter statistics report."""
    filtered = chain.apply(tasks)
    return {
        "total_tasks": len(tasks),
        "filtered_count": len(filtered),
        "filter_count": chain.filter_count,
        "remaining_percentage": round(len(filtered) / max(len(tasks), 1) * 100, 1),
        "by_status": {s: sum(1 for t in filtered if _get_status(t) == s)
                      for s in ("todo", "in-progress", "done")},
        "by_priority": {p: sum(1 for t in filtered if _get_priority(t) == p)
                        for p in ("critical", "high", "medium", "low")},
    }
