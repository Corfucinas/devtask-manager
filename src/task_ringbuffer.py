"""Ring buffer for bounded event history."""
from dataclasses import dataclass
from typing import Any, Generic, List, Optional, TypeVar

T = TypeVar("T")


class RingBuffer(Generic[T]):
    """Fixed-size circular buffer; overwrites oldest on overflow."""
    def __init__(self, capacity: int = 100):
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self._capacity = capacity
        self._items: List[Optional[T]] = [None] * capacity
        self._head = 0  # index of oldest
        self._size = 0

    @property
    def capacity(self) -> int:
        return self._capacity

    def append(self, item: T):
        """Add an item, overwriting the oldest if full."""
        idx = (self._head + self._size) % self._capacity
        self._items[idx] = item
        if self._size < self._capacity:
            self._size += 1
        else:
            self._head = (self._head + 1) % self._capacity

    def get(self, index: int) -> Optional[T]:
        """Get item by insertion order (0 = oldest)."""
        if index < 0 or index >= self._size:
            return None
        return self._items[(self._head + index) % self._capacity]

    def latest(self) -> Optional[T]:
        """Return the most recently added item."""
        if self._size == 0:
            return None
        return self.get(self._size - 1)

    def oldest(self) -> Optional[T]:
        return self.get(0) if self._size else None

    def to_list(self) -> List[T]:
        """Return items oldest-to-newest."""
        return [self.get(i) for i in range(self._size)]

    def recent(self, n: int) -> List[T]:
        """Return the last n items oldest-to-newest."""
        n = min(n, self._size)
        return [self.get(self._size - n + i) for i in range(n)]

    def __len__(self) -> int:
        return self._size

    def __iter__(self):
        for i in range(self._size):
            yield self.get(i)

    def is_empty(self) -> bool:
        return self._size == 0

    def is_full(self) -> bool:
        return self._size == self._capacity

    def clear(self):
        self._items = [None] * self._capacity
        self._head = 0
        self._size = 0


def ring_stats(buf: RingBuffer) -> Dict:
    return {"size": len(buf), "capacity": buf.capacity,
            "is_full": buf.is_full(), "is_empty": buf.is_empty(),
            "utilization": round(len(buf) / buf.capacity * 100, 1)}
