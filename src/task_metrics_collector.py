"""Lightweight metrics collector for task operations."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional
import statistics
import time as time_module


@dataclass
class MetricPoint:
    """A single metric data point."""
    value: float
    timestamp: float
    labels: Dict = field(default_factory=dict)


class MetricsCollector:
    """In-process metrics: counters, gauges, timings."""
    def __init__(self, max_points: int = 1000):
        self._series: Dict[str, List[MetricPoint]] = {}
        self._max_points = max_points

    def _record(self, name: str, value: float, **labels):
        if name not in self._series:
            self._series[name] = []
        pts = self._series[name]
        pts.append(MetricPoint(value=value, timestamp=time_module.time(), labels=labels))
        if len(pts) > self._max_points:
            pts.pop(0)

    def increment(self, name: str, value: float = 1.0, **labels):
        """Record a counter increment."""
        self._record(name, value, **labels)

    def gauge(self, name: str, value: float, **labels):
        """Record a gauge (absolute value)."""
        self._record(name, value, **labels)

    def timing(self, name: str, seconds: float, **labels):
        """Record a timing in seconds."""
        self._record(f"timing.{name}", seconds, **labels)

    def time_it(self, name: str, func: Callable, *args, **kwargs):
        """Time a function call and record it; returns (result, seconds)."""
        start = time_module.time()
        result = func(*args, **kwargs)
        elapsed = time_module.time() - start
        self.timing(name, elapsed)
        return result, elapsed

    def points(self, name: str) -> List[MetricPoint]:
        return list(self._series.get(name, []))

    def values(self, name: str) -> List[float]:
        return [p.value for p in self._series.get(name, [])]

    def sum(self, name: str) -> float:
        return sum(self.values(name))

    def mean(self, name: str) -> float:
        vals = self.values(name)
        return round(statistics.mean(vals), 4) if vals else 0.0

    def median(self, name: str) -> float:
        vals = self.values(name)
        return round(statistics.median(vals), 4) if vals else 0.0

    def series_names(self) -> List[str]:
        return sorted(self._series.keys())

    def point_count(self, name: str = None) -> int:
        if name:
            return len(self._series.get(name, []))
        return sum(len(v) for v in self._series.values())

    def clear(self, name: str = None):
        if name:
            self._series.pop(name, None)
        else:
            self._series.clear()

    def summary(self) -> Dict:
        return {name: {"points": len(pts), "sum": round(self.sum(name), 3),
                       "mean": self.mean(name), "last": pts[-1].value if pts else None}
                for name, pts in sorted(self._series.items())}


def default_collector() -> MetricsCollector:
    return MetricsCollector(max_points=1000)
