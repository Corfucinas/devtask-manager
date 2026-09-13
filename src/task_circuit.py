"""Circuit breaker for failing operations."""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Callable, Dict, List, Optional


class BreakerState:
    CLOSED = "closed"        # normal, operations allowed
    OPEN = "open"            # tripped, operations blocked
    HALF_OPEN = "half_open" # probing recovery


@dataclass
class OperationBreaker:
    """Circuit breaker for a single operation."""
    name: str
    failure_threshold: int = 3
    cooldown_seconds: float = 60.0
    state: str = BreakerState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_at: Optional[str] = None
    opened_at: Optional[str] = None

    @property
    def is_open(self) -> bool:
        """Check if breaker blocks operations, accounting for cooldown."""
        if self.state == BreakerState.OPEN:
            if self.opened_at:
                try:
                    opened = datetime.fromisoformat(self.opened_at.replace("Z", "+00:00"))
                    elapsed = (datetime.now(timezone.utc) - opened).total_seconds()
                    if elapsed >= self.cooldown_seconds:
                        self.state = BreakerState.HALF_OPEN
                        return False
                except (ValueError, TypeError):
                    pass
            return True
        return False

    def record_success(self):
        self.success_count += 1
        if self.state in (BreakerState.HALF_OPEN, BreakerState.OPEN):
            self.state = BreakerState.CLOSED
            self.failure_count = 0
            self.opened_at = None

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_at = datetime.now(timezone.utc).isoformat()
        if self.state == BreakerState.HALF_OPEN or self.failure_count >= self.failure_threshold:
            self.state = BreakerState.OPEN
            self.opened_at = datetime.now(timezone.utc).isoformat()

    def reset(self):
        self.state = BreakerState.CLOSED
        self.failure_count = 0
        self.opened_at = None


class CircuitBreaker:
    """Manages circuit breakers per operation."""
    def __init__(self, failure_threshold: int = 3, cooldown_seconds: float = 60.0):
        self._threshold = failure_threshold
        self._cooldown = cooldown_seconds
        self._breakers: Dict[str, OperationBreaker] = {}

    def _get(self, name: str) -> OperationBreaker:
        if name not in self._breakers:
            self._breakers[name] = OperationBreaker(
                name=name, failure_threshold=self._threshold,
                cooldown_seconds=self._cooldown)
        return self._breakers[name]

    def can_execute(self, name: str) -> bool:
        """Check if operation is allowed (breaker not blocking)."""
        return not self._get(name).is_open

    def record_success(self, name: str):
        self._get(name).record_success()

    def record_failure(self, name: str):
        self._get(name).record_failure()

    def execute(self, name: str, func: Callable, *args, **kwargs):
        """Execute an operation through the breaker."""
        if not self.can_execute(name):
            return {"executed": False, "reason": "circuit_open"}
        try:
            result = func(*args, **kwargs)
            self.record_success(name)
            return {"executed": True, "result": result}
        except Exception as e:
            self.record_failure(name)
            return {"executed": False, "reason": "error", "error": str(e)}

    def get_breaker(self, name: str) -> Optional[OperationBreaker]:
        return self._breakers.get(name)

    def all_breakers(self) -> List[OperationBreaker]:
        return list(self._breakers.values())

    def reset(self, name: str = None):
        """Reset one or all breakers."""
        if name:
            b = self._breakers.get(name)
            if b:
                b.reset()
        else:
            for b in self._breakers.values():
                b.reset()

    def breaker_count(self) -> int:
        return len(self._breakers)


def breaker_report(cb: CircuitBreaker) -> Dict:
    return {"total_breakers": cb.breaker_count(),
            "by_operation": {b.name: {"state": b.state, "failures": b.failure_count,
                                      "successes": b.success_count}
                             for b in cb.all_breakers()}}
