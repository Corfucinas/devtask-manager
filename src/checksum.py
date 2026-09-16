"""Checksum-based integrity verification for task data.

Adds content checksums to detect silent task-data corruption.

- add/verify checksums
- corruption detection
- checksum registry
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class ChecksumEntry:
    """One record inside the checksum."""
    id: int
    value: float = 0.0
    note: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


class Checksum:
    """Manages checksum records."""

    def __init__(self, max_entries: int = 1000):
        self._entries: Dict[int, ChecksumEntry] = {}
        self._next_id = 1
        self._max = max_entries

    def add(self, key: str, content: str) -> str:
        """Register content and return its checksum."""
        import hashlib
        digest = hashlib.sha256(content.encode()).hexdigest()[:16]
        self._entries[self._next_id] = ChecksumEntry(id=self._next_id, value=0.0, note=f"{key}:{digest}")
        self._next_id += 1
        return digest

    def verify(self, key: str, content: str) -> bool:
        """Verify content matches its registered checksum."""
        import hashlib
        digest = hashlib.sha256(content.encode()).hexdigest()[:16]
        return any(e.note == f"{key}:{digest}" for e in self._entries.values())

    def count(self) -> int:
        return len(self._entries)


def checksum_report(store: Checksum) -> Dict:
    """Summary report for the checksum."""
    return {"total": store.count(),
            "capacity": store._max,
            "utilization": round(store.count() / max(store._max, 1) * 100, 1)}
