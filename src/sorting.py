"""Sort tasks by priority and date."""
from .models import Priority, Task

PRIORITY_ORDER = {
    Priority.CRITICAL: 0,
    Priority.HIGH: 1,
    Priority.MEDIUM: 2,
    Priority.LOW: 3,
}

def sort_by_priority(tasks):
    """Sort tasks by priority (critical first)."""
    return sorted(tasks, key=lambda t: PRIORITY_ORDER.get(t.priority, 99))

def sort_by_created(tasks):
    """Sort tasks by creation date (newest first)."""
    return sorted(tasks, key=lambda t: t.created_at, reverse=True)
