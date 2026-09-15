"""Version tracking for task definitions."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


TRACKED_FIELDS = ["title", "description", "priority", "status",
                  "tags", "assignee", "due_date"]


@dataclass
class Revision:
    """One committed revision of a task."""
    number: int
    changed_fields: Dict = field(default_factory=dict)
    committed_at: str = ""

    def __post_init__(self):
        if not self.committed_at:
            self.committed_at = datetime.now(timezone.utc).isoformat()

    @property
    def change_count(self) -> int:
        return len(self.changed_fields)


class VersionedStore:
    """Stores task dicts with per-task revision history."""
    def __init__(self):
        self._tasks: Dict[int, Dict] = {}
        self._history: Dict[int, List[Revision]] = {}
        self._revisions: Dict[int, int] = {}

    def _snapshot(self, task: Dict) -> Dict:
        snap = {}
        for f in TRACKED_FIELDS:
            v = task.get(f)
            snap[f] = sorted(v) if isinstance(v, list) else v
        return snap

    def create(self, task_id: int, data: Dict) -> int:
        self._tasks[task_id] = dict(data)
        self._revisions[task_id] = 1
        self._history[task_id] = [Revision(number=1,
                                           changed_fields={"__created__": {"new": True}})]
        return 1

    def commit(self, task_id: int, new_data: Dict) -> Optional[int]:
        """Commit changes; bumps revision if any tracked field differs."""
        current = self._tasks.get(task_id)
        if current is None:
            return None
        old_snap = self._snapshot(current)
        new_snap = self._snapshot(new_data)
        changes = {}
        for f in TRACKED_FIELDS:
            if old_snap.get(f) != new_snap.get(f):
                changes[f] = {"old": old_snap.get(f), "new": new_snap.get(f)}
        self._tasks[task_id] = dict(new_data)
        if not changes:
            return self._revisions[task_id]
        self._revisions[task_id] += 1
        rev = Revision(number=self._revisions[task_id], changed_fields=changes)
        self._history[task_id].append(rev)
        return rev.number

    def get(self, task_id: int) -> Optional[Dict]:
        t = self._tasks.get(task_id)
        return dict(t) if t else None

    def revision(self, task_id: int) -> int:
        return self._revisions.get(task_id, 0)

    def history(self, task_id: int) -> List[Revision]:
        return list(self._history.get(task_id, []))

    def last_change(self, task_id: int) -> Optional[Revision]:
        h = self._history.get(task_id)
        return h[-1] if h else None

    def tracked_task_count(self) -> int:
        return len(self._tasks)

    def total_revisions(self) -> int:
        return sum(self._revisions.values())

    def clear(self):
        self._tasks.clear()
        self._history.clear()
        self._revisions.clear()


def versioning_report(store: VersionedStore) -> Dict:
    return {"tracked_tasks": store.tracked_task_count(),
            "total_revisions": store.total_revisions()}
