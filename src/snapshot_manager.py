"""Snapshot manager and timeline playback."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class Snapshot:
    """A point-in-time snapshot of project state."""
    id: int
    timestamp: str
    state: Dict[str, Any] = field(default_factory=dict)
    label: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def get(self, key, default=None):
        return self.state.get(key, default)

    def keys(self):
        return sorted(self.state.keys())

    def task_count(self):
        return self.get("task_count", 0)

    def done_count(self):
        return self.get("done_count", 0)

    def completion_rate(self):
        total = self.task_count()
        if total == 0:
            return 0.0
        return round(self.done_count() / total * 100, 1)


class SnapshotManager:
    """Manages project snapshots over time."""
    def __init__(self, max_snapshots=100):
        self._snapshots = []
        self._next_id = 1
        self._max_snapshots = max_snapshots

    def capture(self, state, label="", metadata=None):
        snapshot = Snapshot(id=self._next_id, state=dict(state), label=label,
                            metadata=metadata or {})
        self._snapshots.append(snapshot)
        self._next_id += 1
        if len(self._snapshots) > self._max_snapshots:
            self._snapshots.pop(0)
        return snapshot

    def get(self, snapshot_id):
        for s in self._snapshots:
            if s.id == snapshot_id:
                return s
        return None

    def latest(self):
        return self._snapshots[-1] if self._snapshots else None

    def oldest(self):
        return self._snapshots[0] if self._snapshots else None

    def all_snapshots(self):
        return list(self._snapshots)

    def count(self):
        return len(self._snapshots)

    def at_time(self, timestamp):
        target = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        result = None
        for s in self._snapshots:
            snap_time = datetime.fromisoformat(s.timestamp.replace("Z", "+00:00"))
            if snap_time <= target:
                result = s
            else:
                break
        return result

    def between(self, start_timestamp, end_timestamp):
        start_dt = datetime.fromisoformat(start_timestamp.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_timestamp.replace("Z", "+00:00"))
        results = []
        for s in self._snapshots:
            snap_time = datetime.fromisoformat(s.timestamp.replace("Z", "+00:00"))
            if start_dt <= snap_time <= end_dt:
                results.append(s)
        return results

    def playback(self, start_id=None, end_id=None):
        snapshots = self.all_snapshots()
        if start_id is not None:
            snapshots = [s for s in snapshots if s.id >= start_id]
        if end_id is not None:
            snapshots = [s for s in snapshots if s.id <= end_id]
        return snapshots

    def clear(self):
        self._snapshots = []
        self._next_id = 1


def diff_snapshots(snap_a, snap_b):
    changes = {}
    all_keys = set(snap_a.keys()) | set(snap_b.keys())
    for key in all_keys:
        val_a = snap_a.get(key)
        val_b = snap_b.get(key)
        if val_a != val_b:
            changes[key] = {"from": val_a, "to": val_b}
    return {"snapshot_a": snap_a.id, "snapshot_b": snap_b.id,
            "changed_fields": len(changes), "changes": changes}


def snapshot_timeline(manager):
    return [{"id": s.id, "timestamp": s.timestamp, "label": s.label,
             "task_count": s.task_count(), "done_count": s.done_count(),
             "completion_rate": s.completion_rate()}
            for s in manager.all_snapshots()]


def snapshot_report(manager):
    snapshots = manager.all_snapshots()
    if not snapshots:
        return {"total_snapshots": 0, "latest": None, "oldest": None}
    first = snapshots[0]
    last = snapshots[-1]
    diff = diff_snapshots(first, last) if len(snapshots) >= 2 else {"changed_fields": 0}
    return {"total_snapshots": len(snapshots),
            "first_snapshot": {"id": first.id, "timestamp": first.timestamp},
            "latest_snapshot": {"id": last.id, "timestamp": last.timestamp},
            "total_changes": diff["changed_fields"],
            "timeline": snapshot_timeline(manager)}


def auto_snapshot(manager, tasks, label=""):
    total = len(tasks)
    done = sum(1 for t in tasks
               if (t.status.value if hasattr(t.status, "value") else t.status) == "done")
    in_progress = sum(1 for t in tasks
                      if (t.status.value if hasattr(t.status, "value") else t.status) == "in-progress")
    todo = sum(1 for t in tasks
               if (t.status.value if hasattr(t.status, "value") else t.status) == "todo")
    state = {"task_count": total, "done_count": done,
             "in_progress_count": in_progress, "todo_count": todo,
             "completion_rate": round(done / total * 100, 1) if total > 0 else 0.0}
    return manager.capture(state, label=label)
