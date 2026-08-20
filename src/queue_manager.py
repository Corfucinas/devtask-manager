"""Task queue manager with priority ordering."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional
import heapq


PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


@dataclass
class QueueItem:
    """A single item in the task queue."""
    task_id: int
    priority: str = "medium"
    created_at: str = ""
    sequence: int = 0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    @property
    def sort_key(self):
        return (PRIORITY_ORDER.get(self.priority, 2), self.sequence)


class TaskQueue:
    """Priority-ordered task queue."""
    def __init__(self):
        self._items: List[QueueItem] = []
        self._counter = 0
        self._dequeued: List[QueueItem] = []

    def enqueue(self, task_id, priority="medium"):
        """Add a task to the queue."""
        item = QueueItem(task_id=task_id, priority=priority, sequence=self._counter)
        self._counter += 1
        heapq.heappush(self._items, (item.sort_key, item))
        return item

    def dequeue(self):
        """Remove and return the highest-priority item."""
        if not self._items:
            return None
        _, item = heapq.heappop(self._items)
        self._dequeued.append(item)
        return item

    def peek_next(self):
        """See the next item without removing it."""
        if not self._items:
            return None
        return self._items[0][1]

    def remove(self, task_id):
        """Remove a specific task from the queue."""
        before = len(self._items)
        self._items = [(k, i) for k, i in self._items if i.task_id != task_id]
        heapq.heapify(self._items)
        return len(self._items) < before

    def size(self):
        return len(self._items)

    def is_empty(self):
        return len(self._items) == 0

    def all_items(self):
        return sorted([i for _, i in self._items], key=lambda x: x.sort_key)

    def by_priority(self, priority):
        return [i for _, i in self._items if i.priority == priority]

    def clear(self):
        self._items = []
        self._dequeued = []
        self._counter = 0

    def dequeued_count(self):
        return len(self._dequeued)

    def requeue(self, task_id, priority=None):
        """Move a dequeued item back into the queue."""
        for item in self._dequeued:
            if item.task_id == task_id:
                self._dequeued.remove(item)
                if priority:
                    item.priority = priority
                item.sequence = self._counter
                self._counter += 1
                heapq.heappush(self._items, (item.sort_key, item))
                return True
        return False


def queue_stats(queue):
    """Generate queue statistics."""
    items = queue.all_items()
    return {
        "size": queue.size(),
        "dequeued": queue.dequeued_count(),
        "by_priority": {p: len(queue.by_priority(p)) for p in ("critical", "high", "medium", "low")},
        "next_task": queue.peek_next().task_id if queue.peek_next() else None,
    }
