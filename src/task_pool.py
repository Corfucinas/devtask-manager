"""Task pool for pooled task management."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional
import heapq


@dataclass
class PoolItem:
    """An item in the task pool."""
    task_id: int
    checked_out: bool = False
    checked_out_by: Optional[str] = None
    checked_out_at: Optional[str] = None
    added_at: str = ""

    def __post_init__(self):
        if not self.added_at:
            self.added_at = datetime.now(timezone.utc).isoformat()


class TaskPool:
    """Manages a pool of tasks with checkout/checkin semantics."""
    def __init__(self, max_size: int = 100):
        self._pool: Dict[int, PoolItem] = {}
        self._max_size = max_size

    def add(self, task_id: int) -> bool:
        """Add a task to the pool."""
        if len(self._pool) >= self._max_size:
            return False
        if task_id in self._pool:
            return False
        self._pool[task_id] = PoolItem(task_id=task_id)
        return True

    def checkout(self, task_id: int, user: str = "") -> bool:
        """Check out a task (mark as being worked on)."""
        item = self._pool.get(task_id)
        if item and not item.checked_out:
            item.checked_out = True
            item.checked_out_by = user
            item.checked_out_at = datetime.now(timezone.utc).isoformat()
            return True
        return False

    def checkin(self, task_id: int) -> bool:
        """Check a task back into the pool."""
        item = self._pool.get(task_id)
        if item and item.checked_out:
            item.checked_out = False
            item.checked_out_by = None
            item.checked_out_at = None
            return True
        return False

    def remove(self, task_id: int) -> bool:
        """Remove a task from the pool."""
        if task_id in self._pool:
            del self._pool[task_id]
            return True
        return False

    def get(self, task_id: int) -> Optional[PoolItem]:
        return self._pool.get(task_id)

    def available(self) -> List[int]:
        """Return IDs of non-checked-out tasks."""
        return sorted(tid for tid, item in self._pool.items() if not item.checked_out)

    def checked_out(self) -> List[int]:
        return sorted(tid for tid, item in self._pool.items() if item.checked_out)

    def size(self) -> int:
        return len(self._pool)

    def available_count(self) -> int:
        return len(self.available())

    def is_full(self) -> bool:
        return len(self._pool) >= self._max_size

    def clear(self):
        self._pool.clear()


def pool_stats(pool: TaskPool) -> Dict:
    return {"total": pool.size(), "available": pool.available_count(),
            "checked_out": len(pool.checked_out()), "capacity": pool._max_size,
            "utilization": round(pool.size() / max(pool._max_size, 1) * 100, 1)}
