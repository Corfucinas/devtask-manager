"""Multi-factor task scoring system."""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Callable, Dict, List, Optional


def _get_priority(task):
    return task.priority.value if hasattr(task.priority, "value") else task.priority


def _get_status(task):
    return task.status.value if hasattr(task.status, "value") else task.status


@dataclass
class ScoringFactor:
    """A single scoring factor with weight and calculator."""
    name: str
    weight: float  # 0-1
    calculator: Callable
    description: str = ""
    min_score: float = 0.0
    max_score: float = 100.0

    def calculate(self, task) -> float:
        """Calculate raw score for a task."""
        try:
            score = self.calculator(task)
            return max(self.min_score, min(self.max_score, score))
        except Exception:
            return 0.0


class TaskScorer:
    """Combines multiple scoring factors into a composite score."""
    def __init__(self):
        self._factors: Dict[str, ScoringFactor] = {}

    def add_factor(self, name, weight, calculator, description="",
                   min_score=0.0, max_score=100.0):
        """Add a scoring factor."""
        factor = ScoringFactor(name=name, weight=weight, calculator=calculator,
                               description=description, min_score=min_score,
                               max_score=max_score)
        self._factors[name] = factor
        return factor

    def remove_factor(self, name) -> bool:
        if name in self._factors:
            del self._factors[name]
            return True
        return False

    def get_factor(self, name) -> Optional[ScoringFactor]:
        return self._factors.get(name)

    def all_factors(self) -> List[ScoringFactor]:
        return list(self._factors.values())

    def count(self) -> int:
        return len(self._factors)

    def total_weight(self) -> float:
        return sum(f.weight for f in self._factors.values())

    def normalize_weights(self):
        """Normalize all weights to sum to 1.0."""
        total = self.total_weight()
        if total <= 0:
            return
        for f in self._factors.values():
            f.weight = round(f.weight / total, 4)

    def score(self, task) -> float:
        """Calculate composite score for a task."""
        if not self._factors:
            return 0.0
        status = _get_status(task)
        if status == "done":
            return 0.0
        total = 0.0
        weight_sum = self.total_weight()
        if weight_sum == 0:
            return 0.0
        for factor in self._factors.values():
            raw = factor.calculate(task)
            total += raw * factor.weight
        return round(total / weight_sum, 2)

    def score_breakdown(self, task) -> Dict:
        """Return individual factor scores."""
        result = {}
        for name, factor in self._factors.items():
            result[name] = {
                "raw_score": round(factor.calculate(task), 2),
                "weight": factor.weight,
                "weighted": round(factor.calculate(task) * factor.weight, 2),
            }
        result["total"] = self.score(task)
        return result

    def rank_tasks(self, tasks) -> List[Dict]:
        """Rank tasks by composite score (highest first)."""
        scored = []
        for i, task in enumerate(tasks):
            s = self.score(task)
            scored.append({"task": task, "id": getattr(task, "id", i),
                           "title": getattr(task, "title", ""), "score": s})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored

    def top_n(self, tasks, n=5) -> List[Dict]:
        """Return top N tasks by score."""
        return self.rank_tasks(tasks)[:n]


def default_scorer() -> TaskScorer:
    """Create a scorer with default factors."""
    scorer = TaskScorer()

    def priority_score(task):
        scores = {"critical": 100, "high": 75, "medium": 50, "low": 25}
        return scores.get(_get_priority(task), 50)

    def urgency_score(task):
        due = getattr(task, "due_date", None)
        if not due:
            return 50
        try:
            days = (datetime.fromisoformat(due.replace("Z", "+00:00")) - datetime.now(timezone.utc)).days
            if days < 0: return 100
            elif days == 0: return 90
            elif days <= 3: return 70
            elif days <= 7: return 50
            elif days <= 14: return 30
            return 10
        except: return 50

    def age_score(task):
        created = getattr(task, "created_at", None)
        if not created: return 50
        try:
            days = (datetime.now(timezone.utc) - datetime.fromisoformat(created.replace("Z", "+00:00"))).days
            return min(100, days * 3)
        except: return 50

    def effort_score(task):
        sp = getattr(task, "story_points", None) or 3
        if sp <= 2: return 90
        elif sp <= 5: return 60
        elif sp <= 8: return 40
        return 20

    scorer.add_factor("priority", 0.35, priority_score, "Priority-based score")
    scorer.add_factor("urgency", 0.30, urgency_score, "Due date urgency")
    scorer.add_factor("age", 0.15, age_score, "Task age")
    scorer.add_factor("effort", 0.20, effort_score, "Effort (lower = higher score)")
    scorer.normalize_weights()
    return scorer
