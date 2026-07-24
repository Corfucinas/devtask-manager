"""Blocker and impediment tracking."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class Blocker:
    """An impediment blocking task progress."""
    id: int
    description: str
    blocker_type: str = "external"
    status: str = "active"
    resolver: Optional[str] = None
    created_at: str = ""
    resolved_at: Optional[str] = None
    resolution_note: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


def add_blocker(task, description: str, blocker_type: str = "external") -> Blocker:
    """Add a blocker to a task."""
    if not hasattr(task, "blockers") or task.blockers is None:
        task.blockers = []
    blocker_id = max((b.id for b in task.blockers), default=0) + 1
    blocker = Blocker(id=blocker_id, description=description, blocker_type=blocker_type)
    task.blockers.append(blocker)
    return blocker


def resolve_blocker(task, blocker_id: int, resolver: str = "", note: str = "") -> bool:
    """Mark a blocker as resolved."""
    if not hasattr(task, "blockers") or not task.blockers:
        return False
    for b in task.blockers:
        if b.id == blocker_id:
            b.status = "resolved"
            b.resolver = resolver
            b.resolved_at = datetime.now(timezone.utc).isoformat()
            b.resolution_note = note
            return True
    return False


def waive_blocker(task, blocker_id: int, reason: str = "") -> bool:
    """Waive a blocker instead of resolving it."""
    if not hasattr(task, "blockers") or not task.blockers:
        return False
    for b in task.blockers:
        if b.id == blocker_id:
            b.status = "waived"
            b.resolution_note = reason
            return True
    return False


def active_blockers(task) -> List[Blocker]:
    """Return all active (unresolved) blockers on a task."""
    if not hasattr(task, "blockers") or not task.blockers:
        return []
    return [b for b in task.blockers if b.status == "active"]


def is_blocked(task) -> bool:
    """Check if a task has any active blockers."""
    return len(active_blockers(task)) > 0


def all_active_blockers(tasks) -> List[dict]:
    """Find all active blockers across all tasks."""
    results = []
    for task in tasks:
        for b in active_blockers(task):
            results.append({
                "task_id": task.id,
                "blocker_id": b.id,
                "description": b.description,
                "type": b.blocker_type,
                "created_at": b.created_at,
            })
    return results


def blockers_by_type(tasks, blocker_type: str) -> List[dict]:
    """Find all active blockers of a specific type."""
    all_blockers = all_active_blockers(tasks)
    return [b for b in all_blockers if b["type"] == blocker_type]


def blocker_count(task) -> int:
    """Return total number of blockers on a task."""
    if not hasattr(task, "blockers") or not task.blockers:
        return 0
    return len(task.blockers)


def resolution_time(blocker: Blocker) -> float:
    """Calculate time to resolve a blocker in hours."""
    if not blocker.resolved_at:
        return 0.0
    created = datetime.fromisoformat(blocker.created_at.replace("Z", "+00:00"))
    resolved = datetime.fromisoformat(blocker.resolved_at.replace("Z", "+00:00"))
    delta = resolved - created
    return round(delta.total_seconds() / 3600, 1)
