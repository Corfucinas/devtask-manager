"""Task estimation with story points and complexity scoring."""


COMPLEXITY_WEIGHTS = {
    "trivial": 1,
    "simple": 2,
    "moderate": 3,
    "complex": 5,
    "research": 8,
}

FIBONACCI = [1, 2, 3, 5, 8, 13, 21, 34, 55]


def estimate_task(complexity="simple", uncertainty=0, dependency_count=0):
    """Calculate story points from complexity, uncertainty, and dependencies."""
    base = COMPLEXITY_WEIGHTS.get(complexity, 2)
    uncertainty_factor = 1 + (uncertainty / 10.0)
    dependency_factor = 1 + (dependency_count * 0.15)
    raw = base * uncertainty_factor * dependency_factor
    return fibonacci_estimate(raw)


def fibonacci_estimate(points):
    """Snap a raw estimate to the nearest Fibonacci number."""
    if points <= 0:
        return 1
    closest = FIBONACCI[0]
    for fib in FIBONACCI:
        if abs(fib - points) < abs(closest - points):
            closest = fib
    return closest


def confidence_score(estimate, actual):
    """Track estimation accuracy. Returns 0-100 (100 = perfect)."""
    if actual <= 0:
        return 0
    ratio = estimate / actual
    if ratio == 1.0:
        return 100
    if ratio < 1.0:
        return int(ratio * 100)
    return int((1 / ratio) * 100)


def velocity_by_developer(tasks, developer):
    """Sum completed story points for a developer."""
    total = 0
    for t in tasks:
        if hasattr(t, "assignee") and t.assignee == developer:
            status = t.status.value if hasattr(t.status, "value") else t.status
            if status == "done" and hasattr(t, "story_points"):
                total += t.story_points or 0
    return total


def burndown_remaining(tasks, total_points):
    """Calculate remaining points from incomplete tasks."""
    completed = 0
    for t in tasks:
        status = t.status.value if hasattr(t.status, "value") else t.status
        if status == "done" and hasattr(t, "story_points"):
            completed += t.story_points or 0
    return max(0, total_points - completed)
