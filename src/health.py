"""Project health scoring and diagnostics."""
from datetime import datetime, timezone
from typing import Dict, List, Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse(iso_string: str) -> datetime:
    return datetime.fromisoformat(iso_string.replace("Z", "+00:00"))


def _get_status(task) -> str:
    return task.status.value if hasattr(task.status, "value") else task.status


def _get_priority(task) -> str:
    return task.priority.value if hasattr(task.priority, "value") else task.priority


def completion_rate(tasks) -> float:
    """Return percentage of completed tasks (0-100)."""
    if not tasks:
        return 0.0
    done = sum(1 for t in tasks if _get_status(t) == "done")
    return round((done / len(tasks)) * 100, 1)


def stale_ratio(tasks, threshold_days: int = 14) -> float:
    """Return percentage of tasks not updated in N days (0-100)."""
    if not tasks:
        return 0.0
    stale = 0
    for t in tasks:
        updated = getattr(t, "updated_at", None)
        if updated:
            age = (_now() - _parse(updated)).days
            if age >= threshold_days:
                stale += 1
    return round((stale / len(tasks)) * 100, 1)


def overdue_ratio(tasks) -> float:
    """Return percentage of tasks that are overdue (0-100)."""
    if not tasks:
        return 0.0
    overdue = 0
    for t in tasks:
        due = getattr(t, "due_date", None)
        if due and _get_status(t) != "done":
            if _parse(due) < _now():
                overdue += 1
    return round((overdue / len(tasks)) * 100, 1)


def blocked_ratio(tasks) -> float:
    """Return percentage of tasks with active blockers (0-100)."""
    if not tasks:
        return 0.0
    blocked = sum(
        1 for t in tasks
        if hasattr(t, "blockers") and t.blockers
        and any(b.status == "active" for b in t.blockers)
    )
    return round((blocked / len(tasks)) * 100, 1)


def unassigned_ratio(tasks) -> float:
    """Return percentage of tasks with no assignee (0-100)."""
    if not tasks:
        return 0.0
    unassigned = sum(1 for t in tasks if not getattr(t, "assignee", None))
    return round((unassigned / len(tasks)) * 100, 1)


def priority_balance(tasks) -> dict:
    """Return distribution of priorities."""
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for t in tasks:
        p = _get_priority(t)
        if p in counts:
            counts[p] += 1
    return counts


def health_score(tasks) -> float:
    """Calculate overall project health score (0-100)."""
    if not tasks:
        return 100.0

    completion = completion_rate(tasks)
    stale = stale_ratio(tasks)
    overdue = overdue_ratio(tasks)
    blocked = blocked_ratio(tasks)
    unassigned = unassigned_ratio(tasks)

    score = (
        completion * 0.35
        + (100 - stale) * 0.25
        + (100 - overdue) * 0.20
        + (100 - blocked) * 0.10
        + (100 - unassigned) * 0.10
    )
    return round(max(0, min(100, score)), 1)


def health_grade(score: float) -> str:
    """Convert a health score to a letter grade."""
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"


def health_report(tasks) -> dict:
    """Generate a full health diagnostic report."""
    score = health_score(tasks)
    return {
        "total_tasks": len(tasks),
        "health_score": score,
        "grade": health_grade(score),
        "completion_rate": completion_rate(tasks),
        "stale_ratio": stale_ratio(tasks),
        "overdue_ratio": overdue_ratio(tasks),
        "blocked_ratio": blocked_ratio(tasks),
        "unassigned_ratio": unassigned_ratio(tasks),
        "priority_balance": priority_balance(tasks),
        "issues": _identify_issues(tasks),
    }


def _identify_issues(tasks) -> List[str]:
    """Identify specific health issues."""
    issues = []
    if not tasks:
        issues.append("No tasks in the project")
        return issues

    if completion_rate(tasks) < 20:
        issues.append("Low completion rate - many tasks stuck in progress")
    if stale_ratio(tasks) > 50:
        issues.append("High number of stale tasks - consider archiving")
    if overdue_ratio(tasks) > 30:
        issues.append("Many overdue tasks - reschedule or reprioritize")
    if blocked_ratio(tasks) > 20:
        issues.append("Significant blockers - resolve impediments")
    if unassigned_ratio(tasks) > 40:
        issues.append("Many unassigned tasks - assign owners")

    balance = priority_balance(tasks)
    total = sum(balance.values())
    if total > 0 and balance.get("critical", 0) / total > 0.3:
        issues.append("Too many critical-priority tasks - reduce urgency")

    return issues
