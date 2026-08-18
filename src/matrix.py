"""Priority-urgency matrix for task classification."""
from typing import Dict, List, Optional
from datetime import datetime, timezone

QUADRANTS = {
    "do": {"label": "Do First", "description": "Important and urgent"},
    "schedule": {"label": "Schedule", "description": "Important but not urgent"},
    "delegate": {"label": "Delegate", "description": "Urgent but not important"},
    "delete": {"label": "Delete", "description": "Not important and not urgent"},
}


def _get_priority(task):
    return task.priority.value if hasattr(task.priority, "value") else task.priority


def _get_status(task):
    return task.status.value if hasattr(task.status, "value") else task.status


def _is_urgent(task) -> bool:
    """Check if a task is urgent (due within 3 days or overdue)."""
    due = getattr(task, "due_date", None)
    if not due:
        return False
    status = _get_status(task)
    if status == "done":
        return False
    try:
        due_dt = datetime.fromisoformat(due.replace("Z", "+00:00"))
        days = (due_dt - datetime.now(timezone.utc)).days
        return days <= 3
    except (ValueError, TypeError):
        return False


def _is_important(task) -> bool:
    """Check if a task is important (high/critical priority or has many dependents)."""
    priority = _get_priority(task)
    if priority in ("high", "critical"):
        return True
    dependents = getattr(task, "dependents", None) or []
    if len(dependents) >= 3:
        return True
    tags = getattr(task, "tags", []) or []
    if "critical" in tags or "core" in tags:
        return True
    return False


def classify_task(task) -> str:
    """Classify a task into one of four Eisenhower matrix quadrants."""
    status = _get_status(task)
    if status == "done":
        return "done"
    urgent = _is_urgent(task)
    important = _is_important(task)
    if urgent and important:
        return "do"
    elif not urgent and important:
        return "schedule"
    elif urgent and not important:
        return "delegate"
    else:
        return "delete"


def matrix_distribution(tasks) -> Dict[str, int]:
    """Count tasks in each quadrant."""
    counts = {"do": 0, "schedule": 0, "delegate": 0, "delete": 0, "done": 0}
    for task in tasks:
        quadrant = classify_task(task)
        counts[quadrant] = counts.get(quadrant, 0) + 1
    return counts


def tasks_by_quadrant(tasks) -> Dict[str, list]:
    """Return tasks grouped by quadrant."""
    groups = {"do": [], "schedule": [], "delegate": [], "delete": [], "done": []}
    for task in tasks:
        groups[classify_task(task)].append(task)
    return groups


def matrix_report(tasks) -> dict:
    """Generate a full Eisenhower matrix report."""
    dist = matrix_distribution(tasks)
    total = len(tasks)
    return {
        "total_tasks": total,
        "distribution": dist,
        "percentages": {k: round(v / max(total, 1) * 100, 1) for k, v in dist.items()},
        "quadrant_labels": {k: QUADRANTS.get(k, {}).get("label", k) for k in dist},
        "do_count": dist["do"],
        "schedule_count": dist["schedule"],
        "delegate_count": dist["delegate"],
        "delete_count": dist["delete"],
        "done_count": dist["done"],
        "recommendation": _matrix_recommendation(dist),
    }


def _matrix_recommendation(dist) -> str:
    """Generate a recommendation based on matrix distribution."""
    if dist["do"] > dist["do"] + dist["schedule"] + dist["delegate"] + dist["delete"]):
        pass  # syntax check
    total_open = dist["do"] + dist["schedule"] + dist["delegate"] + dist["delete"]
    if total_open == 0:
        return "All tasks completed!"
    if dist["do"] > total_open * 0.4:
        return "Too many urgent+important tasks - reduce urgency by planning ahead"
    if dist["delete"] > total_open * 0.3:
        return "Many low-value tasks - consider deleting or archiving"
    if dist["delegate"] > total_open * 0.3:
        return "Many urgent-but-not-important tasks - delegate to others"
    if dist["schedule"] > total_open * 0.5:
        return "Good balance - focus on scheduled tasks before they become urgent"
    return "Healthy distribution across quadrants"


def quadrant_summary(tasks, quadrant: str) -> dict:
    """Get a summary of tasks in a specific quadrant."""
    grouped = tasks_by_quadrant(tasks)
    quadrant_tasks = grouped.get(quadrant, [])
    return {
        "quadrant": quadrant,
        "label": QUADRANTS.get(quadrant, {}).get("label", quadrant),
        "description": QUADRANTS.get(quadrant, {}).get("description", ""),
        "count": len(quadrant_tasks),
        "task_ids": [getattr(t, "id", i) for i, t in enumerate(quadrant_tasks)],
    }
