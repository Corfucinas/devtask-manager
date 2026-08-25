"""Enhanced priority queue with weighted scheduling."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional
import heapq


PRIORITY_BASE = {"critical": 0, "high": 10, "medium": 50, "low": 100}


@dataclass
class QueueEntry:
    """A task entry in the priority queue."""
    task_id: int
    base_priority: str = "medium"
    weight: float = 1.0
    enqueued_at: str = ""
    age_seconds: float = 0.0
    sequence: int = 0

    def __post_init__(self):
        if not self.enqueued_at:
            self.enqueued_at = datetime.now(timezone.utc).isoformat()

    @property
    def effective_score(self) -> float:
        """Calculate effective priority score (lower = higher priority)."""
        base = PRIORITY_BASE.get(self.base_priority, 50)
        aging_bonus = min(self.age_seconds / 3600, 20)  # max 20 point bonus from aging
        return (base - aging_bonus) * self.weight


class PriorityQueueV2:
    """Enhanced priority queue with aging and weights."""
    def __init__(self, aging_enabled: bool = True):
        self._entries: List[tuple] = []  # (score, sequence, entry)
        self._counter = 0
        self._aging_enabled = aging_enabled
        self._dequeued: List[QueueEntry] = []
        self._total_enqueued = 0

    def enqueue(self, task_id: int, priority: str = "medium", weight: float = 1.0):
        """Add a task to the queue."""
        entry = QueueEntry(task_id=task_id, base_priority=priority,
                           weight=weight, sequence=self._counter)
        self._counter += 1
        self._total_enqueued += 1
        heapq.heappush(self._entries, (entry.effective_score, entry.sequence, entry))
        return entry

    def dequeue(self) -> Optional[QueueEntry]:
        """Remove and return the highest-priority entry."""
        if not self._entries:
            return None
        _, _, entry = heapq.heappop(self._entries)
        self._dequeued.append(entry)
        return entry

    def peek(self) -> Optional[QueueEntry]:
        """See the next entry without removing it."""
        if not self._entries:
            return None
        return self._entries[0][2]

    def size(self) -> int:
        return len(self._entries)

    def is_empty(self) -> bool:
        return len(self._entries) == 0

    def remove(self, task_id: int) -> bool:
        """Remove a specific task from the queue."""
        before = len(self._entries)
        self._entries = [(s, seq, e) for s, seq, e in self._entries if e.task_id != task_id]
        heapq.heapify(self._entries)
        return len(self._entries) < before

    def update_aging(self):
        """Update age for all entries and re-heapify."""
        now = datetime.now(timezone.utc)
        for i, (score, seq, entry) in enumerate(self._entries):
            try:
                enqueued = datetime.fromisoformat(entry.enqueued_at.replace("Z", "+00:00"))
                entry.age_seconds = (now - enqueued).total_seconds()
            except (ValueError, TypeError):
                pass
            self._entries[i] = (entry.effective_score, entry.sequence, entry)
        heapq.heapify(self._entries)

    def all_entries(self) -> List[QueueEntry]:
        """Return all entries sorted by score."""
        return sorted([e for _, _, e in self._entries], key=lambda e: e.effective_score)

    def by_priority(self, priority: str) -> List[QueueEntry]:
        """Return entries of a specific priority."""
        return [e for _, _, e in self._entries if e.base_priority == priority]

    def clear(self):
        self._entries = []
        self._dequeued = []
        self._counter = 0

    def total_enqueued(self) -> int:
        return self._total_enqueued

    def dequeued_count(self) -> int:
        return len(self._dequeued)


def queue_metrics(queue: PriorityQueueV2) -> Dict:
    """Generate detailed queue metrics."""
    entries = queue.all_entries()
    return {
        "size": queue.size(),
        "total_enqueued": queue.total_enqueued(),
        "dequeued": queue.dequeued_count(),
        "by_priority": {
            p: len(queue.by_priority(p)) for p in ("critical", "high", "medium", "low")
        },
        "next_task": queue.peek().task_id if queue.peek() else None,
        "aging_enabled": queue._aging_enabled,
        "avg_weight": round(
            sum(e.weight for e in entries) / max(len(entries), 1), 2
        ) if entries else 0,
    }


def default_queue() -> PriorityQueueV2:
    """Create a queue with aging enabled."""
    return PriorityQueueV2(aging_enabled=True)
