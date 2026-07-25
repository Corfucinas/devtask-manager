"""Task synchronization state tracking."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class SyncState:
    """Synchronization state for a task with a remote system."""
    system: str
    remote_id: str
    last_synced: str = ""
    status: str = "synced"
    sync_errors: int = 0
    last_error: Optional[str] = None

    def __post_init__(self):
        if not self.last_synced:
            self.last_synced = datetime.now(timezone.utc).isoformat()


def mark_synced(task, system: str, remote_id: str) -> None:
    if not hasattr(task, "sync_states") or task.sync_states is None:
        task.sync_states = {}
    task.sync_states[system] = SyncState(
        system=system,
        remote_id=remote_id,
        status="synced",
        last_synced=datetime.now(timezone.utc).isoformat(),
    )


def mark_pending(task, system: str) -> None:
    if not hasattr(task, "sync_states") or task.sync_states is None:
        task.sync_states = {}
    if system in task.sync_states:
        task.sync_states[system].status = "pending"
    else:
        task.sync_states[system] = SyncState(
            system=system, remote_id="", status="pending"
        )


def mark_conflict(task, system: str, error: str = "") -> None:
    if hasattr(task, "sync_states") and system in task.sync_states:
        task.sync_states[system].status = "conflict"
        task.sync_states[system].last_error = error


def mark_error(task, system: str, error: str) -> None:
    if hasattr(task, "sync_states") and system in task.sync_states:
        state = task.sync_states[system]
        state.status = "error"
        state.last_error = error
        state.sync_errors += 1


def sync_status(task, system: str) -> Optional[SyncState]:
    states = getattr(task, "sync_states", None) or {}
    return states.get(system)


def is_synced(task, system: str) -> bool:
    state = sync_status(task, system)
    return state is not None and state.status == "synced"


def out_of_sync(tasks, system: str) -> list:
    results = []
    for t in tasks:
        state = sync_status(t, system)
        if state is None or state.status in ("pending", "conflict", "error"):
            results.append(t)
    return results


def synced_tasks(tasks, system: str) -> list:
    return [t for t in tasks if is_synced(t, system)]


def last_sync_time(task, system: str) -> Optional[str]:
    state = sync_status(task, system)
    return state.last_synced if state else None


def needs_resync(task, system: str, max_age_hours: int = 24) -> bool:
    state = sync_status(task, system)
    if not state or state.status != "synced":
        return True
    last = datetime.fromisoformat(state.last_synced.replace("Z", "+00:00"))
    age = (datetime.now(timezone.utc) - last).total_seconds() / 3600
    return age > max_age_hours


def sync_summary(tasks, system: str) -> dict:
    total = len(tasks)
    synced = len(synced_tasks(tasks, system))
    pending_count = sum(
        1 for t in tasks
        if sync_status(t, system) and sync_status(t, system).status == "pending"
    )
    conflict_count = sum(
        1 for t in tasks
        if sync_status(t, system) and sync_status(t, system).status == "conflict"
    )
    error_count = sum(
        1 for t in tasks
        if sync_status(t, system) and sync_status(t, system).status == "error"
    )
    return {
        "system": system,
        "total": total,
        "synced": synced,
        "pending": pending_count,
        "conflicts": conflict_count,
        "errors": error_count,
        "unsynced": total - synced,
    }
