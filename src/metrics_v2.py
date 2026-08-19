"""Extended metrics with custom definitions."""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Dict, List, Optional


@dataclass
class MetricDefinition:
    """A custom metric definition."""
    id: int
    name: str
    metric_type: str  # counter, gauge, histogram, timer
    description: str = ""
    unit: str = ""
    aggregation: str = "sum"  # sum, avg, min, max, count, last

    def aggregate_values(self, values: List[float]) -> float:
        """Aggregate a list of values."""
        if not values:
            return 0.0
        if self.aggregation == "sum":
            return round(sum(values), 4)
        elif self.aggregation == "avg":
            return round(sum(values) / len(values), 4)
        elif self.aggregation == "min":
            return min(values)
        elif self.aggregation == "max":
            return max(values)
        elif self.aggregation == "count":
            return float(len(values))
        elif self.aggregation == "last":
            return values[-1] if values else 0.0
        return round(sum(values), 4)


@dataclass
class MetricPoint:
    """A single metric data point."""
    metric_id: int
    value: float
    timestamp: str = ""
    labels: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class MetricsCollector:
    """Collects and aggregates custom metrics."""
    def __init__(self):
        self._definitions: Dict[int, MetricDefinition] = {}
        self._points: List[MetricPoint] = []
        self._next_id = 1

    def define(self, name, metric_type="gauge", description="", unit="", aggregation="sum"):
        """Define a new metric."""
        d = MetricDefinition(id=self._next_id, name=name, metric_type=metric_type,
                             description=description, unit=unit, aggregation=aggregation)
        self._definitions[self._next_id] = d
        self._next_id += 1
        return d

    def get(self, metric_id):
        return self._definitions.get(metric_id)

    def find_by_name(self, name):
        for d in self._definitions.values():
            if d.name == name:
                return d
        return None

    def record(self, metric_id, value, labels=None):
        """Record a metric value."""
        if metric_id not in self._definitions:
            return None
        point = MetricPoint(metric_id=metric_id, value=value, labels=labels or {})
        self._points.append(point)
        return point

    def record_by_name(self, name, value, labels=None):
        """Record a metric value by name."""
        d = self.find_by_name(name)
        if not d:
            return None
        return self.record(d.id, value, labels)

    def all_points(self):
        return list(self._points)

    def points_for(self, metric_id):
        return [p for p in self._points if p.metric_id == metric_id]

    def all_definitions(self):
        return list(self._definitions.values())

    def count(self):
        return len(self._definitions)

    def point_count(self):
        return len(self._points)

    def aggregate(self, metric_id):
        """Aggregate all values for a metric."""
        d = self.get(metric_id)
        if not d:
            return 0.0
        values = [p.value for p in self.points_for(metric_id)]
        return d.aggregate_values(values)

    def aggregate_all(self):
        """Aggregate all metrics."""
        return {d.name: self.aggregate(d.id) for d in self._definitions.values()}

    def since(self, timestamp):
        """Return points after a timestamp."""
        return [p for p in self._points if p.timestamp > timestamp]

    def clear(self):
        self._points = []


def metrics_report(collector):
    """Generate a full metrics report."""
    return {
        "metric_count": collector.count(),
        "total_points": collector.point_count(),
        "aggregations": collector.aggregate_all(),
        "definitions": [{"name": d.name, "type": d.metric_type,
                         "unit": d.unit, "aggregation": d.aggregation}
                        for d in collector.all_definitions()],
    }


def default_metrics():
    """Create a collector with common default metrics."""
    c = MetricsCollector()
    c.define("tasks_created", "counter", "Tasks created", "count", "sum")
    c.define("tasks_completed", "counter", "Tasks completed", "count", "sum")
    c.define("avg_completion_time", "timer", "Average completion time", "hours", "avg")
    c.define("open_tasks", "gauge", "Currently open tasks", "count", "last")
    c.define("velocity", "gauge", "Team velocity", "points", "avg")
    return c
