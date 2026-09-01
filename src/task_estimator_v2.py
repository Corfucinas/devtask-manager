"""Enhanced task estimator with multi-model prediction."""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Callable, Dict, List, Optional
import statistics


class EstimationModel(Enum):
    """Estimation models for task completion time."""
    ANALOGOUS = "analogous"      # based on similar past tasks
    PARAMETRIC = "parametric"    # formula: points * rate
    EXPERT = "expert"            # human-adjusted estimates
    CONSENSUS = "consensus"      # average of multiple models
    RISK_ADJUSTED = "risk_adjusted"  # base + risk buffer


@dataclass
class Estimate:
    """A complete estimate for a task."""
    task_id: int
    model: str
    optimistic: float  # best case (hours)
    likely: float      # most likely (hours)
    pessimistic: float # worst case (hours)
    expected: float    # weighted average
    confidence: float  # 0-1
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.expected:
            self.expected = self._compute_expected()

    def _compute_expected(self):
        """PERT: (optimistic + 4*likely + pessimistic) / 6"""
        return round((self.optimistic + 4 * self.likely + self.pessimistic) / 6, 1)


class TaskEstimatorV2:
    """Enhanced estimator with multiple models."""
    def __init__(self):
        self._history: List[dict] = []
        self._estimates: List[Estimate] = []
        self._accuracy: Dict[str, List[float]] = {}

    def add_historical(self, task_id, priority, story_points, tags, actual_hours):
        """Add historical completion data."""
        entry = {"task_id": task_id, "priority": priority,
                 "story_points": story_points, "tags": tags or [],
                 "actual_hours": actual_hours}
        self._history.append(entry)
        return entry

    def record_estimate(self, task_id, model, optimistic, likely, pessimistic, confidence=0.5):
        """Record a new estimate."""
        est = Estimate(task_id=task_id, model=model, optimistic=optimistic,
                       likely=likely, pessimistic=pessimistic, confidence=confidence)
        self._estimates.append(est)
        return est

    def estimate(self, task, model=EstimationModel.PARAMETRIC):
        """Estimate completion time using a specific model."""
        story_points = getattr(task, "story_points", None) or 3
        priority = getattr(task, "priority", None)
        pval = priority.value if hasattr(priority, "value") else priority

        if model == EstimationModel.ANALOGOUS:
            return self._analogous_estimate(task, story_points, pval)
        elif model == EstimationModel.PARAMETRIC:
            return self._parametric_estimate(task, story_points, pval)
        elif model == EstimationModel.EXPERT:
            return self._expert_estimate(task, story_points, pval)
        elif model == EstimationModel.RISK_ADJUSTED:
            return self._risk_adjusted_estimate(task, story_points, pval)
        elif model == EstimationModel.CONSENSUS:
            return self._consensus_estimate(task, story_points, pval)
        return self._parametric_estimate(task, story_points, pval)

    def _parametric_estimate(self, task, story_points, priority):
        """Formula-based estimate."""
        rate = {"critical": 2.0, "high": 3.0, "medium": 4.0, "low": 6.0}.get(priority, 4.0)
        likely = story_points * rate
        return Estimate(
            task_id=getattr(task, "id", 0), model="parametric",
            optimistic=round(likely * 0.7, 1), likely=round(likely, 1),
            pessimistic=round(likely * 1.5, 1),
            confidence=0.6,
        )

    def _analogous_estimate(self, task, story_points, priority):
        """Estimate based on similar past tasks."""
        similar = [h for h in self._history
                   if h["priority"] == priority and
                   abs(h["story_points"] - story_points) <= 2]
        if not similar:
            return self._parametric_estimate(task, story_points, priority)
        avg = statistics.median(h["actual_hours"] for h in similar)
        std = statistics.stdev([h["actual_hours"] for h in similar]) if len(similar) > 1 else avg * 0.3
        return Estimate(
            task_id=getattr(task, "id", 0), model="analogous",
            optimistic=round(avg - std, 1), likely=round(avg, 1),
            pessimistic=round(avg + std, 1),
            confidence=min(len(similar) / 10, 1.0),
        )

    def _expert_estimate(self, task, story_points, priority):
        """Expert-adjusted estimate (higher for complex/new work)."""
        base = story_points * 5
        tags = set(getattr(task, "tags", []) or [])
        if "research" in tags: base *= 1.8
        if "new" in tags: base *= 1.5
        if "bug" in tags: base *= 0.8
        return Estimate(
            task_id=getattr(task, "id", 0), model="expert",
            optimistic=round(base * 0.6, 1), likely=round(base, 1),
            pessimistic=round(base * 2.0, 1),
            confidence=0.7,
        )

    def _risk_adjusted_estimate(self, task, story_points, priority):
        """Estimate with risk buffer."""
        risk = {"critical": 0.4, "high": 0.3, "medium": 0.2, "low": 0.1}.get(priority, 0.2)
        base = story_points * 4
        buffered = base * (1 + risk)
        return Estimate(
            task_id=getattr(task, "id", 0), model="risk_adjusted",
            optimistic=round(base, 1), likely=round(buffered, 1),
            pessimistic=round(buffered * 1.3, 1),
            confidence=0.65,
            pessimistic=round(buffered * 1.3, 1),
        )

    def _consensus_estimate(self, task, story_points, priority):
        """Average of all models."""
        estimates = [self._parametric_estimate(task, story_points, priority),
                     self._expert_estimate(task, story_points, priority),
                     self._risk_adjusted_estimate(task, story_points, priority)]
        avg_likely = statistics.mean(e.likely for e in estimates)
        return Estimate(
            task_id=getattr(task, "id", 0), model="consensus",
            optimistic=round(statistics.mean(e.optimistic for e in estimates), 1),
            likely=round(avg_likely, 1),
            pessimistic=round(statistics.mean(e.pessimistic for e in estimates), 1),
            confidence=0.75,
        )

    def all_estimates(self):
        return list(self._estimates)

    def estimate_count(self):
        return len(self._estimates)

    def history_count(self):
        return len(self._history)

    def accuracy_by_model(self):
        """Calculate accuracy per model."""
        result = {}
        for model in EstimationModel:
            estimates = [e for e in self._estimates if e.model == model.value]
            if estimates:
                result[model.value] = len(estimates)
        return result

    def compare_models(self, task) -> Dict[str, Estimate]:
        """Compare estimates across all models."""
        return {m.value: self.estimate(task, m) for m in EstimationModel}


def estimation_report(estimator):
    """Generate a comprehensive estimation report."""
    estimates = estimator.all_estimates()
    if not estimates:
        return {"total": 0}
    return {
        "total_estimates": len(estimates),
        "history_size": estimator.history_count(),
        "by_model": estimator.accuracy_by_model(),
        "avg_expected": round(statistics.mean(e.expected for e in estimates), 1),
        "avg_confidence": round(statistics.mean(e.confidence for e in estimates), 2),
        "range": {
            "min_expected": min(e.expected for e in estimates),
            "max_expected": max(e.expected for e in estimates),
        },
    }


def default_estimator():
    """Create an estimator with sample data."""
    e = TaskEstimatorV2()
    e.add_historical(1, "high", 3, ["bug"], 9.0)
    e.add_historical(2, "medium", 5, ["feature"], 20.0)
    e.add_historical(3, "critical", 8, ["research"], 24.0)
    e.add_historical(4, "low", 2, [], 12.0)
    e.add_historical(5, "medium", 3, ["bug"], 12.0)
    return e
