"""Persistent snapshot store for task states."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class StoredSnapshot:
    """A named snapshot of state."""
    name: str
    state: Dict[str, Any]
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


class SnapshotStore:
    """Named store for state snapshots with retention limit."""
    def __init__(self, max_snapshots: int = 50):
        self._snapshots: Dict[str, StoredSnapshot] = {}
        self._order: List[str] = []
        self._max = max_snapshots
        self._restore_count = 0

    def save(self, name: str, state: Dict[str, Any]) -> StoredSnapshot:
        if name not in self._snapshots:
            self._order.append(name)
            if len(self._order) > self._max:
                evicted = self._order.pop(0)
                self._snapshots.pop(evicted, None)
        self._snapshots[name] = StoredSnapshot(name=name, state=dict(state))
        return self._snapshots[name]

    def restore(self, name: str) -> Optional[Dict[str, Any]]:
        snap = self._snapshots.get(name)
        if snap:
            self._restore_count += 1
            return dict(snap.state)
        return None

    def get(self, name: str) -> Optional[StoredSnapshot]:
        return self._snapshots.get(name)

    def has(self, name: str) -> bool:
        return name in self._snapshots

    def delete(self, name: str) -> bool:
        if name in self._snapshots:
            del self._snapshots[name]
            if name in self._order:
                self._order.remove(name)
            return True
        return False

    def names(self) -> List[str]:
        return list(self._order)

    def count(self) -> int:
        return len(self._snapshots)

    def restore_count(self) -> int:
        return self._restore_count

    def latest(self) -> Optional[StoredSnapshot]:
        if not self._order:
            return None
        return self._snapshots.get(self._order[-1])

    def oldest(self) -> Optional[StoredSnapshot]:
        if not self._order:
            return None
        return self._snapshots.get(self._order[0])

    def clear(self):
        self._snapshots.clear()
        self._order.clear()
        self._restore_count = 0


def store_report(store: SnapshotStore) -> Dict:
    return {"total_snapshots": store.count(),
            "max_snapshots": store._max,
            "restore_count": store.restore_count(),
            "names": store.names()}
