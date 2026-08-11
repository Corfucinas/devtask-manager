"""Velocity tracking and forecasting."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class VelocityPoint:
    """A single data point of velocity for a sprint."""
    sprint_id: int
    sprint_name: str
    planned_points: float = 0.0
    completed_points: float = 0.0
    sprint_number: int = 0


class VelocityTracker:
    """Tracks velocity across sprints."""
    def __init__(self):
        self._points = []
        self._by_sprint = {}

    def record(self, sprint_id, sprint_name, planned_points, completed_points):
        point = VelocityPoint(sprint_id=sprint_id, sprint_name=sprint_name,
                              planned_points=planned_points, completed_points=completed_points,
                              sprint_number=len(self._points) + 1)
        self._points.append(point)
        self._by_sprint[sprint_id] = point
        return point

    def get(self, sprint_id):
        return self._by_sprint.get(sprint_id)

    def all_points(self):
        return list(self._points)

    def count(self):
        return len(self._points)

    def average_velocity(self, last_n=0):
        points = self._points[-last_n:] if last_n > 0 else self._points
        if not points:
            return 0.0
        return round(sum(p.completed_points for p in points) / len(points), 2)

    def average_planned(self, last_n=0):
        points = self._points[-last_n:] if last_n > 0 else self._points
        if not points:
            return 0.0
        return round(sum(p.planned_points for p in points) / len(points), 2)

    def velocity_trend(self):
        if len(self._points) < 2:
            return "stable"
        n = min(len(self._points), 5)
        recent = self._points[-n:]
        first_half = recent[:n // 2]
        second_half = recent[n // 2:]
        avg_first = sum(p.completed_points for p in first_half) / max(len(first_half), 1)
        avg_second = sum(p.completed_points for p in second_half) / max(len(second_half), 1)
        if avg_second > avg_first * 1.1:
            return "increasing"
        elif avg_second < avg_first * 0.9:
            return "decreasing"
        return "stable"

    def forecast(self, future_sprints=3):
        avg = self.average_velocity(last_n=5)
        return [{"sprint_offset": i + 1, "forecasted_velocity": avg,
                 "confidence": "high" if self.count() >= 5 else "low"}
                for i in range(future_sprints)]

    def accuracy(self):
        if not self._points:
            return 0.0
        accuracies = []
        for p in self._points:
            if p.planned_points > 0:
                ratio = min(p.completed_points, p.planned_points) / p.planned_points
                accuracies.append(ratio)
        if not accuracies:
            return 0.0
        return round(sum(accuracies) / len(accuracies) * 100, 1)

    def min_velocity(self):
        if not self._points:
            return 0.0
        return min(p.completed_points for p in self._points)

    def max_velocity(self):
        if not self._points:
            return 0.0
        return max(p.completed_points for p in self._points)

    def standard_deviation(self):
        if len(self._points) < 2:
            return 0.0
        avg = self.average_velocity()
        variance = sum((p.completed_points - avg) ** 2 for p in self._points) / len(self._points)
        return round(variance ** 0.5, 2)


def velocity_report(tracker):
    return {"sprints_tracked": tracker.count(),
            "average_velocity": tracker.average_velocity(),
            "average_planned": tracker.average_planned(),
            "min_velocity": tracker.min_velocity(),
            "max_velocity": tracker.max_velocity(),
            "std_deviation": tracker.standard_deviation(),
            "trend": tracker.velocity_trend(),
            "accuracy": tracker.accuracy(),
            "forecast": tracker.forecast(future_sprints=3),
            "history": [{"sprint": p.sprint_name, "planned": p.planned_points,
                         "completed": p.completed_points,
                         "delta": round(p.completed_points - p.planned_points, 2)}
                        for p in tracker.all_points()]}


def velocity_by_sprint_name(tracker, name):
    point = next((p for p in tracker.all_points() if p.sprint_name == name), None)
    return point.completed_points if point else None


def compare_sprints(tracker, sprint_a, sprint_b):
    a = tracker.get(sprint_a)
    b = tracker.get(sprint_b)
    if not a or not b:
        return {"comparable": False}
    delta = b.completed_points - a.completed_points
    return {"comparable": True,
            "sprint_a": {"id": sprint_a, "velocity": a.completed_points},
            "sprint_b": {"id": sprint_b, "velocity": b.completed_points},
            "delta": round(delta, 2),
            "percent_change": round(delta / max(a.completed_points, 1) * 100, 1)}
