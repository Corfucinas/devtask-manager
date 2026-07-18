"""Tag management and analytics."""
from collections import Counter
from .models import Task, Status

def get_all_tags(tasks):
    tags = set()
    for t in tasks: tags.update(t.tags)
    return sorted(tags)

def count_tags(tasks):
    counter = Counter()
    for t in tasks:
        for tag in t.tags: counter[tag] += 1
    return dict(counter.most_common())

def filter_by_tag(tasks, tag):
    return [t for t in tasks if tag in t.tags]

def get_tasks_by_tag(tasks):
    groups = {}
    for t in tasks:
        for tag in t.tags:
            if tag not in groups: groups[tag] = []
            groups[tag].append(t)
    return groups

def tag_stats(tasks):
    counts = count_tags(tasks)
    total = len(tasks)
    tagged = sum(1 for t in tasks if t.tags)
    return {"total_tags": len(counts), "tagged_tasks": tagged, "untagged_tasks": total - tagged, "tag_counts": counts, "avg_tags_per_task": round(sum(len(t.tags) for t in tasks) / total, 1) if total > 0 else 0}
