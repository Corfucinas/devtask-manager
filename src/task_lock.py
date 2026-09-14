"""Advisory locks for coordinated task access."""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional


@dataclass
class LockInfo:
    """Metadata about a held lock."""
    name: str
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


class LockManager:
    """Named advisory locks with TTL-based expiry."""
    def __init__(self, default_ttl: int = 300):
        self._locks: Dict[str, LockInfo] = {}
        self._default_ttl = default_ttl

    def acquire(self, name: str, owner: str = "", ttl: int = None) -> bool:
        """Acquire a named lock; fails if held (unless expired)."""
        existing = self._locks.get(name)
        if existing and not existing.is_expired:
            return False
        ttl = ttl if ttl is not None else self._default_ttl
        expires = None
        if ttl > 0:
            expires = (datetime.now(timezone.utc) + timedelta(seconds=ttl)).isoformat()
        self._locks[name] = LockInfo(name=name, owner=owner, expires_at=expires)
        return True

    def release(self, name: str, owner: str = None) -> bool:
        """Release a lock (optionally only if owned)."""
        lock = self._locks.get(name)
        if not lock:
            return False
        if owner is not None and lock.owner != owner:
            return False
        del self._locks[name]
        return True

    def is_locked(self, name: str) -> bool:
        lock = self._locks.get(name)
        if lock and lock.is_expired:
            del self._locks[name]
            return False
        return lock is not None

    def get_lock(self, name: str) -> Optional[LockInfo]:
        return self._locks.get(name)

    def held_locks(self) -> List[LockInfo]:
        self._purge_expired()
        return list(self._locks.values())

    def force_release(self, name: str) -> bool:
        if name in self._locks:
            del self._locks[name]
            return True
        return False

    def _purge_expired(self):
        expired = [n for n, l in self._locks.items() if l.is_expired]
        for n in expired:
            del self._locks[n]

    def clear(self):
        self._locks.clear()

    def lock_count(self) -> int:
        self._purge_expired()
        return len(self._locks)


def lock_report(mgr: LockManager) -> Dict:
    return {"held": mgr.lock_count(),
            "locks": [{"name": l.name, "owner": l.owner} for l in mgr.held_locks()]}
