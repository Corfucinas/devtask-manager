"""Task history for tracking changes over time."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class HistoryEntry:
    """A single history entry."""
    id: int
    task_id: int
    action: str  # created, updated, status_changed, assigned, completed, deleted
    actor: str = ""
    timestamp: str = ""
    field_changed: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class TaskHistory:
    """Tracks task change history."""
    def __init__(self, max_entries: int = 5000):
        self._entries: List[HistoryEntry] = []
        self._by_task: Dict[int, List[int]] = {}
        self._next_id = 1
        self._max_entries = max_entries

    def record(self, task_id: int, action: str, actor: str = "",
               field_changed: str = None, old_value=None, new_value=None) -> HistoryEntry:
        """Record a change."""
        entry = HistoryEntry(
            id=self._next_id, task_id=task_id, action=action, actor=actor,
            field_changed=field_changed, old_value=old_value, new_value=new_value)
        self._entries.append(entry)
        if task_id not in self._by_task:
            self._by_task[task_id] = []
        self._by_task[task_id].append(self._next_id)
        self._next_id += 1
        if len(self._entries) > self._max_entries:
            removed = self._entries.pop(0)
            if removed.task_id in self._by_task:
                self._by_task[removed.task_id] = [
                    i for i in self._by_task[removed.task_id] if i != removed.id]
        return entry

    def for_task(self, task_id: int) -> List[HistoryEntry]:
        """Return all history entries for a task."""
        ids = self._by_task.get(task_id, [])
        return [e for e in self._entries if e.id in ids]

    def recent(self, limit: int = 20) -> List[HistoryEntry]:
        """Return most recent entries."""
        return self._entries[-limit:] if limit > 0 else []

    def all_entries(self) -> List[HistoryEntry]:
        return list(self._entries)

    def entry_count(self) -> int:
        return len(self._entries)

    def task_count(self) -> int:
        return len(self._by_task)

    def by_action(self, action: str) -> List[HistoryEntry]:
        """Return entries for a specific action."""
        return [e for e in self._entries if e.action == action]

    def by_actor(self, actor: str) -> List[HistoryEntry]:
        """Return entries by a specific actor."""
        return [e for e in self._entries if e.actor == actor]

    def actions(self) -> List[str]:
        """Return all unique actions."""
        return sorted(set(e.action for e in self._entries))

    def actors(self) -> List[str]:
        """Return all unique actors."""
        return sorted(set(e.actor for e in self._entries if e.actor))

    def since(self, timestamp: str) -> List[HistoryEntry]:
        """Return entries after a timestamp."""
        try:
            since_dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return [e for e in self._entries
                    if datetime.fromisoformat(e.timestamp.replace("Z", "+00:00")) > since_dt]
        except (ValueError, TypeError):
            return []

    def clear(self):
        self._entries = []
        self._by_task = {}
        self._next_id = 1


def history_report(history: TaskHistory) -> Dict:
    """Generate a history report."""
    return {
        "total_entries": history.entry_count(),
        "tracked_tasks": history.task_count(),
        "actions": history.actions(),
        "actors": history.actors(),
        "by_action": {a: len(history.by_action(a)) for a in history.actions()},
        "by_actor": {a: len(history.by_actor(a)) for a in history.actors()},
    }


def default_history() -> TaskHistory:
    """Create a default history."""
    return TaskHistory(max_entries=5000)
