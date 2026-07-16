"""Search and filter tasks by text content."""
from .models import Task, Status

def search_by_text(tasks, query):
    query_lower = query.lower()
    return [t for t in tasks if query_lower in t.title.lower() or query_lower in (t.description or "").lower()]

def filter_by_priority_range(tasks, min_priority=None, max_priority=None):
    order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    results = tasks
    if min_priority:
        min_val = order.get(min_priority, 0)
        results = [t for t in results if order.get(t.priority.value, 0) >= min_val]
    if max_priority:
        max_val = order.get(max_priority, 3)
        results = [t for t in results if order.get(t.priority.value, 0) <= max_val]
    return results

def group_by_status(tasks):
    groups = {"todo": [], "in-progress": [], "done": []}
    for t in tasks:
        key = t.status.value
        if key in groups:
            groups[key].append(t)
    return groups

def count_by_priority(tasks):
    counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for t in tasks:
        key = t.priority.value
        if key in counts:
            counts[key] += 1
    return counts
