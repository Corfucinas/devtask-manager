"""Task assignment and delegation to team members."""
from datetime import datetime, timezone


def assign_task(task, user: str) -> None:
    """Assign a task to a user, recording the assignment time."""
    old = getattr(task, "assignee", None)
    task.assignee = user
    task.assigned_at = datetime.now(timezone.utc).isoformat()
    if not hasattr(task, "assignment_history") or task.assignment_history is None:
        task.assignment_history = []
    task.assignment_history.append({
        "user": user,
        "assigned_at": task.assigned_at,
        "previous": old,
    })


def unassign_task(task) -> None:
    """Remove the current assignment from a task."""
    task.assignee = None
    task.assigned_at = None


def workload(tasks, user: str) -> dict:
    """Count open and total tasks assigned to a user."""
    user_tasks = [t for t in tasks if getattr(t, "assignee", None) == user]
    open_count = sum(
        1 for t in user_tasks
        if (t.status.value if hasattr(t.status, "value") else t.status) != "done"
    )
    return {
        "total": len(user_tasks),
        "open": open_count,
        "done": len(user_tasks) - open_count,
    }


def reassign_task(task, new_user: str) -> None:
    """Transfer a task from its current assignee to a new user."""
    assign_task(task, new_user)


def assignment_history(task) -> list:
    """Return the full assignment history for a task."""
    if not hasattr(task, "assignment_history") or not task.assignment_history:
        return []
    return list(task.assignment_history)


def current_assignee(task) -> str:
    """Return the current assignee of a task, or None."""
    return getattr(task, "assignee", None)


def team_workload(tasks, users: list) -> dict:
    """Return workload summary for each user."""
    return {user: workload(tasks, user) for user in users}


def unassigned_tasks(tasks) -> list:
    """Return all tasks with no assignee."""
    return [t for t in tasks if getattr(t, "assignee", None) is None]
