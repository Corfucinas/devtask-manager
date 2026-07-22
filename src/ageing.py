"""Task ageing analysis and staleness detection."""
from datetime import datetime, timezone
from typing import List


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse(iso_string: str) -> datetime:
    return datetime.fromisoformat(iso_string.replace("Z", "+00:00"))


def task_age(task) -> int:
    """Return age of task in days since creation."""
    created = getattr(task, "created_at", None)
    if not created:
        return 0
    delta = _now() - _parse(created)
    return max(0, delta.days)


def days_since_update(task) -> int:
    """Return days since the task was last updated."""
    updated = getattr(task, "updated_at", None)
    if not updated:
        return task_age(task)
    delta = _now() - _parse(updated)
    return max(0, delta.days)


def stale_tasks(tasks, threshold: int = 14) -> List:
    """Find tasks not updated in N or more days."""
    return [t for t in tasks if days_since_update(t) >= threshold]


def age_buckets(tasks) -> dict:
    """Group tasks by age ranges: fresh, aging, old, ancient."""
    buckets = {"fresh": [], "aging": [], "old": [], "ancient": []}
    for t in tasks:
        age = task_age(t)
        if age < 7:
            buckets["fresh"].append(t)
        elif age < 30:
            buckets["aging"].append(t)
        elif age < 90:
            buckets["old"].append(t)
        else:
            buckets["ancient"].append(t)
    return buckets


def oldest_task(tasks):
    """Return the task with the greatest age, or None if empty."""
    if not tasks:
        return None
    return max(tasks, key=task_age)


def average_age(tasks) -> float:
    """Calculate mean age in days across all tasks."""
    if not tasks:
        return 0.0
    ages = [task_age(t) for t in tasks]
    return sum(ages) / len(ages)


def ageing_report(tasks) -> dict:
    """Generate a summary report of task ageing."""
    buckets = age_buckets(tasks)
    return {
        "total": len(tasks),
        "average_age_days": round(average_age(tasks), 1),
        "stale_count": len(stale_tasks(tasks)),
        "buckets": {k: len(v) for k, v in buckets.items()},
    }
