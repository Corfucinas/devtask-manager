"""Advanced filter CLI commands for tasks."""
from datetime import datetime, timezone
from typing import Callable, List


def _parse(iso_string: str) -> datetime:
    return datetime.fromisoformat(iso_string.replace("Z", "+00:00"))


def filter_by_date_range(tasks, start: str, end: str) -> list:
    """Filter tasks created within a date range (inclusive)."""
    start_dt = _parse(start)
    end_dt = _parse(end)
    results = []
    for t in tasks:
        created = getattr(t, "created_at", None)
        if created:
            ct = _parse(created)
            if start_dt <= ct <= end_dt:
                results.append(t)
    return results


def filter_by_tags(tasks, tags: List[str], mode: str = "any") -> list:
    """Filter tasks by tags. mode='all' requires all tags, 'any' requires at least one."""
    if not tags:
        return list(tasks)
    results = []
    for t in tasks:
        task_tags = set(getattr(t, "tags", []) or [])
        if mode == "all":
            if set(tags).issubset(task_tags):
                results.append(t)
        else:
            if set(tags) & task_tags:
                results.append(t)
    return results


def filter_by_assignee(tasks, assignee: str) -> list:
    """Filter tasks assigned to a specific person."""
    return [t for t in tasks if getattr(t, "assignee", None) == assignee]


def filter_by_priority(tasks, priorities: List[str]) -> list:
    """Filter tasks by one or more priority levels."""
    results = []
    for t in tasks:
        priority = t.priority.value if hasattr(t.priority, "value") else t.priority
        if priority in priorities:
            results.append(t)
    return results


def compose_filters(tasks, *filters: Callable) -> list:
    """Chain multiple filter functions together."""
    result = list(tasks)
    for f in filters:
        result = f(result)
    return result


def filter_inactive(tasks, days: int = 30) -> list:
    """Filter tasks not updated in N or more days."""
    now = datetime.now(timezone.utc)
    results = []
    for t in tasks:
        updated = getattr(t, "updated_at", None)
        if updated:
            age = (now - _parse(updated)).days
            if age >= days:
                results.append(t)
    return results


def filter_overdue(tasks) -> list:
    """Filter tasks that have a due date in the past and are not done."""
    now = datetime.now(timezone.utc)
    results = []
    for t in tasks:
        due = getattr(t, "due_date", None)
        status = t.status.value if hasattr(t.status, "value") else t.status
        if due and status != "done":
            if _parse(due) < now:
                results.append(t)
    return results


def sort_by_created(tasks, descending: bool = False) -> list:
    """Sort tasks by creation date."""
    return sorted(
        tasks,
        key=lambda t: getattr(t, "created_at", ""),
        reverse=descending,
    )
