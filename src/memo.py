"""Memoization layer for repeated task computations.

Adds a memoization layer keyed by computation input.

- get-or-compute semantics
- invalidation by key
- hit/miss stats
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class MemoEntry:
    """One record inside the memo."""
    id: int
    value: float = 0.0
    note: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


class Memo:
    """Manages memo records."""

    def __init__(self, max_entries: int = 1000):
        self._entries: Dict[int, MemoEntry] = {}
        self._next_id = 1
        self._max = max_entries

    def memoize(self, key: str, compute) -> object:
        """Return cached value or compute, cache, and return."""
        hit = self._entries.get(hash(key) % self._max)
        if hit is not None and hit.note == key:
            return hit.value
        val = compute()
        self._entries[self._next_id] = MemoEntry(id=self._next_id, value=1.0, note=key)
        self._next_id += 1
        return val

    def invalidate(self, key: str) -> bool:
        """Drop a memoized key."""
        ids = [i for i, e in self._entries.items() if e.note == key]
        for i in ids:
            del self._entries[i]
        return bool(ids)

    def count(self) -> int:
        return len(self._entries)


def memo_report(store: Memo) -> Dict:
    """Summary report for the memo."""
    return {"total": store.count(),
            "capacity": store._max,
            "utilization": round(store.count() / max(store._max, 1) * 100, 1)}
