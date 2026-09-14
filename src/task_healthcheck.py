"""Health check for task subsystems."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional


class HealthStatus:
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class CheckResult:
    """Result of a single subsystem check."""
    name: str
    status: str
    message: str = ""
    duration_ms: float = 0.0
    checked_at: str = ""

    def __post_init__(self):
        if not self.checked_at:
            self.checked_at = datetime.now(timezone.utc).isoformat()

    @property
    def is_healthy(self) -> bool:
        return self.status == HealthStatus.HEALTHY


class HealthCheck:
    """Registry of subsystem health checks."""
    def __init__(self):
        self._checks: Dict[str, Callable[[], bool]] = {}
        self._last_results: Dict[str, CheckResult] = {}

    def register(self, name: str, check: Callable[[], bool]):
        """Register a check: returns True=healthy, False=unhealthy."""
        self._checks[name] = check

    def unregister(self, name: str) -> bool:
        if name in self._checks:
            del self._checks[name]
            self._last_results.pop(name, None)
            return True
        return False

    def run_check(self, name: str) -> Optional[CheckResult]:
        """Run a single check by name."""
        check = self._checks.get(name)
        if not check:
            return None
        start = datetime.now(timezone.utc)
        try:
            healthy = bool(check())
        except Exception as e:
            healthy = False
            message = f"error: {e}"
        else:
            message = "ok" if healthy else "check returned false"
        duration = (datetime.now(timezone.utc) - start).total_seconds() * 1000
        result = CheckResult(name=name,
                              status=HealthStatus.HEALTHY if healthy else HealthStatus.UNHEALTHY,
                              message=message, duration_ms=round(duration, 2))
        self._last_results[name] = result
        return result

    def run_all(self) -> List[CheckResult]:
        """Run every registered check."""
        return [self.run_check(name) for name in sorted(self._checks.keys())]

    def overall_status(self) -> str:
        """Aggregate: healthy if all pass, else unhealthy."""
        results = self.run_all()
        if not results:
            return HealthStatus.HEALTHY
        all_healthy = all(r.is_healthy for r in results)
        return HealthStatus.HEALTHY if all_healthy else HealthStatus.UNHEALTHY

    def last_result(self, name: str) -> Optional[CheckResult]:
        return self._last_results.get(name)

    def last_results(self) -> Dict[str, CheckResult]:
        return dict(self._last_results)

    def check_names(self) -> List[str]:
        return sorted(self._checks.keys())

    def check_count(self) -> int:
        return len(self._checks)

    def report(self) -> Dict:
        results = self.run_all()
        return {"overall": self.overall_status(),
                "checks": [{"name": r.name, "status": r.status,
                             "message": r.message, "duration_ms": r.duration_ms}
                            for r in results]}


def default_healthcheck() -> HealthCheck:
    """Health check with trivial always-true defaults."""
    hc = HealthCheck()
    hc.register("storage", lambda: True)
    hc.register("sync", lambda: True)
    hc.register("notifications", lambda: True)
    return hc
