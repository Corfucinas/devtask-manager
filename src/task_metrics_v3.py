"""Task metrics dashboard with real-time stats."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class MetricValue:
    """A single metric reading."""
    name: str
    value: float
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class MetricsDashboard:
    """Real-time metrics dashboard for task monitoring."""
    def __init__(self):
        self._metrics: Dict[str, List[MetricValue]] = {}
        self._last_values: Dict[str, MetricValue] = {}

    def record(self, name: str, value: float):
        """Record a metric value."""
        mv = MetricValue(name=name, value=value)
        if name not in self._metrics:
            self._metrics[name] = []
        self._metrics[name].append(mv)
        self._last_values[name] = mv
        return mv

    def get_latest(self, name: str) -> Optional[float]:
        """Get the latest value for a metric."""
        mv = self._last_values.get(name)
        return mv.value if mv else None

    def get_history(self, name: str, limit: int = 0) -> List[MetricValue]:
        """Get history for a metric."""
        history = self._metrics.get(name, [])
        if limit > 0:
            return history[-limit:]
        return list(history)

    def all_metrics(self) -> List[str]:
        """Return all metric names."""
        return sorted(self._metrics.keys())

    def metric_count(self) -> int:
        return len(self._metrics)

    def total_data_points(self) -> int:
        return sum(len(v) for v in self._metrics.values())

    def average(self, name: str) -> float:
        """Calculate average for a metric."""
        history = self._metrics.get(name, [])
        if not history:
            return 0.0
        return round(sum(mv.value for mv in history) / len(history), 2)

    def min_value(self, name: str) -> float:
        history = self._metrics.get(name, [])
        if not history:
            return 0.0
        return min(mv.value for mv in history)

    def max_value(self, name: str) -> float:
        history = self._metrics.get(name, [])
        if not history:
            return 0.0
        return max(mv.value for mv in history)

    def snapshot(self) -> Dict[str, float]:
        """Return current state of all metrics."""
        return {name: mv.value for name, mv in self._last_values.items()}

    def clear(self):
        self._metrics.clear()
        self._last_values.clear()

    def remove(self, name: str) -> bool:
        if name in self._metrics:
            del self._metrics[name]
            self._last_values.pop(name, None)
            return True
        return False


def dashboard_report(dashboard: MetricsDashboard) -> Dict:
    """Generate a formatted dashboard report."""
    metrics = dashboard.all_metrics()
    return {
        "metric_count": dashboard.metric_count(),
        "total_data_points": dashboard.total_data_points(),
        "snapshot": dashboard.snapshot(),
        "averages": {m: dashboard.average(m) for m in metrics},
        "ranges": {m: {"min": dashboard.min_value(m), "max": dashboard.max_value(m)}
                   for m in metrics},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def default_dashboard() -> MetricsDashboard:
    """Create a dashboard with default metrics."""
    d = MetricsDashboard()
    d.record("open_tasks", 0)
    d.record("completed_today", 0)
    d.record("avg_cycle_time", 0)
    d.record("velocity", 0)
    d.record("blocked_count", 0)
    return d
