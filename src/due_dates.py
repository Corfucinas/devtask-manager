"""Due date management and reminders."""
from datetime import datetime, timezone
from typing import List, Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse(iso_string: str) -> datetime:
    return datetime.fromisoformat(iso_string.replace("Z", "+00:00"))


def set_due_date(task, date: str) -> None:
    """Set the due date for a task."""
    task.due_date = date


def get_due_date(task) -> Optional[str]:
    """Return the due date string or None."""
    return getattr(task, "due_date", None)


def is_overdue(task) -> bool:
    """Check if a task is past its due date and not done."""
    due = getattr(task, "due_date", None)
    if not due:
        return False
    status = task.status.value if hasattr(task.status, "value") else task.status
    if status == "done":
        return False
    return _parse(due) < _now()


def days_until_due(task) -> int:
    """Return days until due (negative if overdue). Returns None if no due date."""
    due = getattr(task, "due_date", None)
    if not due:
        return None
    delta = _parse(due) - _now()
    return delta.days


def due_soon(tasks, within_days: int = 3) -> List:
    """Find tasks due within N days that are not done."""
    results = []
    for t in tasks:
        days = days_until_due(t)
        if days is not None and 0 <= days <= within_days:
            status = t.status.value if hasattr(t.status, "value") else t.status
            if status != "done":
                results.append(t)
    return results


def overdue_tasks(tasks) -> List:
    """Return all overdue tasks."""
    return [t for t in tasks if is_overdue(t)]


def due_summary(tasks) -> dict:
    """Generate a summary of due date status across tasks."""
    overdue = overdue_tasks(tasks)
    soon = due_soon(tasks, within_days=3)
    no_due = [t for t in tasks if not getattr(t, "due_date", None)]
    has_due_not_overdue = [
        t for t in tasks
        if getattr(t, "due_date", None)
        and t not in overdue
        and t not in soon
    ]
    return {
        "overdue": len(overdue),
        "due_soon": len(soon),
        "on_track": len(has_due_not_overdue),
        "no_due_date": len(no_due),
        "total": len(tasks),
    }


def remove_due_date(task) -> None:
    """Remove the due date from a task."""
    if hasattr(task, "due_date"):
        task.due_date = None


def reschedule(task, new_date: str) -> None:
    """Reschedule a task's due date and record the change."""
    old = getattr(task, "due_date", None)
    set_due_date(task, new_date)
    if not hasattr(task, "reschedule_history") or task.reschedule_history is None:
        task.reschedule_history = []
    task.reschedule_history.append({
        "old": old,
        "new": new,
        "changed_at": _now().isoformat(),
    })


def reschedule_count(task) -> int:
    """Return how many times a task's due date was rescheduled."""
    history = getattr(task, "reschedule_history", None) or []
    return len(history)
