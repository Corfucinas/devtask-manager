"""Task ranker v2 with configurable scoring."""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Dict, List, Optional


PRIORITY_WEIGHTS = {"critical": 100, "high": 75, "medium": 50, "low": 25}
STATUS_MULTIPLIERS = {"todo": 1.0, "in-progress": 1.2, "review": 1.5,
                      "blocked": 0.8, "done": 0.0}


def _get_priority(task):
    return task.priority.value if hasattr(task.priority, "value") else task.priority


def _get_status(task):
    return task.status.value if hasattr(task.status, "value") else task.status


def _parse(iso_string):
    return datetime.fromisoformat(iso_string.replace("Z", "+00:00"))


@dataclass
class ScoringConfig:
    """Configuration for scoring."""
    priority_weight: float = 0.35
    urgency_weight: float = 0.25
    age_weight: float = 0.15
    effort_weight: float = 0.15
    dependency_weight: float = 0.10

    @property
    def total_weight(self) -> float:
        return (self.priority_weight + self.urgency_weight + self.age_weight +
                self.effort_weight + self.dependency_weight)


def _priority_score(task):
    return PRIORITY_WEIGHTS.get(_get_priority(task), 50)


def _urgency_score(task):
    due = getattr(task, "due_date", None)
    if not due:
        return 30
    try:
        days = (_parse(due) - datetime.now(timezone.utc)).days
        if days < 0: return 100
        elif days == 0: return 90
        elif days <= 3: return 70
        elif days <= 7: return 50
        elif days <= 14: return 30
        return 10
    except (ValueError, TypeError):
        return 30


def _age_score(task):
    created = getattr(task, "created_at", None)
    if not created:
        return 20
    try:
        days = (datetime.now(timezone.utc) - _parse(created)).days
        return min(100, days * 2)
    except (ValueError, TypeError):
        return 20


def _effort_score(task):
    sp = getattr(task, "story_points", None) or 3
    if sp <= 2: return 90
    elif sp <= 5: return 60
    elif sp <= 8: return 40
    return 20


def _dependency_score(task):
    dependents = getattr(task, "dependents", None) or []
    return min(100, len(dependents) * 15)


FACTOR_FUNCTIONS = {
    "priority": _priority_score,
    "urgency": _urgency_score,
    "age": _age_score,
    "effort": _effort_score,
    "dependency": _dependency_score,
}


class RankerV2:
    """Ranks tasks using configurable scoring."""
    def __init__(self, config=None):
        self._config = config or ScoringConfig()
        self._custom_factors: Dict[str, Callable] = {}

    @property
    def config(self) -> ScoringConfig:
        return self._config

    def set_config(self, config: ScoringConfig):
        self._config = config
        return self

    def add_custom_factor(self, name: str, func: Callable, weight: float = 0.1):
        """Add a custom scoring factor."""
        self._custom_factors[name] = (func, weight)
        return self

    def score(self, task) -> float:
        """Calculate composite score for a task."""
        status = _get_status(task)
        multiplier = STATUS_MULTIPLIERS.get(status, 1.0)
        if multiplier == 0:
            return 0.0

        config = self._config
        total = (
            _priority_score(task) * config.priority_weight +
            _urgency_score(task) * config.urgency_weight +
            _age_score(task) * config.age_weight +
            _effort_score(task) * config.effort_weight +
            _dependency_score(task) * config.dependency_weight
        )
        for name, (func, weight) in self._custom_factors.items():
            try:
                total += func(task) * weight
            except Exception:
                pass
        return round(total * multiplier, 2)

    def score_breakdown(self, task) -> Dict:
        """Return individual factor scores."""
        return {
            "priority": round(_priority_score(task), 1),
            "urgency": round(_urgency_score(task), 1),
            "age": round(_age_score(task), 1),
            "effort": round(_effort_score(task), 1),
            "dependency": round(_dependency_score(task), 1),
            "total": self.score(task),
        }

    def rank(self, tasks) -> List[Dict]:
        """Rank tasks by composite score."""
        scored = []
        for i, task in enumerate(tasks):
            s = self.score(task)
            scored.append({"task": task, "id": getattr(task, "id", i),
                          "title": getattr(task, "title", ""),
                          "score": s, "status": _get_status(task)})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored

    def top_n(self, tasks, n=5) -> List[Dict]:
        return self.rank(tasks)[:n]

    def bottom_n(self, tasks, n=5) -> List[Dict]:
        """Return lowest-scored tasks."""
        return self.rank(tasks)[-n:]

    def set_weights(self, **weights):
        """Update scoring weights."""
        for key, value in weights.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
        return self


def rank_tasks(tasks, config=None) -> List[Dict]:
    """Quick ranking helper."""
    ranker = RankerV2(config)
    return ranker.rank(tasks)


def ranking_report(ranker: RankerV2, tasks) -> Dict:
    """Generate a ranking report."""
    ranked = ranker.rank(tasks)
    return {
        "total_tasks": len(tasks),
        "ranked_count": len(ranked),
        "top_3": [{"id": r["id"], "title": r["title"], "score": r["score"]}
                  for r in ranked[:3]],
        "avg_score": round(sum(r["score"] for r in ranked) / max(len(ranked), 1), 2),
        "max_score": max((r["score"] for r in ranked), default=0),
        "min_score": min((r["score"] for r in ranked), default=0),
        "weights": {
            "priority": ranker.config.priority_weight,
            "urgency": ranker.config.urgency_weight,
            "age": ranker.config.age_weight,
            "effort": ranker.config.effort_weight,
            "dependency": ranker.config.dependency_weight,
        },
    }


def default_ranker() -> RankerV2:
    """Create a ranker with default config."""
    return RankerV2(ScoringConfig())
