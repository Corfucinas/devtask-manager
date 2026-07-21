"""Cycle time, lead time, and throughput metrics."""
from datetime import datetime, timezone
from typing import List


def _parse(iso_string: str) -> datetime:
    """Parse an ISO timestamp string."""
    return datetime.fromisoformat(iso_string.replace("Z", "+00:00"))


def cycle_time(task) -> float:
    """Calculate cycle time (started to done) in hours. Returns 0 if not complete."""
    status = task.status.value if hasattr(task.status, "value") else task.status
    if status != "done":
        return 0.0
    started = getattr(task, "started_at", None)
    completed = getattr(task, "completed_at", None)
    if not started or not completed:
        return 0.0
    delta = _parse(completed) - _parse(started)
    return delta.total_seconds() / 3600


def lead_time(task) -> float:
    """Calculate lead time (created to done) in hours. Returns 0 if not complete."""
    status = task.status.value if hasattr(task.status, "value") else task.status
    if status != "done":
        return 0.0
    created = getattr(task, "created_at", None)
    completed = getattr(task, "completed_at", None)
    if not created or not completed:
        return 0.0
    delta = _parse(completed) - _parse(created)
    return delta.total_seconds() / 3600


def throughput(tasks, days: int = 7) -> int:
    """Count tasks completed in the last N days."""
    now = datetime.now(timezone.utc)
    cutoff = now.timestamp() - (days * 86400)
    count = 0
    for t in tasks:
        status = t.status.value if hasattr(t.status, "value") else t.status
        if status != "done":
            continue
        completed = getattr(t, "completed_at", None)
        if completed and _parse(completed).timestamp() >= cutoff:
            count += 1
    return count


def average_cycle_time(tasks) -> float:
    """Calculate mean cycle time in hours for completed tasks."""
    times = [cycle_time(t) for t in tasks]
    valid = [t for t in times if t > 0]
    if not valid:
        return 0.0
    return sum(valid) / len(valid)


def average_lead_time(tasks) -> float:
    """Calculate mean lead time in hours for completed tasks."""
    times = [lead_time(t) for t in tasks]
    valid = [t for t in times if t > 0]
    if not valid:
        return 0.0
    return sum(valid) / len(valid)


def throughput_by_day(tasks, days: int = 7) -> List[dict]:
    """Return daily completion counts for the last N days."""
    now = datetime.now(timezone.utc)
    results = []
    for i in range(days):
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        day_start = day_start.timestamp() - (i * 86400)
        day_end = day_start + 86400
        count = 0
        for t in tasks:
            status = t.status.value if hasattr(t.status, "value") else t.status
            if status != "done":
                continue
            completed = getattr(t, "completed_at", None)
            if completed:
                ts = _parse(completed).timestamp()
                if day_start <= ts < day_end:
                    count += 1
        results.append({"day_offset": i, "completed": count})
    return results
