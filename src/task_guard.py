"""Task guard for concurrency protection."""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional


@dataclass
class GuardLock:
    """A lock on a task."""
    task_id: int
    owner: str = ""
    acquired_at: str = ""
    expires_at: Optional[str] = None

    def __post_init__(self):
        if not self.acquired_at:
            self.acquired_at = datetime.now(timezone.utc).isoformat()

    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        try:
            exp = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
            return datetime.now(timezone.utc) > exp
        except (ValueError, TypeError):
            return False


class TaskGuard:
    """Prevents conflicting concurrent task updates."""
    def __init__(self, default_ttl_seconds: int = 300):
        self._locks: Dict[int, GuardLock] = {}
        self._ttl = default_ttl_seconds

    def acquire(self, task_id: int, owner: str = "", ttl_seconds: int = None) -> bool:
        """Acquire a lock on a task."""
        existing = self._locks.get(task_id)
        if existing and not existing.is_expired:
            return False
        ttl = ttl_seconds if ttl_seconds is not None else self._ttl
        expires = None
        if ttl > 0:
            expires = (datetime.now(timezone.utc) + timedelta(seconds=ttl)).isoformat()
        self._locks[task_id] = GuardLock(task_id=task_id, owner=owner, expires_at=expires)
        return True

    def release(self, task_id: int, owner: str = None) -> bool:
        """Release a lock (optionally only if owned by owner)."""
        lock = self._locks.get(task_id)
        if not lock:
            return False
        if owner is not None and lock.owner != owner:
            return False
        del self._locks[task_id]
        return True

    def is_locked(self, task_id: int) -> bool:
        """Check if a task is locked (not expired)."""
        lock = self._locks.get(task_id)
        return lock is not None and not lock.is_expired

    def force_release(self, task_id: int) -> bool:
        """Release a lock regardless of owner."""
        if task_id in self._locks:
            del self._locks[task_id]
            return True
        return False

    def get_lock(self, task_id: int) -> Optional[GuardLock]:
        lock = self._locks.get(task_id)
        if lock and lock.is_expired:
            del self._locks[task_id]
            return None
        return lock

    def locked_tasks(self) -> List[int]:
        """Return all currently locked task IDs."""
        self._purge_expired()
        return sorted(self._locks.keys())

    def _purge_expired(self):
        expired = [tid for tid, lock in self._locks.items() if lock.is_expired]
        for tid in expired:
            del self._locks[tid]

    def clear(self):
        self._locks.clear()

    def lock_count(self) -> int:
        self._purge_expired()
        return len(self._locks)


def guard_stats(guard: TaskGuard) -> Dict:
    return {"locked": guard.lock_count(), "default_ttl": guard._ttl}
