"""Crash recovery manager for task state."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class RecoveryCheckpoint:
    """A saved state checkpoint."""
    id: int
    name: str
    state: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
    size: int = 0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        self.size = len(str(self.state))


class RecoveryManager:
    """Manages state checkpoints for crash recovery."""
    def __init__(self, max_checkpoints: int = 20):
        self._checkpoints: Dict[int, RecoveryCheckpoint] = {}
        self._next_id = 1
        self._max_checkpoints = max_checkpoints
        self._restored_count = 0

    def save_checkpoint(self, name: str, state: Dict[str, Any]) -> RecoveryCheckpoint:
        """Save a new checkpoint."""
        checkpoint = RecoveryCheckpoint(id=self._next_id, name=name, state=dict(state))
        self._checkpoints[self._next_id] = checkpoint
        self._next_id += 1
        if len(self._checkpoints) > self._max_checkpoints:
            oldest = min(self._checkpoints.keys())
            del self._checkpoints[oldest]
        return checkpoint

    def restore_checkpoint(self, checkpoint_id: int) -> Optional[Dict[str, Any]]:
        """Restore state from a checkpoint."""
        cp = self._checkpoints.get(checkpoint_id)
        if cp:
            self._restored_count += 1
            return dict(cp.state)
        return None

    def restore_latest(self) -> Optional[Dict[str, Any]]:
        """Restore from the most recent checkpoint."""
        if not self._checkpoints:
            return None
        latest_id = max(self._checkpoints.keys())
        return self.restore_checkpoint(latest_id)

    def get(self, checkpoint_id: int) -> Optional[RecoveryCheckpoint]:
        return self._checkpoints.get(checkpoint_id)

    def all_checkpoints(self) -> List[RecoveryCheckpoint]:
        return sorted(self._checkpoints.values(), key=lambda c: c.id)

    def count(self) -> int:
        return len(self._checkpoints)

    def restored_count(self) -> int:
        return self._restored_count

    def remove(self, checkpoint_id: int) -> bool:
        if checkpoint_id in self._checkpoints:
            del self._checkpoints[checkpoint_id]
            return True
        return False

    def clear(self):
        self._checkpoints.clear()
        self._restored_count = 0

    def latest(self) -> Optional[RecoveryCheckpoint]:
        if not self._checkpoints:
            return None
        return max(self._checkpoints.values(), key=lambda c: c.id)

    def find_by_name(self, name: str) -> Optional[RecoveryCheckpoint]:
        for cp in self._checkpoints.values():
            if cp.name.lower() == name.lower():
                return cp
        return None


def recovery_report(manager: RecoveryManager) -> Dict:
    """Generate a recovery manager report."""
    return {
        "total_checkpoints": manager.count(),
        "restored_count": manager.restored_count(),
        "latest_checkpoint": manager.latest().name if manager.latest() else None,
        "checkpoint_names": [cp.name for cp in manager.all_checkpoints()],
        "max_checkpoints": manager._max_checkpoints,
    }


def auto_save(manager: RecoveryManager, tasks: List, name: str = "auto") -> RecoveryCheckpoint:
    """Auto-save a checkpoint from task list."""
    state = {
        "task_count": len(tasks),
        "task_ids": [getattr(t, "id", i) for i, t in enumerate(tasks)],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return manager.save_checkpoint(name, state)
