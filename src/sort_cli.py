"""Sort CLI commands for task ordering."""
from typing import List, Tuple


_PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
_STATUS_ORDER = {"todo": 0, "in-progress": 1, "review": 2, "blocked": 3, "done": 4}


def _get_status(task) -> str:
    return task.status.value if hasattr(task.status, "value") else task.status


def _get_priority(task) -> str:
    return task.priority.value if hasattr(task.priority, "value") else task.priority


def sort_by_priority(tasks, descending: bool = False) -> list:
    """Sort tasks by priority (critical first by default)."""
    return sorted(
        tasks,
        key=lambda t: _PRIORITY_ORDER.get(_get_priority(t), 99),
        reverse=descending,
    )


def sort_by_status(tasks) -> list:
    """Sort tasks by status in workflow order."""
    return sorted(tasks, key=lambda t: _STATUS_ORDER.get(_get_status(t), 99))


def sort_by_title(tasks, descending: bool = False) -> list:
    """Sort tasks alphabetically by title."""
    return sorted(tasks, key=lambda t: getattr(t, "title", ""), reverse=descending)


def sort_by_updated(tasks, descending: bool = True) -> list:
    """Sort tasks by last updated time (most recent first by default)."""
    return sorted(
        tasks,
        key=lambda t: getattr(t, "updated_at", ""),
        reverse=descending,
    )


def sort_by_created(tasks, descending: bool = False) -> list:
    """Sort tasks by creation time (oldest first by default)."""
    return sorted(
        tasks,
        key=lambda t: getattr(t, "created_at", ""),
        reverse=descending,
    )


def sort_by_id(tasks, descending: bool = False) -> list:
    """Sort tasks by ID."""
    return sorted(tasks, key=lambda t: getattr(t, "id", 0), reverse=descending)


def multi_sort(tasks, *keys: Tuple[str, bool]) -> list:
    """Sort tasks by multiple keys. Each key is (field_name, descending).

    Example: multi_sort(tasks, ("priority", False), ("created_at", True))
    """
    if not keys:
        return list(tasks)
    result = list(tasks)
    for field_name, descending in reversed(keys):
        if field_name == "priority":
            result = sort_by_priority(result, descending=descending)
        elif field_name == "status":
            result = sort_by_status(result)
        elif field_name == "title":
            result = sort_by_title(result, descending=descending)
        elif field_name == "updated_at":
            result = sort_by_updated(result, descending=descending)
        elif field_name == "created_at":
            result = sort_by_created(result, descending=descending)
        elif field_name == "id":
            result = sort_by_id(result, descending=descending)
    return result


def group_and_sort(tasks, group_by: str = "status", sort_by: str = "priority") -> dict:
    """Group tasks by a field, then sort each group."""
    groups = {}
    for t in tasks:
        if group_by == "status":
            key = _get_status(t)
        elif group_by == "priority":
            key = _get_priority(t)
        else:
            key = str(getattr(t, group_by, "unknown"))
        if key not in groups:
            groups[key] = []
        groups[key].append(t)

    if sort_by == "priority":
        for key in groups:
            groups[key] = sort_by_priority(groups[key])
    elif sort_by == "title":
        for key in groups:
            groups[key] = sort_by_title(groups[key])

    return dict(sorted(groups.items()))
