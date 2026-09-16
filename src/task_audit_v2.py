"""Audit trail with actor attribution."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class AuditEntryV2:
    """A single attributed change."""
    id: int
    task_id: int
    actor: str
    action: str
    before: Any = None
    after: Any = None
    field_name: Optional[str] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class AuditTrail:
    """Append-only audit log with attribution."""
    def __init__(self, max_entries: int = 10000):
        self._entries: List[AuditEntryV2] = []
        self._next_id = 1
        self._max = max_entries

    def record(self, task_id: int, actor: str, action: str,
               before=None, after=None, field_name: str = None) -> AuditEntryV2:
        entry = AuditEntryV2(id=self._next_id, task_id=task_id, actor=actor,
                             action=action, before=before, after=after,
                             field_name=field_name)
        self._entries.append(entry)
        self._next_id += 1
        if len(self._entries) > self._max:
            self._entries.pop(0)
        return entry

    def for_task(self, task_id: int) -> List[AuditEntryV2]:
        return [e for e in self._entries if e.task_id == task_id]

    def by_actor(self, actor: str) -> List[AuditEntryV2]:
        return [e for e in self._entries if e.actor == actor]

    def by_action(self, action: str) -> List[AuditEntryV2]:
        return [e for e in self._entries if e.action == action]

    def latest(self, n: int = 10) -> List[AuditEntryV2]:
        return self._entries[-n:]

    def oldest(self, n: int = 10) -> List[AuditEntryV2]:
        return self._entries[:n]

    def entry_count(self) -> int:
        return len(self._entries)

    def task_count(self) -> int:
        return len({e.task_id for e in self._entries})

    def actors(self) -> List[str]:
        return sorted({e.actor for e in self._entries if e.actor})

    def actions(self) -> List[str]:
        return sorted({e.action for e in self._entries})

    def clear(self):
        self._entries.clear()
        self._next_id = 1


def audit_report(trail: AuditTrail) -> Dict:
    return {"total_entries": trail.entry_count(),
            "tasks_audited": trail.task_count(),
            "actors": trail.actors(),
            "actions": trail.actions(),
            "by_actor": {a: len(trail.by_actor(a)) for a in trail.actors()}}
