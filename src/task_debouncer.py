"""Task debouncer for rate limiting operations."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
import time as time_module


@dataclass
class OperationCall:
    """A record of an operation call."""
    operation: str
    timestamp: float = 0.0
    allowed: bool = True
    wait_seconds: float = 0.0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time_module.time()


class Debouncer:
    """Rate limiting and debouncing for task operations."""
    def __init__(self, min_interval_seconds: float = 1.0, burst_limit: int = 10,
                 window_seconds: float = 60.0):
        self._min_interval = min_interval_seconds
        self._burst_limit = burst_limit
        self._window_seconds = window_seconds
        self._calls: List[OperationCall] = []
        self._last_call_time: Optional[float] = None

    def record(self, operation: str) -> OperationCall:
        """Record an operation call and return whether it was allowed."""
        now = time_module.time()
        call = OperationCall(operation=operation, timestamp=now)

        if self._last_call_time is not None:
            elapsed = now - self._last_call_time
            if elapsed < self._min_interval:
                call.allowed = False
                call.wait_seconds = round(self._min_interval - elapsed, 2)
                self._calls.append(call)
                return call

        # Check burst limit
        cutoff = now - self._window_seconds
        recent = [c for c in self._calls if c.timestamp > cutoff and c.allowed]
        if len(recent) >= self._burst_limit:
            call.allowed = False
            call.wait_seconds = round(self._window_seconds - (now - recent[0].timestamp), 2)
            self._calls.append(call)
            return call

        self._last_call_time = now
        self._calls.append(call)
        return call

    def is_allowed(self, operation: str) -> bool:
        """Check if an operation would be allowed (without recording)."""
        now = time_module.time()
        if self._last_call_time is not None:
            if now - self._last_call_time < self._min_interval:
                return False
        cutoff = now - self._window_seconds
        recent = [c for c in self._calls if c.timestamp > cutoff and c.allowed]
        return len(recent) < self._burst_limit

    def allowed_calls(self, operation: str = None) -> int:
        """Count of allowed calls."""
        calls = self._calls
        if operation:
            calls = [c for c in calls if c.operation == operation]
        return sum(1 for c in calls if c.allowed)

    def denied_calls(self, operation: str = None) -> int:
        """Count of denied calls."""
        calls = self._calls
        if operation:
            calls = [c for c in calls if c.operation == operation]
        return sum(1 for c in calls if not c.allowed)

    def recent_calls(self, seconds: float = 60) -> List[OperationCall]:
        """Return calls within a time window."""
        cutoff = time_module.time() - seconds
        return [c for c in self._calls if c.timestamp > cutoff]

    def all_calls(self) -> List[OperationCall]:
        return list(self._calls)

    def min_interval(self):
        return self._min_interval

    def burst_limit(self):
        return self._burst_limit

    def set_min_interval(self, seconds: float):
        self._min_interval = seconds

    def set_burst_limit(self, limit: int):
        self._burst_limit = limit

    def reset(self):
        self._calls = []
        self._last_call_time = None


def debounce(min_interval: float = 1.0, debouncer: Debouncer = None):
    """Decorator to debounce a function."""
    if debouncer is None:
        debouncer = Debouncer(min_interval_seconds=min_interval)
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            call = debouncer.record(func.__name__)
            if call.allowed:
                return func(*args, **kwargs)
            return None
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator


def debounce_report(debouncer: Debouncer) -> Dict:
    """Generate a debouncing report."""
    all_calls = debouncer.all_calls()
    return {
        "total_calls": len(all_calls),
        "allowed": debouncer.allowed_calls(),
        "denied": debouncer.denied_calls(),
        "allow_rate": round(debouncer.allowed_calls() / max(len(all_calls), 1) * 100, 1),
        "min_interval": debouncer.min_interval,
        "burst_limit": debouncer.burst_limit,
        "window_seconds": debouncer._window_seconds,
        "denied_recent": len([c for c in debouncer.recent_calls(60) if not c.allowed]),
    }


def default_debouncer():
    """Create a default debouncer."""
    return Debouncer(min_interval_seconds=1.0, burst_limit=10, window_seconds=60)
