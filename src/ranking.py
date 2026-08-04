"""Task ranking algorithm with weighted scoring."""
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional


def _get_status(task):
    return task.status.value if hasattr(task.status, "value") else task.status


def _get_priority(task):
    return task.priority.value if hasattr(task.priority, "value") else task.priority


def _parse(iso_string):
    return datetime.fromisoformat(iso_string.replace("Z", "+00:00"))


PRIORITY_SCORES = {"critical": 100, "high": 70, "medium": 40, "low": 10}
STATUS_MULTIPLIERS = {"todo": 1.0, "in-progress": 1.2, "review": 1.5, "blocked": 0.8, "done": 0.0}


def default_weights():
    return {"priority": 0.35, "urgency": 0.25, "dependencies": 0.15,
            "age": 0.10, "effort": 0.10, "tags": 0.05}


def _priority_score(task):
    return PRIORITY_SCORES.get(_get_priority(task), 40)


def _urgency_score(task):
    due = getattr(task, "due_date", None)
    if not due:
        return 20
    try:
        due_dt = _parse(due)
        days_until = (due_dt - datetime.now(timezone.utc)).days
        if days_until < 0:
            return 100
        elif days_until == 0:
            return 90
        elif days_until <= 3:
            return 70
        elif days_until <= 7:
            return 50
        elif days_until <= 14:
            return 30
        else:
            return 10
    except (ValueError, TypeError):
        return 20


def _dependency_score(task):
    dependents = getattr(task, "dependents", None) or []
    return min(100, len(dependents) * 20)


def _age_score(task):
    created = getattr(task, "created_at", None)
    if not created:
        return 20
    try:
        days_old = (datetime.now(timezone.utc) - _parse(created)).days
        return min(100, days_old * 2)
    except (ValueError, TypeError):
        return 20


def _effort_score(task):
    effort = getattr(task, "story_points", None) or getattr(task, "effort_score", None)
    if effort is None:
        return 50
    if effort <= 2:
        return 90
    elif effort <= 5:
        return 60
    elif effort <= 10:
        return 30
    else:
        return 10


def _tag_score(task):
    tags = set(getattr(task, "tags", []) or [])
    score = 50
    if "urgent" in tags:
        score += 30
    if "bug" in tags:
        score += 20
    if "blocked" in tags:
        score -= 20
    if "archived" in tags:
        score = 0
    return max(0, min(100, score))


def task_score(task, weights=None):
    if weights is None:
        weights = default_weights()
    status = _get_status(task)
    status_multiplier = STATUS_MULTIPLIERS.get(status, 1.0)
    if status_multiplier == 0:
        return 0.0
    score = (
        _priority_score(task) * weights.get("priority", 0.35)
        + _urgency_score(task) * weights.get("urgency", 0.25)
        + _dependency_score(task) * weights.get("dependencies", 0.15)
        + _age_score(task) * weights.get("age", 0.10)
        + _effort_score(task) * weights.get("effort", 0.10)
        + _tag_score(task) * weights.get("tags", 0.05)
    )
    return round(score * status_multiplier, 2)


def rank_tasks(tasks, weights=None):
    scored = [{"task": t, "score": task_score(t, weights), "id": getattr(t, "id", i)}
              for i, t in enumerate(tasks)]
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def top_n(tasks, n=5, weights=None):
    return rank_tasks(tasks, weights)[:n]


def ranking_report(tasks, weights=None):
    ranked = rank_tasks(tasks, weights)
    return {
        "total_tasks": len(tasks),
        "ranked": [{"rank": i+1, "id": r["id"], "score": r["score"],
                     "title": getattr(r["task"], "title", str(r["id"]))}
                    for i, r in enumerate(ranked)],
        "top_score": ranked[0]["score"] if ranked else 0,
        "average_score": round(sum(r["score"] for r in ranked) / len(ranked), 2) if ranked else 0,
    }


def score_breakdown(task, weights=None):
    if weights is None:
        weights = default_weights()
    return {
        "priority": _priority_score(task),
        "urgency": _urgency_score(task),
        "dependencies": _dependency_score(task),
        "age": _age_score(task),
        "effort": _effort_score(task),
        "tags": _tag_score(task),
        "total": task_score(task, weights),
    }


def adjust_weights(base_weights, **adjustments):
    weights = dict(base_weights)
    for key, delta in adjustments.items():
        if key in weights:
            weights[key] = max(0, weights[key] + delta)
    total = sum(weights.values())
    if total > 0:
        weights = {k: round(v / total, 4) for k, v in weights.items()}
    return weights
