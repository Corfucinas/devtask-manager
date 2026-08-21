"""ML-based completion time predictor."""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import statistics


def _get_priority(task):
    return task.priority.value if hasattr(task.priority, "value") else task.priority


@dataclass
class HistoricalData:
    """Historical task completion data."""
    task_id: int
    priority: str
    story_points: float
    tags: List[str] = field(default_factory=list)
    actual_hours: float = 0.0


class CompletionPredictor:
    """Predicts task completion time from historical data."""
    def __init__(self):
        self._history: List[HistoricalData] = []
        self._predictions: List[dict] = []

    def add_historical(self, task_id, priority, story_points, tags, actual_hours):
        """Add historical completion data."""
        data = HistoricalData(task_id=task_id, priority=priority,
                              story_points=story_points, tags=tags or [],
                              actual_hours=actual_hours)
        self._history.append(data)
        return data

    def history_count(self):
        return len(self._history)

    def _hours_per_point(self, priority=None):
        """Calculate average hours per story point from history."""
        data = self._history
        if priority:
            data = [d for d in data if d.priority == priority]
        if not data:
            return 4.0  # default
        rates = [d.actual_hours / max(d.story_points, 1) for d in data if d.story_points > 0]
        if not rates:
            return 4.0
        return statistics.median(rates)

    def _hours_by_priority(self, priority):
        """Average hours for a priority level."""
        matching = [d.actual_hours for d in self._history if d.priority == priority]
        if not matching:
            return {"critical": 8, "high": 16, "medium": 24, "low": 40}.get(priority, 24)
        return statistics.median(matching)

    def predict_completion(self, task):
        """Predict completion time in hours for a task."""
        priority = _get_priority(task)
        story_points = getattr(task, "story_points", None) or getattr(task, "effort_score", None) or 3

        rate = self._hours_per_point(priority)
        point_based = story_points * rate

        priority_avg = self._hours_by_priority(priority)
        predicted = (point_based * 0.6 + priority_avg * 0.4) if self._history else point_based

        tags = set(getattr(task, "tags", []) or [])
        if "research" in tags:
            predicted *= 1.5
        if "bug" in tags:
            predicted *= 0.8
        if "refactor" in tags:
            predicted *= 1.2

        result = {
            "task_id": getattr(task, "id", None),
            "predicted_hours": round(predicted, 1),
            "confidence": round(min(self.history_count() / 20, 1.0) * 100, 1),
            "factors": {
                "story_points": story_points,
                "rate_per_point": round(rate, 2),
                "priority_avg": round(priority_avg, 1),
                "tag_adjustments": {t: v for t, v in
                    [("research", 1.5), ("bug", 0.8), ("refactor", 1.2)]
                    if t in tags},
            },
        }
        self._predictions.append(result)
        return result

    def predict_batch(self, tasks):
        """Predict completion for multiple tasks."""
        return [self.predict_completion(t) for t in tasks]

    def accuracy_score(self, actuals):
        """Calculate prediction accuracy against actual times."""
        if not self._predictions or not actuals:
            return 0.0
        accuracies = []
        for pred, actual in zip(self._predictions, actuals):
            if actual <= 0:
                continue
            ratio = min(pred["predicted_hours"], actual) / max(pred["predicted_hours"], actual)
            accuracies.append(ratio)
        if not accuracies:
            return 0.0
        return round(statistics.mean(accuracies) * 100, 1)

    def predictions(self):
        return list(self._predictions)


def prediction_report(predictor, tasks):
    """Generate a full prediction report."""
    predictions = predictor.predict_batch(tasks)
    return {
        "total_tasks": len(tasks),
        "predictions_made": len(predictions),
        "avg_predicted_hours": round(
            sum(p["predicted_hours"] for p in predictions) / max(len(predictions), 1), 1
        ) if predictions else 0,
        "total_predicted_hours": round(sum(p["predicted_hours"] for p in predictions), 1),
        "avg_confidence": round(
            sum(p["confidence"] for p in predictions) / max(len(predictions), 1), 1
        ) if predictions else 0,
        "history_size": predictor.history_count(),
    }


def default_predictor():
    """Create a predictor with some default historical data."""
    p = CompletionPredictor()
    defaults = [
        (1, "critical", 3, ["bug"], 4),
        (2, "high", 5, ["feature"], 12),
        (3, "medium", 3, ["docs"], 8),
        (4, "low", 2, ["test"], 6),
        (5, "critical", 8, ["research"], 16),
        (6, "high", 5, ["bug"], 10),
    ]
    for task_id, priority, sp, tags, hours in defaults:
        p.add_historical(task_id, priority, sp, tags, hours)
    return p
