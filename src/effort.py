"""Effort and complexity scoring for tasks."""

COMPLEXITY_LEVELS = {
    (0, 3): "trivial",
    (4, 7): "simple",
    (8, 15): "moderate",
    (16, 25): "complex",
    (26, 100): "research",
}


def effort_score(task) -> float:
    """Calculate effort score from task attributes."""
    base = 5.0
    priority = getattr(task, "priority", None)
    if priority:
        pval = priority.value if hasattr(priority, "value") else priority
        priority_weight = {"low": 0.8, "medium": 1.0, "high": 1.5, "critical": 2.0}
        base *= priority_weight.get(pval, 1.0)

    tags = getattr(task, "tags", []) or []
    if "refactor" in tags:
        base *= 1.3
    if "research" in tags:
        base *= 1.8
    if "docs" in tags:
        base *= 0.7

    desc = getattr(task, "description", "") or ""
    if len(desc) > 200:
        base *= 1.1

    subtasks = getattr(task, "subtasks", None) or []
    base += len(subtasks) * 2

    return round(base, 1)


def complexity_level(score: float) -> str:
    """Classify an effort score into a complexity level."""
    for (low, high), level in COMPLEXITY_LEVELS.items():
        if low <= score <= high:
            return level
    return "research"


def risk_adjusted_effort(task, risk_factor: float = 1.0) -> float:
    """Apply a risk multiplier to the base effort score."""
    base = effort_score(task)
    return round(base * risk_factor, 1)


def effort_distribution(tasks) -> dict:
    """Return distribution of complexity levels across tasks."""
    dist = {"trivial": 0, "simple": 0, "moderate": 0, "complex": 0, "research": 0}
    for t in tasks:
        score = effort_score(t)
        level = complexity_level(score)
        dist[level] = dist.get(level, 0) + 1
    return dist


def total_effort(tasks) -> float:
    """Sum effort scores across all tasks."""
    return round(sum(effort_score(t) for t in tasks), 1)


def average_effort(tasks) -> float:
    """Calculate mean effort score."""
    if not tasks:
        return 0.0
    return round(total_effort(tasks) / len(tasks), 1)


def highest_effort(tasks):
    """Return the task with the highest effort score, or None."""
    if not tasks:
        return None
    return max(tasks, key=effort_score)


def effort_by_tag(tasks) -> dict:
    """Sum effort grouped by tags."""
    result = {}
    for t in tasks:
        tags = getattr(t, "tags", []) or []
        score = effort_score(t)
        for tag in tags:
            result[tag] = round(result.get(tag, 0) + score, 1)
    return result
