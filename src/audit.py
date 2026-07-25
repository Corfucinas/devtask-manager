"""Audit log trail for task changes."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class AuditEntry:
    """A single audit log entry recording a task change."""
    id: int
    task_id: int
    action: str
    actor: str
    timestamp: str = ""
    before: Optional[dict] = None
    after: Optional[dict] = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class AuditLog:
    """Manages audit entries for task changes."""

    def __init__(self):
        self._entries: List[AuditEntry] = []
        self._next_id = 1

    def log_action(self, task_id: int, action: str, actor: str,
                   before: dict = None, after: dict = None,
                   metadata: dict = None) -> AuditEntry:
        entry = AuditEntry(
            id=self._next_id,
            task_id=task_id,
            action=action,
            actor=actor,
            before=before,
            after=after,
            metadata=metadata or {},
        )
        self._entries.append(entry)
        self._next_id += 1
        return entry

    def audit_trail(self, task_id: int) -> List[AuditEntry]:
        return [e for e in self._entries if e.task_id == task_id]

    def audit_by_actor(self, actor: str) -> List[AuditEntry]:
        return [e for e in self._entries if e.actor == actor]

    def audit_by_action(self, action: str) -> List[AuditEntry]:
        return [e for e in self._entries if e.action == action]

    def recent_entries(self, limit: int = 10) -> List[AuditEntry]:
        return self._entries[-limit:] if limit > 0 else []

    def entries_between(self, start: str, end: str) -> List[AuditEntry]:
        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
        results = []
        for e in self._entries:
            ts = datetime.fromisoformat(e.timestamp.replace("Z", "+00:00"))
            if start_dt <= ts <= end_dt:
                results.append(e)
        return results

    def entry_count(self, task_id: Optional[int] = None) -> int:
        if task_id is None:
            return len(self._entries)
        return sum(1 for e in self._entries if e.task_id == task_id)

    def first_entry(self, task_id: int) -> Optional[AuditEntry]:
        trail = self.audit_trail(task_id)
        return trail[0] if trail else None

    def last_entry(self, task_id: int) -> Optional[AuditEntry]:
        trail = self.audit_trail(task_id)
        return trail[-1] if trail else None

    def to_dict(self) -> List[dict]:
        return [
            {
                "id": e.id,
                "task_id": e.task_id,
                "action": e.action,
                "actor": e.actor,
                "timestamp": e.timestamp,
                "before": e.before,
                "after": e.after,
            }
            for e in self._entries
        ]
