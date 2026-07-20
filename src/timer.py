"""Time tracking for individual tasks."""
from datetime import datetime, timezone


def start_timer(task):
    """Start a timing session on a task."""
    if not hasattr(task, "time_entries") or task.time_entries is None:
        task.time_entries = []
    entry = {"start": datetime.now(timezone.utc).isoformat(), "end": None}
    task.time_entries.append(entry)
    return entry


def stop_timer(task):
    """Stop the most recent active timing session."""
    if not hasattr(task, "time_entries") or not task.time_entries:
        return None
    for entry in reversed(task.time_entries):
        if entry["end"] is None:
            entry["end"] = datetime.now(timezone.utc).isoformat()
            return entry
    return None


def _parse(iso_string):
    return datetime.fromisoformat(iso_string.replace("Z", "+00:00"))


def session_duration(entry):
    """Calculate duration in seconds for a completed session."""
    if not entry.get("end"):
        return 0
    start = _parse(entry["start"])
    end = _parse(entry["end"])
    return (end - start).total_seconds()


def total_time(task):
    """Sum all completed timing sessions in seconds."""
    if not hasattr(task, "time_entries") or not task.time_entries:
        return 0
    return sum(session_duration(e) for e in task.time_entries)


def format_duration(seconds):
    """Format seconds into a human-readable duration string."""
    if seconds <= 0:
        return "0m"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"
