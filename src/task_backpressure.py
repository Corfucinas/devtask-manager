"""Backpressure handling for slow consumers."""
from typing import Any, Callable, Dict, List, Optional


class DropPolicy:
    BLOCK = "block"          # reject when full
    DROP_OLDEST = "oldest"   # evict oldest to admit newest
    DROP_NEWEST = "newest"   # reject newest when full


class BackpressureQueue:
    """Bounded queue with explicit overflow policies."""
    def __init__(self, capacity: int = 100, high_water: float = 0.8,
                 low_water: float = 0.5, policy: str = DropPolicy.DROP_OLDEST):
        self._capacity = max(1, capacity)
        self._high = high_water
        self._low = low_water
        self._policy = policy
        self._items: List[Any] = []
        self._accepted = 0
        self._rejected = 0
        self._dropped = 0
        self._callbacks: List[Callable] = []

    @property
    def policy(self) -> str:
        return self._policy

    def set_policy(self, policy: str):
        self._policy = policy

    def on_overflow(self, callback: Callable):
        """Register a callback fired when items are dropped/rejected."""
        self._callbacks.append(callback)

    def _fire_overflow(self, item: Any, action: str):
        for cb in self._callbacks:
            try:
                cb(item, action)
            except Exception:
                pass

    def offer(self, item: Any) -> bool:
        """Enqueue an item; returns True if accepted."""
        if len(self._items) >= self._capacity:
            if self._policy == DropPolicy.BLOCK:
                self._rejected += 1
                self._fire_overflow(item, "rejected")
                return False
            elif self._policy == DropPolicy.DROP_OLDEST:
                if self._items:
                    self._items.pop(0)
                    self._dropped += 1
            elif self._policy == DropPolicy.DROP_NEWEST:
                self._rejected += 1
                self._fire_overflow(item, "rejected")
                return False
        self._items.append(item)
        self._accepted += 1
        return True

    def poll(self) -> Any:
        """Dequeue the oldest item; None if empty."""
        if self._items:
            return self._items.pop(0)
        return None

    def peek(self) -> Any:
        return self._items[0] if self._items else None

    def drain(self, n: int = None) -> List[Any]:
        """Dequeue up to n items (all if None)."""
        count = len(self._items) if n is None else min(n, len(self._items))
        out = [self._items.pop(0) for _ in range(count)]
        return out

    def size(self) -> int:
        return len(self._items)

    def is_empty(self) -> bool:
        return len(self._items) == 0

    def is_full(self) -> bool:
        return len(self._items) >= self._capacity

    def high_water_reached(self) -> bool:
        """True when fill ratio >= high water mark."""
        return len(self._items) / self._capacity >= self._high

    def below_low_water(self) -> bool:
        """True when fill ratio <= low water mark."""
        return len(self._items) / self._capacity <= self._low

    def fill_ratio(self) -> float:
        return round(len(self._items) / self._capacity, 3)

    def stats(self) -> Dict:
        return {"size": self.size(), "capacity": self._capacity,
                "accepted": self._accepted, "rejected": self._rejected,
                "dropped": self._dropped, "fill_ratio": self.fill_ratio(),
                "high_water": self._high, "low_water": self._low}

    def clear(self):
        self._items.clear()
        self._accepted = 0
        self._rejected = 0
        self._dropped = 0
