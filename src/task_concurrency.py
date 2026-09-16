"""Concurrency helpers for parallel task processing."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class CountingSemaphore:
    """In-process semaphore to bound parallelism."""
    def __init__(self, permits: int = 1):
        if permits < 1:
            raise ValueError("permits must be >= 1")
        self._permits = permits
        self._available = permits
        self._waiters: List = []   # placeholder FIFO of acquire requests
        self._acquired_count = 0

    @property
    def permits(self) -> int:
        return self._permits

    @property
    def available(self) -> int:
        return self._available

    def acquire(self) -> bool:
        """Take a permit; False if none available (non-blocking)."""
        if self._available > 0:
            self._available -= 1
            self._acquired_count += 1
            return True
        return False

    def release(self) -> bool:
        """Return a permit; False if none outstanding."""
        if self._available < self._permits:
            self._available += 1
            return True
        return False

    def try_acquire_all(self) -> bool:
        """Acquire all remaining permits atomically."""
        if self._available == self._permits:
            self._available = 0
            self._acquired_count += self._permits
            return True
        return False

    def utilization(self) -> float:
        """Fraction of permits currently held."""
        return round((self._permits - self._available) / self._permits, 2)


class PhaseBarrier:
    """Synchronizes named phases: all participants must arrive before advancing."""
    def __init__(self, phases: int, parties: int):
        if parties < 1:
            raise ValueError("parties must be >= 1")
        self._phases = phases
        self._parties = parties
        self._current_phase = 0
        self._arrivals: Dict[int, int] = {}

    @property
    def current_phase(self) -> int:
        return self._current_phase

    def arrive(self, party_id: int) -> bool:
        """Party arrives at the current phase; advances when all arrive."""
        if self._current_phase >= self._phases:
            return False
        count = self._arrivals.get(self._current_phase, 0)
        self._arrivals[self._current_phase] = count + 1
        if self._arrivals[self._current_phase] >= self._parties:
            self._current_phase += 1
            return True
        return False

    def phase_complete(self, phase: int) -> bool:
        return self._arrivals.get(phase, 0) >= self._parties

    def reset(self):
        self._current_phase = 0
        self._arrivals.clear()


class AtomicCounter:
    """Monotonic counter with generation tracking."""
    def __init__(self, start: int = 0):
        self._value = start
        self._increments = 0
        self._decrements = 0

    @property
    def value(self) -> int:
        return self._value

    def increment(self, by: int = 1) -> int:
        self._value += by
        self._increments += 1
        return self._value

    def decrement(self, by: int = 1) -> int:
        self._value -= by
        self._decrements += 1
        return self._value

    def compare_and_set(self, expected: int, new_value: int) -> bool:
        if self._value == expected:
            self._value = new_value
            return True
        return False

    def stats(self) -> Dict:
        return {"value": self._value, "increments": self._increments,
                "decrements": self._decrements}
