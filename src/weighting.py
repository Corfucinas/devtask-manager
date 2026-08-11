"""Weighted scoring and priority weighting."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


PRIORITY_WEIGHTS = {"critical": 4.0, "high": 3.0, "medium": 2.0, "low": 1.0}
STATUS_WEIGHTS = {"todo": 1.0, "in-progress": 1.2, "review": 1.5, "blocked": 0.8, "done": 0.0}


@dataclass
class WeightProfile:
    """A configurable weight profile for task scoring."""
    name: str
    priority_weight: float = 0.35
    age_weight: float = 0.20
    complexity_weight: float = 0.15
    urgency_weight: float = 0.15
    dependency_weight: float = 0.10
    effort_weight: float = 0.05

    def normalize(self):
        total = (self.priority_weight + self.age_weight + self.complexity_weight +
                 self.urgency_weight + self.dependency_weight + self.effort_weight)
        if total <= 0:
            return self
        return WeightProfile(
            name=self.name,
            priority_weight=round(self.priority_weight / total, 4),
            age_weight=round(self.age_weight / total, 4),
            complexity_weight=round(self.complexity_weight / total, 4),
            urgency_weight=round(self.urgency_weight / total, 4),
            dependency_weight=round(self.dependency_weight / total, 4),
            effort_weight=round(self.effort_weight / total, 4))


def _get_priority(task):
    return task.priority.value if hasattr(task.priority, "value") else task.priority


def _get_status(task):
    return task.status.value if hasattr(task.status, "value") else task.status


def _parse(iso_string):
    return datetime.fromisoformat(iso_string.replace("Z", "+00:00"))


def _priority_score(task):
    return PRIORITY_WEIGHTS.get(_get_priority(task), 2.0) / 4.0 * 100


def _age_score(task):
    created = getattr(task, "created_at", None)
    if not created:
        return 50.0
    try:
        days = (datetime.now(timezone.utc) - _parse(created)).days
        return min(100.0, days * 3.0)
    except (ValueError, TypeError):
        return 50.0


def _complexity_score(task):
    sp = getattr(task, "story_points", None)
    if sp is None:
        return 50.0
    if sp <= 3: return 80.0
    elif sp <= 8: return 60.0
    elif sp <= 13: return 40.0
    return 20.0


def _urgency_score(task):
    due = getattr(task, "due_date", None)
    if not due:
        return 50.0
    try:
        days_until = (_parse(due) - datetime.now(timezone.utc)).days
        if days_until < 0: return 100.0
        elif days_until == 0: return 90.0
        elif days_until <= 3: return 70.0
        elif days_until <= 7: return 50.0
        elif days_until <= 14: return 30.0
        return 10.0
    except (ValueError, TypeError):
        return 50.0


def _dependency_score(task):
    dependents = getattr(task, "dependents", None) or []
    deps = getattr(task, "dependencies", None) or []
    blocked = getattr(task, "blockers", None) or []
    s = len(dependents) * 15 + len(deps) * 5
    if blocked and any(b.status == "active" for b in blocked):
        s += 20
    return min(100.0, float(s))


def _effort_score(task):
    e = getattr(task, "story_points", None) or getattr(task, "effort_score", None)
    if e is None: return 50.0
    if e <= 2: return 90.0
    elif e <= 5: return 60.0
    elif e <= 8: return 40.0
    return 20.0


def score(task, profile=None):
    if profile is None:
        profile = WeightProfile(name="default").normalize()
    status_mult = STATUS_WEIGHTS.get(_get_status(task), 1.0)
    if status_mult == 0:
        return 0.0
    result = (
        _priority_score(task) * profile.priority_weight
        + _age_score(task) * profile.age_weight
        + _complexity_score(task) * profile.complexity_weight
        + _urgency_score(task) * profile.urgency_weight
        + _dependency_score(task) * profile.dependency_weight
        + _effort_score(task) * profile.effort_weight)
    return round(result * status_mult, 2)


def rank(tasks, profile=None):
    scored = []
    for i, task in enumerate(tasks):
        s = score(task, profile)
        scored.append({"task": task, "id": getattr(task, "id", i),
                       "title": getattr(task, "title", ""), "score": s})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def top_n(tasks, n=5, profile=None):
    return rank(tasks, profile)[:n]


def score_breakdown(task, profile=None):
    if profile is None:
        profile = WeightProfile(name="default").normalize()
    return {"priority": round(_priority_score(task), 2),
            "age": round(_age_score(task), 2),
            "complexity": round(_complexity_score(task), 2),
            "urgency": round(_urgency_score(task), 2),
            "dependency": round(_dependency_score(task), 2),
            "effort": round(_effort_score(task), 2),
            "total": score(task, profile)}


def default_profiles():
    return {
        "balanced": WeightProfile(name="balanced").normalize(),
        "urgency_first": WeightProfile(name="urgency_first", priority_weight=0.30,
            age_weight=0.10, complexity_weight=0.10, urgency_weight=0.40,
            dependency_weight=0.05, effort_weight=0.05).normalize(),
        "quick_wins": WeightProfile(name="quick_wins", priority_weight=0.20,
            age_weight=0.10, complexity_weight=0.20, urgency_weight=0.15,
            dependency_weight=0.05, effort_weight=0.30).normalize(),
        "critical_path": WeightProfile(name="critical_path", priority_weight=0.25,
            age_weight=0.10, complexity_weight=0.10, urgency_weight=0.15,
            dependency_weight=0.35, effort_weight=0.05).normalize(),
    }
