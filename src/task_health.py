"""Task health indicator with scoring."""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional


def _get_status(task):
    return task.status.value if hasattr(task.status, "value") else task.status


def _get_priority(task):
    return task.priority.value if hasattr(task.priority, "value") else task.priority


def _parse(iso_string):
    return datetime.fromisoformat(iso_string.replace("Z", "+00:00"))


@dataclass
class HealthIndicator:
    """Health assessment for a task."""
    task_id: int
    score: float = 0.0
    grade: str = "F"
    factors: Dict[str, float] = field(default_factory=dict)
    assessed_at: str = ""

    def __post_init__(self):
        if not self.assessed_at:
            self.assessed_at = datetime.now(timezone.utc).isoformat()

    @property
    def is_healthy(self): return self.score >= 70
    @property
    def is_critical(self): return self.score < 40
    @property
    def needs_attention(self): return 40 <= self.score < 70


def _age_factor(task):
    created = getattr(task, "created_at", None)
    if not created: return 50.0
    try:
        days = (datetime.now(timezone.utc) - _parse(created)).days
        if days <= 7: return 100
        elif days <= 14: return 90
        elif days <= 30: return 70
        elif days <= 60: return 40
        elif days <= 90: return 20
        else: return 10
    except: return 50.0


def _staleness_factor(task):
    updated = getattr(task, "updated_at", None)
    if not updated: return 50.0
    try:
        days = (datetime.now(timezone.utc) - _parse(updated)).days
        if days <= 1: return 100
        elif days <= 3: return 90
        elif days <= 7: return 75
        elif days <= 14: return 50
        elif days <= 30: return 25
        else: return 10
    except: return 50.0


def _blocking_factor(task):
    blockers = getattr(task, "blockers", None) or []
    if not blockers: return 100.0
    active = sum(1 for b in blockers if getattr(b, "status", "") == "active")
    if active == 0: return 100.0
    elif active == 1: return 50.0
    else: return 20.0


def _assignee_factor(task):
    return 100.0 if getattr(task, "assignee", None) else 30.0


def _priority_factor(task):
    return {"critical": 100, "high": 85, "medium": 70, "low": 50}.get(_get_priority(task), 50)


def _due_date_factor(task):
    due = getattr(task, "due_date", None)
    if not due: return 50
    if _get_status(task) == "done": return 100
    try:
        days = (_parse(due) - datetime.now(timezone.utc)).days
        if days < 0: return 20
        elif days == 0: return 70
        elif days <= 3: return 85
        elif days <= 7: return 95
        else: return 100
    except: return 50


def _tag_factor(task):
    tags = getattr(task, "tags", []) or []
    if not tags: return 40
    if len(tags) <= 3: return 100
    elif len(tags) <= 5: return 80
    else: return 50


WEIGHTS = {"age": 0.20, "staleness": 0.20, "blocking": 0.15, "assignee": 0.10,
           "priority": 0.10, "due_date": 0.10, "tags": 0.15}


def assess_health(task) -> HealthIndicator:
    if _get_status(task) == "done":
        return HealthIndicator(task_id=getattr(task, "id", 0), score=100.0, grade="A",
                                factors={"status": 100})
    factors = {"age": _age_factor(task), "staleness": _staleness_factor(task),
               "blocking": _blocking_factor(task), "assignee": _assignee_factor(task),
               "priority": _priority_factor(task), "due_date": _due_date_factor(task),
               "tags": _tag_factor(task)}
    score = sum(factors[k] * WEIGHTS.get(k, 0.1) for k in factors)
    score = round(max(0, min(100, score)), 1)
    grade = "A" if score >= 90 else "B" if score >= 80 else             "C" if score >= 70 else "D" if score >= 60 else "F"
    return HealthIndicator(task_id=getattr(task, "id", 0), score=score, grade=grade,
                            factors=factors)


def assess_batch(tasks) -> List[HealthIndicator]:
    return [assess_health(t) for t in tasks]


def health_report(tasks) -> Dict:
    assessments = assess_batch(tasks)
    if not assessments:
        return {"total_tasks": 0, "average_score": 0}
    avg = round(sum(a.score for a in assessments) / len(assessments), 1)
    return {"total_tasks": len(assessments), "average_score": avg,
            "healthy": sum(1 for a in assessments if a.is_healthy),
            "needs_attention": sum(1 for a in assessments if a.needs_attention),
            "critical": sum(1 for a in assessments if a.is_critical),
            "grade_distribution": {g: sum(1 for a in assessments if a.grade == g)
                                    for g in ("A", "B", "C", "D", "F")},
            "grade": "A" if avg >= 90 else "B" if avg >= 80 else "C" if avg >= 70 else                     "D" if avg >= 60 else "F"}


def healthiest_tasks(tasks, n=5) -> List[HealthIndicator]:
    assessments = assess_batch(tasks)
    assessments.sort(key=lambda a: -a.score)
    return assessments[:n]


def unhealthy_tasks(tasks, threshold=40) -> List[HealthIndicator]:
    return [a for a in assess_batch(tasks) if a.score <= threshold]
