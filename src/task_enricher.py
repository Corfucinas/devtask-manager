"""Task enricher for adding computed metadata."""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional


def _get_status(task):
    return task.status.value if hasattr(task.status, "value") else task.status


def _get_priority(task):
    return task.priority.value if hasattr(task.priority, "value") else task.priority


def _parse(iso_string):
    return datetime.fromisoformat(iso_string.replace("Z", "+00:00"))


@dataclass
class EnrichmentConfig:
    """Configuration for task enrichment."""
    compute_age: bool = True
    compute_urgency: bool = True
    compute_complexity: bool = True
    compute_blocked: bool = True
    compute_dependency_count: bool = True
    compute_tag_count: bool = True
    compute_completion_estimate: bool = True


def _compute_age(task):
    """Compute age in days."""
    created = getattr(task, "created_at", None)
    if not created:
        return 0
    try:
        return (datetime.now(timezone.utc) - _parse(created)).days
    except (ValueError, TypeError):
        return 0


def _compute_urgency(task):
    """Compute urgency score (0-100)."""
    due = getattr(task, "due_date", None)
    if not due or _get_status(task) == "done":
        return 0
    try:
        days = (_parse(due) - datetime.now(timezone.utc)).days
        if days < 0: return 100
        elif days == 0: return 90
        elif days <= 3: return 70
        elif days <= 7: return 50
        elif days <= 14: return 30
        return 10
    except (ValueError, TypeError):
        return 0


def _compute_complexity(task):
    """Compute complexity score (0-100)."""
    sp = getattr(task, "story_points", None) or getattr(task, "effort_score", None) or 3
    desc = getattr(task, "description", "") or ""
    tags = set(getattr(task, "tags", []) or [])
    score = min(100, sp * 10)
    if len(desc) > 500: score += 10
    if "research" in tags: score += 15
    if "refactor" in tags: score += 10
    return min(100, score)


def _compute_blocked(task):
    """Check if task is blocked."""
    blockers = getattr(task, "blockers", None) or []
    if blockers and any(b.status == "active" for b in blockers):
        return True
    deps = getattr(task, "dependencies", None) or []
    return len(deps) > 5


def _compute_dependency_count(task):
    """Count dependencies."""
    deps = getattr(task, "dependencies", None) or []
    dependents = getattr(task, "dependents", None) or []
    return len(deps) + len(dependents)


def _compute_tag_count(task):
    """Count tags."""
    tags = getattr(task, "tags", []) or []
    return len(tags)


def _compute_completion_estimate(task):
    """Estimate completion time in hours."""
    sp = getattr(task, "story_points", None) or 3
    return sp * 4  # 4 hours per story point


def enrich_task(task, all_tasks=None, config=None):
    """Enrich a task with computed metadata."""
    if config is None:
        config = EnrichmentConfig()
    enriched = {}
    
    if config.compute_age:
        enriched["age_days"] = _compute_age(task)
        task.age_days = enriched["age_days"]
    
    if config.compute_urgency:
        enriched["urgency_score"] = _compute_urgency(task)
        task.urgency_score = enriched["urgency_score"]
    
    if config.compute_complexity:
        enriched["complexity_score"] = _compute_complexity(task)
        task.complexity_score = enriched["complexity_score"]
    
    if config.compute_blocked:
        enriched["is_blocked"] = _compute_blocked(task)
        task.is_blocked = enriched["is_blocked"]
    
    if config.compute_dependency_count:
        enriched["dependency_count"] = _compute_dependency_count(task)
        task.dependency_count = enriched["dependency_count"]
    
    if config.compute_tag_count:
        enriched["tag_count"] = _compute_tag_count(task)
        task.tag_count = enriched["tag_count"]
    
    if config.compute_completion_estimate:
        enriched["estimated_hours"] = _compute_completion_estimate(task)
        task.estimated_hours = enriched["estimated_hours"]
    
    enriched["status"] = _get_status(task)
    enriched["priority"] = _get_priority(task)
    
    return enriched


def enrich_batch(tasks, config=None):
    """Enrich multiple tasks."""
    return [enrich_task(t, tasks, config) for t in tasks]


def enrichment_report(tasks, config=None):
    """Generate an enrichment report."""
    if config is None:
        config = EnrichmentConfig()
    enriched = enrich_batch(tasks, config)
    total = len(enriched)
    return {
        "total_tasks": total,
        "blocked_count": sum(1 for e in enriched if e.get("is_blocked")),
        "avg_urgency": round(sum(e.get("urgency_score", 0) for e in enriched) / max(total, 1), 1),
        "avg_complexity": round(sum(e.get("complexity_score", 0) for e in enriched) / max(total, 1), 1),
        "avg_age_days": round(sum(e.get("age_days", 0) for e in enriched) / max(total, 1), 1),
        "avg_dependency_count": round(sum(e.get("dependency_count", 0) for e in enriched) / max(total, 1), 1),
        "avg_tag_count": round(sum(e.get("tag_count", 0) for e in enriched) / max(total, 1), 1),
        "avg_estimated_hours": round(sum(e.get("estimated_hours", 0) for e in enriched) / max(total, 1), 1),
        "high_urgency_count": sum(1 for e in enriched if e.get("urgency_score", 0) >= 70),
    }


def default_config():
    """Return default enrichment config."""
    return EnrichmentConfig()
